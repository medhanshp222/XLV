from __future__ import annotations

from pathlib import Path
from typing import Dict

BASE_DIR = Path(__file__).resolve().parent.parent
GOVERNMENT_VAULT = BASE_DIR / "data" / "government_vault"
MOCK_WEB_VAULT = BASE_DIR / "data" / "mock_web_vault"


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


def is_heavy_industry_sector(target_sector: str) -> bool:
    sector = target_sector.lower()
    keywords = (
        "steel",
        "iron",
        "metall",
        "heavy",
        "manufact",
        "foundr",
    )
    return any(k in sector for k in keywords)


def select_company_from_local_data(region: str, sector: str) -> Dict[str, str] | None:
    """
    Minimal local company directory implemented in-code because only local
    dataset files are allowed for this stage.
    """
    if region.lower() == "india" and is_heavy_industry_sector(sector):
        return {
            "company_name": "Tata Metallics Limited",
            "report_file": "tata_metallics_sustainability_report.txt",
        }
    return None
