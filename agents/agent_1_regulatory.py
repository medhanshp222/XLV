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
    and parse India's FY 2026-27 Renewable Consumption Obligation (RCO)
    and Energy Storage Obligation (ESO) mandates.
    """
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
        "You are a compliance automation bot focused on India's power-sector compliance mandates. "
        f"Find the official Renewable Consumption Obligation (RCO) and Energy Storage Obligation (ESO) "
        "percentage targets mandated by the Ministry of Power for the current fiscal year FY 2026-27. "
        f"For the {state['target_sector']} sector context, use the official India policy sources and extract the exact numeric percentages clearly, "
        "for example: 'RCO target: 35.95%, ESO target: 2.5%'. "
        "Summarize the exact targets and provide the legal citation source."
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