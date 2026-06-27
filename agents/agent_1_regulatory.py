from __future__ import annotations

from state import AgentState
from services.data_loader import GOVERNMENT_VAULT, is_heavy_industry_sector, read_text


def agent_1_regulatory_tracker(state: AgentState) -> dict:
	"""
	Agent 1: Reads the local government vault and returns the exact regulation
	text relevant to the configured region and sector.
	"""
	print(f"--- [Agent 1] Searching local regulation for {state.get('target_region')} / {state.get('target_sector')} ---")

	region = state.get("target_region", "").strip().lower()
	sector = state.get("target_sector", "").strip()

	raw_laws_text = ""

	# Current local dataset only covers the India + heavy-industry / steel path.
	if region == "india" and is_heavy_industry_sector(sector):
		law_file = GOVERNMENT_VAULT / "india_heavy_industry_mandate.txt"
		if law_file.exists():
			raw_laws_text = read_text(law_file)

	if raw_laws_text:
		next_step = "agent_2_corporate_scraper"
	else:
		next_step = "stop"
		raw_laws_text = (
			f"No local mandate found for region='{state.get('target_region')}' "
			f"and sector='{state.get('target_sector')}'."
		)

	return {
		**state,
		"raw_laws_text": raw_laws_text,
		"next_step": next_step,
	}
