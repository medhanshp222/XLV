import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

STORE_PATH = Path(__file__).resolve().parent.parent / "notifications.json"


def _ensure_store_exists() -> None:
    if not STORE_PATH.exists():
        STORE_PATH.write_text(json.dumps([], indent=2), encoding="utf-8")


def load_notifications() -> List[Dict[str, Any]]:
    _ensure_store_exists()
    return json.loads(STORE_PATH.read_text(encoding="utf-8"))


def save_notifications(entries: List[Dict[str, Any]]) -> None:
    STORE_PATH.write_text(json.dumps(entries, indent=2), encoding="utf-8")


def _normalize_identifier(company: str, region: str, sector: str) -> Dict[str, str]:
    return {
        "company": company.strip().lower(),
        "region": region.strip().lower(),
        "sector": sector.strip().lower(),
    }


def find_notification(company: str, region: str, sector: str) -> Optional[Dict[str, Any]]:
    normalized = _normalize_identifier(company, region, sector)
    for entry in load_notifications():
        candidate = _normalize_identifier(entry.get("company", ""), entry.get("region", ""), entry.get("sector", ""))
        if candidate == normalized:
            return entry
    return None


def record_notification(
    company: str,
    email: str,
    region: str,
    sector: str,
    message: str,
    source: str,
) -> Dict[str, Any]:
    existing = find_notification(company, region, sector)
    if existing:
        return existing

    entry: Dict[str, Any] = {
        "company": company,
        "email": email,
        "region": region,
        "sector": sector,
        "message": message,
        "source": source,
        "notified_at": datetime.utcnow().isoformat() + "Z",
    }
    notifications = load_notifications()
    notifications.append(entry)
    save_notifications(notifications)
    return entry
