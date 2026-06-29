import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from graph import app as compliance_app
from services.email_service import send_email
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


class EmailSendRequest(BaseModel):
    recipient: str
    subject: str
    body: str
    sender: Optional[str] = None


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
        "primary_metric_name": "",
        "numeric_target": "",
        "target_type": "",
        "discovered_company": "",
        "extracted_metric_value": "",
        "metric_unit": "",
        "cso_name": "",
        "designation": "",
        "email": "",
        "discovery_context": "",
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
        "primary_metric_name": final_state.get("primary_metric_name", ""),
        "numeric_target": final_state.get("numeric_target", ""),
        "target_type": final_state.get("target_type", ""),
        "extracted_metric_value": final_state.get("extracted_metric_value", ""),
        "metric_unit": final_state.get("metric_unit", ""),
        "compliance_status": final_state.get("compliance_status", ""),
        "audit_reasoning": final_state.get("audit_reasoning", ""),
    }

    def parse_metric(value: str) -> Optional[float]:
        text = str(value or "").lower().replace(",", "").strip()
        if not text:
            return None
        # Extract the first numeric substring
        import re

        match = re.search(r"[0-9]*\.?[0-9]+", text)
        if not match:
            return None
        try:
            return float(match.group(0))
        except ValueError:
            return None

    compliance_status = str(final_state.get("compliance_status", "") or "").lower()
    company_metric = final_state.get("company_emission_metric", "")
    should_send = False
    risk_keywords = ["non", "fail", "risk", "exceed", "over", "uncertain", "cannot be established"]

    if any(k in compliance_status for k in risk_keywords):
        should_send = True
    else:
        metric = parse_metric(company_metric)
        threshold = 0.0
        try:
            threshold = float(os.getenv("EMAIL_METRIC_THRESHOLD", "0"))
        except ValueError:
            threshold = 0.0

        # Use a conservative default threshold for pulp & paper if no custom threshold is configured
        if threshold == 0.0 and request.sector.lower() == "pulp & paper":
            threshold = 0.15

        if metric is not None and metric > threshold:
            should_send = True

    result["should_send_email"] = should_send

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


@app.post("/api/send-email")
def api_send_email(request: EmailSendRequest) -> Dict[str, Any]:
    try:
        result = send_email(
            to=request.recipient,
            subject=request.subject,
            body=request.body,
            sender=request.sender,
        )
    except Exception as exc:
        msg = str(exc)
        low = msg.lower()
        # If provider indicates verification/domain/testing issues, return 400 with helpful message
        if any(k in low for k in ("verify", "verified", "domain", "testing", "only send")):
            raise HTTPException(status_code=400, detail=msg)
        # Otherwise return a 500 for unexpected errors
        raise HTTPException(status_code=500, detail=msg)

    return {"success": True, "sent": result}
