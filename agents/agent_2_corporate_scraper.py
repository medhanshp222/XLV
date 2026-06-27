import os
import re
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage, ToolMessage
from langchain_tavily import TavilySearch as TavilySearchResults
from langchain_google_genai import ChatGoogleGenerativeAI
from state import AgentState

load_dotenv(override=True)


def _extract_pdf_urls(text: str):
    urls = re.findall(r"https?://[^\s<>'\"]+", text)
    cleaned_urls = []
    for url in urls:
        normalized = url.rstrip(".,;:)")
        if re.search(r"\.pdf(?:$|[?#])", normalized, re.IGNORECASE):
            cleaned_urls.append(normalized)
    return cleaned_urls


class FullCorporateProfile(BaseModel):
    discovered_company: str = Field(description="Name of the company found in the target sector and region.")
    company_emission_metric: str = Field(description="The exact current GHG emission intensity or CO2 metrics found for this company (e.g., '2.3 tCO2e/tcs'). Use 'N/A' if unknown.")
    cso_name: str = Field(description="Full name of the Chief Sustainability Officer or ESG Head. Use 'N/A' if unknown.")
    designation: str = Field(description="Official corporate title/designation.")
    email: str = Field(description="Direct corporate email address or official ESG contact point. Use 'N/A' if missing.")
    discovery_context: str = Field(description="Brief notes on what was discovered about their emissions and leadership.")


def agent_2_corporate_scraper(state: AgentState) -> AgentState:
    from graph import read_sustainability_report

    llm_agent2 = ChatGoogleGenerativeAI(
        model="gemini-3.1-flash-lite",
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0,
    )
    structured_llm_agent2 = llm_agent2.with_structured_output(FullCorporateProfile)
    web_search_tool_agent2 = TavilySearchResults(max_results=3)
    llm_with_tools_agent2 = llm_agent2.bind_tools([web_search_tool_agent2, read_sustainability_report])

    target_sector = state["target_sector"]
    target_region = state["target_region"]

    prompt_text = (
        f"You are a comprehensive corporate researcher. Your goal is to build a profile for a prospect.\n"
        f"1. Find a major prominent company in the '{target_sector}' sector operating in '{target_region}'.\n"
        f"2. Execute a two-step plan to gather the best evidence:\n"
        f"   - Step 1: Use the web search tool to find the direct PDF URL for the target company's latest Business Responsibility and Sustainability Report (BRSR) or ESG report. Use specific search terms like '[Company Name] sustainability report 2025 2026 filetype:pdf' or '[Company Name] brsr report pdf'.\n"
        f"   - Step 2: If you find a direct PDF URL, use the read_sustainability_report tool with that URL and a focused query such as 'What is the company's total Scope 1 and Scope 2 emission intensity or CO2 metric? Return the exact metric and unit.'\n"
        f"3. Search the web to find their Chief Sustainability Officer (CSO) or Head of ESG name and contact email.\n"
        f"4. Loop through as many web searches and PDF reads as needed until you have gathered both the emission metric and the contact information, then compile them into the structured schema."
    )

    messages = [HumanMessage(content=prompt_text)]

    manual_search_queries = [
        f"{target_sector} {target_region} sustainability report pdf",
        f"{target_sector} {target_region} brsr report pdf",
        f"{target_sector} {target_region} ESG report pdf",
    ]

    for query in manual_search_queries:
        try:
            web_results = web_search_tool_agent2.invoke({"query": query})
            messages.append(ToolMessage(content=str(web_results), tool_call_id=f"manual_search:{query}"))
            pdf_urls = _extract_pdf_urls(str(web_results))
            if pdf_urls:
                for pdf_url in pdf_urls[:2]:
                    try:
                        pdf_result = read_sustainability_report.invoke({
                            "pdf_url": pdf_url,
                            "query": "What is the company's total Scope 1 and Scope 2 emission intensity or CO2 metric? Return the exact metric and unit.",
                        })
                        messages.append(ToolMessage(content=f"PDF extraction for {pdf_url}: {pdf_result}", tool_call_id=f"manual_pdf:{pdf_url}"))
                    except Exception as exc:
                        messages.append(ToolMessage(content=f"PDF extraction failed for {pdf_url}: {exc}", tool_call_id=f"manual_pdf_error:{pdf_url}"))
                    break
        except Exception as exc:
            messages.append(ToolMessage(content=f"Manual web search failed for '{query}': {exc}", tool_call_id=f"manual_search_error:{query}"))

    while True:
        response = llm_with_tools_agent2.invoke(messages)
        messages.append(response)

        if not response.tool_calls:
            break

        for tool_call in response.tool_calls:
            try:
                if tool_call.get("name") == "read_sustainability_report":
                    pdf_url = tool_call.get("args", {}).get("pdf_url")
                    query = tool_call.get("args", {}).get("query")
                    if pdf_url:
                        try:
                            tool_output = read_sustainability_report.invoke({"pdf_url": pdf_url, "query": query})
                        except Exception as exc:
                            tool_output = f"PDF tool failed: {exc}"
                    else:
                        tool_output = "No valid PDF URL provided."
                else:
                    tool_output = web_search_tool_agent2.invoke(tool_call["args"])
            except Exception as exc:
                tool_output = f"Tool execution failed: {exc}"

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
