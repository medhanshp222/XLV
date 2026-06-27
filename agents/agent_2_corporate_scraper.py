import os
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage, ToolMessage
from langchain_tavily import TavilySearch as TavilySearchResults
from langchain_google_genai import ChatGoogleGenerativeAI
from state import AgentState

load_dotenv(override=True)


class FullCorporateProfile(BaseModel):
    discovered_company: str = Field(description="Name of the company found in the target sector and region.")
    company_emission_metric: str = Field(description="The exact current GHG emission intensity or CO2 metrics found for this company (e.g., '2.3 tCO2e/tcs'). Use 'N/A' if unknown.")
    cso_name: str = Field(description="Full name of the Chief Sustainability Officer or ESG Head. Use 'N/A' if unknown.")
    designation: str = Field(description="Official corporate title/designation.")
    email: str = Field(description="Direct corporate email address or official ESG contact point. Use 'N/A' if missing.")
    discovery_context: str = Field(description="Brief notes on what was discovered about their emissions and leadership.")


def agent_2_corporate_scraper(state: AgentState) -> AgentState:
    llm_agent2 = ChatGoogleGenerativeAI(
        model="gemini-3.1-flash-lite",
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0,
    )
    structured_llm_agent2 = llm_agent2.with_structured_output(FullCorporateProfile)
    web_search_tool_agent2 = TavilySearchResults(max_results=3)
    llm_with_tools_agent2 = llm_agent2.bind_tools([web_search_tool_agent2])

    target_sector = state["target_sector"]
    target_region = state["target_region"]

    prompt_text = (
        f"You are a comprehensive corporate researcher. Your goal is to build a profile for a prospect.\n"
        f"1. Find a major prominent company in the '{target_sector}' sector operating in '{target_region}'.\n"
        f"2. Search the web to find that specific company's latest reported environmental metrics, specifically their GHG emission intensity or CO2 per tonne of production.\n"
        f"3. Search the web to find their Chief Sustainability Officer (CSO) or Head of ESG name and contact email.\n"
        f"4. Loop through as many web searches as needed until you have gathered both pieces of information, then compile them into the structured schema."
    )

    messages = [HumanMessage(content=prompt_text)]

    while True:
        response = llm_with_tools_agent2.invoke(messages)
        messages.append(response)

        if not response.tool_calls:
            break

        for tool_call in response.tool_calls:
            tool_output = web_search_tool_agent2.invoke(tool_call["args"])
            messages.append(ToolMessage(content=str(tool_output), tool_call_id=tool_call["id"]))

    final_corporate_profile = structured_llm_agent2.invoke(messages)

    return {
        **state,
        "discovered_company": final_corporate_profile.discovered_company,
        "company_emission_metric": final_corporate_profile.company_emission_metric,
        "cso_name": final_corporate_profile.cso_name,
        "designation": final_corporate_profile.designation,
        "email": final_corporate_profile.email,
        "discovery_context": final_corporate_profile.discovery_context,
        "next_step": "agent_3_gap_analyst",
    }
