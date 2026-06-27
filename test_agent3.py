from nodes import gap_analysis_node
from state import AgentState

# Create a mock state matching your schema
mock_state: AgentState = {
    "company_name": "Tata Metallics Limited",
    "target_region": "India",
    "raw_laws_text": "Sample Law Text...", 
    "raw_corporate_report": "Sample ESG Report...",
    "compliance_gap_analysis": None,
    "cso_contact_info": {
        "name": "Rajesh Sharma",
        "email": "rajesh.sharma@tatametallics.co.in",
        "phone": "+91-22-6665-8282"
    },
    "next_step": "agent_3"
}

# Run the node
print("Executing standalone test for Agent 3...\n")
result = gap_analysis_node(mock_state)

# Display the output
print(result["compliance_gap_analysis"])
print(f"\nNext routing step: {result['next_step']}")