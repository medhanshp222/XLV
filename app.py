import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from graph import app as compliance_app
from services.notification_store import find_notification, load_notifications, record_notification

app = FastAPI(title="XLV Compliance API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class RunRequest(BaseModel):
    region: str
    sector: str


class ApproveRequest(BaseModel):
    region: str
    sector: str
    company: str
    email: str
    message: str
    source: Optional[str] = None


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/api/notifications")
def api_notifications() -> Any:
    return load_notifications()


@app.post("/api/run")
def api_run(request: RunRequest) -> Dict[str, Any]:
    initial_state = {
        "target_region": request.region,
        "target_sector": request.sector,
        "raw_laws_text": "",
        "numeric_target": "",
        "target_type": "",
        "discovered_company": "",
        "reporting_year": "",
        "metric_results": [],
        "cso_name": "",
        "designation": "",
        "email": "",
        "discovery_context": "",
        "outreach_email": "",
        "compliance_status": "",
        "audit_reasoning": "",
        "final_outreach_draft": "",
        "next_step": "",
    }

    try:
        final_state = compliance_app.invoke(initial_state)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    company = str(final_state.get("discovered_company", "")).strip()
    already_notified = False
    notification = None
    if company:
        notification = find_notification(company, request.region, request.sector)
        already_notified = notification is not None

    result = {
        "result": final_state,
        "company": company,
        "already_notified": already_notified,
        "notification": notification,
        "metrics": final_state.get("metric_results", []),
        "compliance_status": final_state.get("compliance_status", ""),
        "audit_reasoning": final_state.get("audit_reasoning", ""),
    }
    return result


@app.post("/api/approve")
def api_approve(request: ApproveRequest) -> Dict[str, Any]:
    if not request.company:
        raise HTTPException(status_code=400, detail="Company name is required")

    notification = record_notification(
        company=request.company,
        email=request.email,
        region=request.region,
        sector=request.sector,
        message=request.message,
        source=request.source or "manual_approval",
    )
    return {"status": "recorded", "notification": notification}


app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
