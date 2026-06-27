from __future__ import annotations

from state import AgentState
from services.data_loader import MOCK_WEB_VAULT, read_text, select_company_from_local_data
from services.extractors import extract_contact_info


def agent_2_corporate_scraper_persona_finder(state: AgentState) -> AgentState:
    """
    Step 2:
    Uses raw_laws_text + (target_region, target_sector) to find company report,
    scrape raw report text, and extract CSO contact details from local files.
    """
    if not state.get("raw_laws_text"):
        return {
            **state,
            "raw_corporate_report": "",
            "cso_contact_info": {},
            "next_step": "stop",
        }

    selected = select_company_from_local_data(
        state["target_region"],
        state["target_sector"],
    )

    if not selected:
        return {
            **state,
            "raw_corporate_report": (
                f"No local company report mapped for region='{state['target_region']}' "
                f"and sector='{state['target_sector']}'."
            ),
            "cso_contact_info": {},
            "next_step": "stop",
        }

    report_path = MOCK_WEB_VAULT / selected["report_file"]
    if not report_path.exists():
        return {
            **state,
            "raw_corporate_report": f"Report file not found: {report_path.name}",
            "cso_contact_info": {},
            "next_step": "stop",
        }

    report_text = read_text(report_path)
    contact_info = extract_contact_info(report_text)

    return {
        **state,
        "company_name": selected["company_name"],
        "raw_corporate_report": report_text,
        "cso_contact_info": contact_info,
        "next_step": "agent_3_gap_analyst",
    }
