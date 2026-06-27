from __future__ import annotations

from agents.agent_1_regulatory import agent_1_regulatory_tracker
from agents.agent_2_corporate import agent_2_corporate_scraper_persona_finder
from state import AgentState


def run_agent_1_and_2(initial_state: AgentState) -> AgentState:
    state_after_agent_1 = agent_1_regulatory_tracker(initial_state)
    state_after_agent_2 = agent_2_corporate_scraper_persona_finder(state_after_agent_1)
    return state_after_agent_2
