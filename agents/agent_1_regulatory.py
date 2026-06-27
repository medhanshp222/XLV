from __future__ import annotations

from state import AgentState
from services.data_loader import GOVERNMENT_VAULT, is_heavy_industry_sector, read_text


def agent_1_regulatory_tracker(state: AgentState) -> AgentState:
    """
    Step 1:
    Uses target_region + target_sector to pull only relevant regulation text
    from local government vault files.
    """
    region = state["target_region"].strip().lower()
    sector = state["target_sector"].strip()

    raw_laws_text = ""

    # Current demo dataset supports India + heavy industry/steel classes.
    if region == "india" and is_heavy_industry_sector(sector):
        law_file = GOVERNMENT_VAULT / "india_heavy_industry_mandate.txt"
        if law_file.exists():
            raw_laws_text = read_text(law_file)

    next_step = "agent_2_corporate_scraper"
    if not raw_laws_text:
        next_step = "stop"
        raw_laws_text = (
            f"No local mandate found for region='{state['target_region']}' "
            f"and sector='{state['target_sector']}'."
        )

    return {
        **state,
        "raw_laws_text": raw_laws_text,
        "next_step": next_step,
    }
