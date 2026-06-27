# state.py
from typing import TypedDict, Optional, Dict

class AgentState(TypedDict):
    # Core Global Inputs
    company_name: str
    target_region: str
    
    # Squad 1 (Ingestion Output)
    raw_laws_text: Optional[str]
    raw_corporate_report: Optional[str]
    
    # Squad 2 (Reasoning & Synthesis Output)
    compliance_gap_analysis: Optional[str]
    cso_contact_info: Optional[Dict]
    final_outreach_draft: Optional[str]
    
    # Router State (Tells the Planner who goes next)
    next_step: str