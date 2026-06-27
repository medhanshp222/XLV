from typing import TypedDict


class AgentState(TypedDict, total=False):
    # Inputs
    target_region: str
    target_sector: str

    # Agent 1 Outputs (Regulatory)
    raw_laws_text: str
    primary_metric_name: str
    numeric_target: str
    target_type: str

    # Agent 2 Outputs (Corporate & Prospecting)
    discovered_company: str
    extracted_metric_value: str
    metric_unit: str
    cso_name: str
    designation: str
    email: str
    discovery_context: str

    # Agent 3 Outputs (Audit)
    compliance_status: str
    audit_reasoning: str

    # Agent 4 Outputs (Outreach)
    final_outreach_draft: str

    # LangGraph Routing
    next_step: str