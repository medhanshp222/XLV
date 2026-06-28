from typing import TypedDict


class AgentState(TypedDict, total=False):
    # Inputs
    target_region: str
    target_sector: str

    # Agent 1 Outputs (Regulatory)
    raw_laws_text: str

    # Agent 2 Outputs (Corporate & Prospecting)
    discovered_company: str
    company_emission_metric: str
    cso_name: str
    designation: str
    email: str
    discovery_context: str

    # Agent 3 Outputs (Audit)
    compliance_status: str
    audit_reasoning: str

    # Agent 4 Outputs (Outreach)
    final_outreach_draft: str
    outreach_email_subject: str
    outreach_email_body: str

    # LangGraph Routing
    next_step: str