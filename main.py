import argparse

from graph import app
from state import AgentState


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the compliance automation pipeline")
    parser.add_argument("--region", default="India", help="Target region for the compliance analysis")
    parser.add_argument("--sector", default="Steel Manufacturing", help="Target sector for the compliance analysis")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    initial_state: AgentState = {
        "target_region": args.region,
        "target_sector": args.sector,
        "raw_laws_text": "",
        "discovered_company": "",
        "company_emission_metric": "",
        "cso_name": "",
        "designation": "",
        "email": "",
        "discovery_context": "",
        "compliance_status": "",
        "audit_reasoning": "",
        "final_outreach_draft": "",
        "next_step": "",
    }

    final_state = app.invoke(initial_state)

    print("=== Pipeline complete ===")
    print(f"Region: {final_state.get('target_region')}")
    print(f"Sector: {final_state.get('target_sector')}")
    print(f"Regulation / Rule from Agent 1:")
    print(final_state.get("raw_laws_text", ""))
    print("\nCompany: {0}".format(final_state.get("discovered_company", "")))
    print("Emission Metric: {0}".format(final_state.get("company_emission_metric", "")))
    print("Contact Info:")
    print("- Name: {0}".format(final_state.get("cso_name", "")))
    print("- Title: {0}".format(final_state.get("designation", "")))
    print("- Email: {0}".format(final_state.get("email", "")))
    print("- Context: {0}".format(final_state.get("discovery_context", "")))
    print(f"Compliance Status: {final_state.get('compliance_status')}")
    print(f"Reasoning: {final_state.get('audit_reasoning')}")
    print(f"Next step: {final_state.get('next_step')}")
    print("\nOutreach draft:\n")
    print(final_state.get("final_outreach_draft", ""))


if __name__ == "__main__":
    main()
