from langgraph.graph import StateGraph, START, END
from state import AgentState
from nodes import (
    agent_1_regulatory_tracker,
    agent_2_corporate_scraper_persona_finder,
    gap_analysis_node,  # Assuming this is what you named your agent 3
    outreach_node,      # Assuming this is what you named your agent 4
    router
)

# 1. Initialize the Graph
workflow = StateGraph(AgentState)

# 2. Add the Nodes
workflow.add_node("agent_1", agent_1_regulatory_tracker)
workflow.add_node("agent_2", agent_2_corporate_scraper_persona_finder)
workflow.add_node("agent_3", gap_analysis_node)
workflow.add_node("agent_4", outreach_node)

# 3. Define the Edges
workflow.add_edge(START, "agent_1")

# Use the router to determine the flow
# The router reads 'next_step' from the returned state dictionary
workflow.add_conditional_edges(
    "agent_1", 
    router, 
    {"agent_2_corporate_scraper": "agent_2", "stop": END}
)

workflow.add_conditional_edges(
    "agent_2", 
    router, 
    {"agent_3_gap_analyst": "agent_3", "stop": END}
)

workflow.add_edge("agent_3", "agent_4")
workflow.add_edge("agent_4", END)

# 4. Compile
compliance_pipeline = workflow.compile()