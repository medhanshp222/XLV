from orchestrator.pipeline import run_agent_1_and_2
from state import AgentState


def main() -> None:
    initial_state: AgentState = {
        "target_region": "India",
        "target_sector": "Steel Manufacturing",
        "company_name": "",
        "raw_laws_text": None,
        "raw_corporate_report": None,
        "compliance_gap_analysis": None,
        "cso_contact_info": None,
        "next_step": "agent_1_regulatory_tracker",
    }

    state_after_agent_2 = run_agent_1_and_2(initial_state)

    print("=== Pipeline state after Agent 2 ===")
    print(f"Region: {state_after_agent_2['target_region']}")
    print(f"Sector: {state_after_agent_2['target_sector']}")
    print(f"Company: {state_after_agent_2['company_name']}")
    print(f"Next step: {state_after_agent_2['next_step']}")
    print("CSO Contact:", state_after_agent_2["cso_contact_info"])


if __name__ == "__main__":
    main()
