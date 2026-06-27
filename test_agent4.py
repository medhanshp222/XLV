# test_agent4.py
from nodes import outreach_node
from state import AgentState

# We simulate the state exactly as Agent 2 and Agent 3 would have left it
mock_state: AgentState = {
    "company_name": "Tata Metallics Limited",
    "target_region": "India",
    "raw_laws_text": "...", 
    "raw_corporate_report": "...",
    "compliance_gap_analysis": """--- COMPLIANCE AUDIT REPORT ---
    - Entity: Tata Metallics Limited
    - Legal Threshold: 50,000 MTCO2e
    - Reported Emissions: 54,200 MTCO2e
    - Breach Volume: 4,200 MTCO2e
    - Breach Severity: 8.40% above mandate
    - Estimated Financial Exposure: INR 160.00 Crores""",
    "cso_contact_info": {
        "name": "Rajesh Sharma",
        "email": "rajesh.sharma@tatametallics.co.in",
        "phone": "+91-22-6665-8282"
    },
    "final_outreach_draft": None,
    "next_step": "agent_4"
}

print("Executing standalone test for Agent 4...\n")
result = outreach_node(mock_state)

print(result["final_outreach_draft"])
print(f"\nNext routing step: {result['next_step']}")