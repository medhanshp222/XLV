import os
from dotenv import load_dotenv
from langchain_tavily import TavilySearch as TavilySearchResults
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, ToolMessage
from state import AgentState

# Load environment variables
load_dotenv()


def _extract_text_content(content: object) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict):
                text_value = block.get("text")
                if isinstance(text_value, str):
                    parts.append(text_value)
            else:
                parts.append(str(block))
        return "\n".join(part for part in parts if part)
    return str(content or "")


def agent_1_regulatory_tracker(state: AgentState) -> AgentState:
    """
    Agent 1: Uses a native web search tool bound to Gemini to discover
    and parse the regulatory target for the user-requested sustainability metric.
    """
    metric_results = state.get("metric_results", []) or []
    metric_names = [
        metric.get("metric_name")
        for metric in metric_results
        if isinstance(metric, dict) and metric.get("metric_name")
    ]
    target_metrics = ", ".join(metric_names) if metric_names else (
        "Scope 1 & 2 GHG Emissions (tCO2e), Energy Intensity (GJ/tcs), "
        "Water Intensity (m3/tcs), Hazardous Waste Generation (MT)"
    )

    llm = ChatGoogleGenerativeAI(
        model="gemini-3.1-flash-lite",
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0,
    )

    web_search_tool = TavilySearchResults(
        tavily_api_key=os.getenv("TAVILY_API_KEY"),
        max_results=3,
    )

    llm_with_tools = llm.bind_tools([web_search_tool])

    prompt = (
        "You are a targeted regulatory researcher for sustainability compliance. "
        f"You must find current, legally binding regulatory targets or mandates for these metrics: {target_metrics} "
        f"in the {state['target_sector']} sector for {state['target_region']}. "
        "Use official government, statutory, or authoritative regulatory sources, and extract the exact numeric target or mandate if available. "
        "If the regulation is expressed as a percentage, intensity, or other unit, preserve the unit explicitly. "
        "Use exact formal terminology used in statutory ESG reporting frameworks (like BRSR), not generic terms. "
        "Summarize each metric's target/mandate, legal basis, and citation source."
    )

    messages = [HumanMessage(content=prompt)]
    response = None

    while True:
        response = llm_with_tools.invoke(messages)
        messages.append(response)

        if not getattr(response, "tool_calls", None):
            break

        for tool_call in response.tool_calls:
            tool_output = web_search_tool.invoke(tool_call["args"])
            messages.append(ToolMessage(content=str(tool_output), tool_call_id=tool_call["id"]))

    final_text = _extract_text_content(response.content if response is not None else "")

    return {
        **state,
        "raw_laws_text": final_text,
        "next_step": "agent_2_corporate_scraper",
    }