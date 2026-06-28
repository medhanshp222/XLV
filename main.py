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
    core_metrics = [
        "Scope 1 & 2 GHG Emissions (tCO2e)",
        "Energy Intensity (GJ/tcs)",
        "Water Intensity (m3/tcs)",
        "Hazardous Waste Generation (MT)",
    ]

    # Initializing the state dictionary
    initial_state: AgentState = {
        "target_region": args.region,
        "target_sector": args.sector,
        "raw_laws_text": "",
        "numeric_target": "",
        "target_type": "",
        "discovered_company": "",
        "reporting_year": "",
        "metric_results": [{"metric_name": m} for m in core_metrics],
        "cso_name": "",
        "designation": "",
        "email": "",
        "discovery_context": "",
        "compliance_status": "",
        "audit_reasoning": "",
        "outreach_email": "",
        "final_outreach_draft": "",
        "next_step": "",
    }

    final_state = app.invoke(initial_state)

    # Cleaned up the print block to use f-strings and correct state keys
    print("\n" + "="*50)
    print("=== Pipeline Complete ===")
    print("="*50)
    print(f"Region: {final_state.get('target_region')}")
    print(f"Sector: {final_state.get('target_sector')}")
    
    print(f"\n--- Regulation / Rule (Agent 1) ---")
    print(final_state.get("raw_laws_text", ""))
    
    print(f"\n--- Corporate Profile (Agent 2) ---")
    print(f"Company: {final_state.get('discovered_company', '')}")
    print(f"Reported Year: {final_state.get('reporting_year', '')}")

    metric_results = final_state.get("metric_results", []) or []
    print("Extracted Metrics:")
    for metric in metric_results:
        if not isinstance(metric, dict):
            continue
        metric_name = metric.get("metric_name", "N/A")
        metric_value = metric.get("extracted_metric_value", "N/A")
        metric_unit = metric.get("metric_unit", "N/A")
        metric_quote = metric.get("evidence_quote", "N/A")
        metric_page = metric.get("source_page", "N/A")
        print(f"- {metric_name}: {metric_value} {metric_unit}")
        print(f"  📍 Source Page: {metric_page}")
        print(f"  🔎 Evidence Quote: {metric_quote}")
    
    print(f"\nContact Info:")
    print(f"- Name: {final_state.get('cso_name', '')}")
    print(f"- Title: {final_state.get('designation', '')}")
    print(f"- Email: {final_state.get('email', '')}")
    print(f"- Context: {final_state.get('discovery_context', '')}")
    
    print(f"\n--- Audit Results (Agent 3) ---")
    print(f"Compliance Status: {final_state.get('compliance_status')}")
    print(f"Reasoning: {final_state.get('audit_reasoning')}")
    
    print(f"\n--- Outreach Draft (Agent 4) ---")
    print(final_state.get("final_outreach_draft", ""))
    print("="*50 + "\n")


if __name__ == "__main__":
    main()