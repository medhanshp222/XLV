from langgraph.graph import StateGraph, START, END
from state import AgentState
from nodes import (
    ingestion_node, 
    extraction_node, 
    gap_analysis_node, 
    outreach_node, 
    router
)

# 1. Initialize the Graph with your strict schema
workflow = StateGraph(AgentState)

# 2. Add the Nodes (Your Agents)
workflow.add_node("agent_1", ingestion_node)
workflow.add_node("agent_2", extraction_node)
workflow.add_node("agent_3", gap_analysis_node)
workflow.add_node("agent_4", outreach_node)

# 3. Define the Edges (The Flow)
# Always start at the ingestion node
workflow.add_edge(START, "agent_1")

# Use your router function to dynamically move between nodes based on 'next_step'
workflow.add_conditional_edges("agent_1", router, {"agent_2": "agent_2", "end": END})
workflow.add_conditional_edges("agent_2", router, {"agent_3": "agent_3", "end": END})
workflow.add_conditional_edges("agent_3", router, {"agent_4": "agent_4", "end": END})
workflow.add_conditional_edges("agent_4", router, {"end": END})

# 4. Compile the Pipeline
# This makes it an executable app we can run
compliance_pipeline = workflow.compile()

# ==========================================
# 🧪 END-TO-END EXECUTION TEST
# ==========================================
if __name__ == "__main__":
    print("\n🚀 INITIATING END-TO-END PIPELINE...\n")
    
    # We only need to provide the initial starting trigger
    initial_state = {
        "company_name": "Tata Metallics Limited",
        "target_region": "India"
    }
    
    # Stream the output as the graph traverses the nodes
    for event in compliance_pipeline.stream(initial_state):
        for node_name, state_update in event.items():
            pass # The print statements inside your nodes will show the progress
            
    print("\n✅ PIPELINE EXECUTION COMPLETE.")