

# 1. Import their agents
from agents.agent_1_regulatory import agent_1_regulatory_tracker
from agents.agent_2_corporate import agent_2_corporate_scraper_persona_finder

# 2. Import your agents (Make sure the function names match what you called them)
from agents.agent_3_gap_analysis import gap_analysis_node
from agents.agent_4_outreach import outreach_node

# 3. Keep the router here, as it dictates traffic between all agents
from state import AgentState

def router(state: AgentState) -> str:
    """
    Reads the 'next_step' variable from the state and tells LangGraph where to go.
    """
    return state.get("next_step", "end")

# 4. Export everything so graph.py can easily grab them
__all__ = [
    "agent_1_regulatory_tracker",
    "agent_2_corporate_scraper_persona_finder",
    "gap_analysis_node",
    "outreach_node",
    "router"
]