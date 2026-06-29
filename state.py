from typing import Any, Dict, List, TypedDict


class AgentState(TypedDict, total=False):
    # Inputs
    target_region: str
    target_sector: str

    # Agent 1 Outputs (Regulatory)
    raw_laws_text: str
    numeric_target: str
    target_type: str

    # Agent 2 Outputs (Corporate & Prospecting)
    discovered_company: str
    reporting_year: str
    metric_results: List[Dict[str, Any]]
    cso_name: str
    designation: str
    email: str
    discovery_context: str

    # Agent 3 Outputs (Audit)
    compliance_status: str
    audit_reasoning: str

    # Agent 4 Outputs (Outreach)
    outreach_email: str
    final_outreach_draft: str
    outreach_email_subject: str
    outreach_email_body: str

    # LangGraph Routing
    next_step: str