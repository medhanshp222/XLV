from langchain_core.tools import tool
from langgraph.graph import StateGraph, START, END
from state import AgentState
from agents.agent_1_regulatory import agent_1_regulatory_tracker
from agents.agent_2_corporate_scraper import agent_2_corporate_scraper
from agents.agent_3_gap_analyst import agent_3_gap_analyst
from agents.agent_4_outreach_drafter import agent_4_outreach_drafter
from agents.pdf_reader import extract_metric_from_pdf


@tool
def read_sustainability_report(pdf_url: str, query: str) -> str:
    """Use this tool when you have found an online PDF URL and need to extract an emission metric from it."""
    return extract_metric_from_pdf(pdf_url, query)

workflow = StateGraph(AgentState)

workflow.add_node("agent_1", agent_1_regulatory_tracker)
workflow.add_node("agent_2", agent_2_corporate_scraper)
workflow.add_node("agent_3", agent_3_gap_analyst)
workflow.add_node("agent_4", agent_4_outreach_drafter)

workflow.add_edge(START, "agent_1")
workflow.add_edge("agent_1", "agent_2")
workflow.add_edge("agent_2", "agent_3")
workflow.add_edge("agent_3", "agent_4")
workflow.add_edge("agent_4", END)

app = workflow.compile()
compliance_pipeline = app