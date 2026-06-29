import os
import re
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage, ToolMessage
from langchain_tavily import TavilySearch as TavilySearchResults
from langchain_google_genai import ChatGoogleGenerativeAI
from state import AgentState
from datetime import datetime

load_dotenv(override=True)

def get_latest_reporting_year():
    # If today is June 2026, the latest full FY report is 2025-26
    current_year = datetime.now().year
    return f"{current_year-1}-{str(current_year)[-2:]}"

def _extract_pdf_urls(text: str):
    urls = re.findall(r"https?://[^\s<>'\"]+", text)
    cleaned_urls = []
    for url in urls:
        normalized = url.rstrip(".,;:)")
        if re.search(r"\.pdf(?:$|[?#])", normalized, re.IGNORECASE):
            cleaned_urls.append(normalized)
    return cleaned_urls


def _is_missing_metric_value(value: str | None) -> bool:
    normalized_value = str(value or "").strip().lower()
    return normalized_value in {"", "n/a", "none", "metric not found"}


def _extract_page_numbers(source_page: str | None) -> list[int]:
    if not source_page:
        return []
    return sorted({int(match) for match in re.findall(r"\d+", str(source_page))})

class MetricExtraction(BaseModel):
    metric_name: str = Field(description="Name of the ESG metric being extracted.")
    extracted_metric_value: str = Field(description="Extracted numeric value for this metric, or 'N/A' if not found.")
    metric_unit: str = Field(description="Unit for the extracted value, or 'N/A' if unknown.")
    evidence_quote: str = Field(description="Exact sentence/row proving this metric value, or 'N/A' if unavailable.")
    source_page: str = Field(
        description="CRITICAL: You MUST extract this number directly from the exact string '[Source Pages: ...]' provided anywhere in the tool output. Do NOT write the page number printed in the document text."
    )


class FullCorporateProfile(BaseModel):
    discovered_company: str = Field(
        description="Name of the company found in the target sector and region."
    )
    reporting_year: str = Field(
        description="The financial year of the report you downloaded (e.g., 'FY 2023-24' or 'FY 2024-25'). Infer this from the search query or PDF name if needed."
    )
    cso_name: str = Field(
        description="Full name of the Chief Sustainability Officer or ESG Head. Use 'N/A' if unknown."
    )
    designation: str = Field(
        description="Official corporate title/designation. Use 'N/A' if unknown."
    )
    email: str = Field(
        description="Direct corporate email address or official ESG contact point. Use 'N/A' if missing."
    )
    discovery_context: str = Field(
        description="Brief notes on what was discovered about their metric extraction and leadership."
    )
    extracted_metrics: list[MetricExtraction] = Field(
        description="List of extracted ESG metrics with value, unit, evidence quote, and source page."
    )

def agent_2_corporate_scraper(state: AgentState) -> AgentState:
    from graph import read_sustainability_report, read_sustainability_report_by_page

    # Ensure this matches the model you have quota for
    llm_agent2 = ChatGoogleGenerativeAI(
        model="gemini-3.1-flash-lite", 
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0,
    )
    
    # Define variables inside function scope
    reporting_cycle = get_latest_reporting_year()
    
    structured_llm_agent2 = llm_agent2.with_structured_output(FullCorporateProfile)
    web_search_tool_agent2 = TavilySearchResults(max_results=3)
    llm_with_tools_agent2 = llm_agent2.bind_tools([web_search_tool_agent2, read_sustainability_report])

    target_sector = state["target_sector"]
    target_region = state["target_region"]
    
    dynamic_audit_query = (
        "You are an ESG auditor. Extract the current-year values for ALL of these metrics from the same report: "
        "'Scope 1 & 2 GHG Emissions', 'Energy Intensity', 'Water Intensity', and 'Hazardous Waste Generation'.\n"
        "For EACH metric, return: Value, Unit, Proof (exact sentence or table row), and Page Number.\n"
        "CRITICAL PAGE RULE: To ensure consistency, your Page Number output MUST exactly match the index provided in the [Source Pages: ...] array from the tool output. If the text says 'Page 222' but the tool output says '[Source Pages: [156]]', you MUST output 156. Completely ignore printed page numbers.\n"
        "If a metric is not found, return Value='N/A', Unit='N/A', Proof='N/A', Page='N/A' for that metric.\n"
        "Do not invent data; use only evidence present in the report/tool output."
    )

    prompt_text = (
        f"You are a strict, methodical corporate researcher. Your goal is to build a compliance profile for a prospect following these EXACT phases:\n\n"
        f"PHASE 1: IDENTIFY THE TARGET COMPANY\n"
        f"- Execute a web search to identify a major prominent company in the '{target_sector}' sector operating in '{target_region}'.\n\n"
        f"PHASE 2: TARGETED PDF SEARCH\n"
        f"- Use query: '[Company Name] BRSR report {reporting_cycle} pdf' or '[Company Name] sustainability report {reporting_cycle} filetype:pdf'.\n"
        f"- If the report for {reporting_cycle} is not yet published or cannot be found, you MUST fall back and search for the previous year (e.g., 2024-25, and then 2023-24) until you locate the most recent *available* official PDF.\n"
        f"- Prioritize official company domains (e.g., .in or .com). Avoid generic stock exchange index links (e.g., nseindia.com).\n\n"
        f"PHASE 3: METRIC EXTRACTION\n"
        f"- Call `read_sustainability_report` with your PDF URL and this query: '{dynamic_audit_query}'.\n"
        f"- CRITICAL SCHEMA MAPPING: When the PDF tool returns the data, you MUST extract the 'Proof' string and map it directly to the `evidence_quote` field. You MUST extract the '[Source Pages: X]' string and map it directly to the `source_page` field. Do NOT leave these as N/A if the tool provided them.\n"
        f"- If it fails, try a different link from the official domain.\n\n"
        f"PHASE 4: LEADERSHIP HUNT\n"
        f"- Search for the CSO/Head of ESG contact details."
    )

    messages = [HumanMessage(content=prompt_text)]

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
                    tool_output = read_sustainability_report.invoke({"pdf_url": pdf_url, "query": query})
                    
                else:
                    tool_output = web_search_tool_agent2.invoke(tool_call["args"])
            except Exception as exc:
                tool_output = f"Tool execution failed: {exc}"
            
            messages.append(ToolMessage(content=str(tool_output), tool_call_id=tool_call["id"]))
    

    wake_up_prompt = (
        "All tools have finished executing. Map the tool output into the extracted_metrics list in the schema. "
        "For each of the four required metrics, populate metric_name, extracted_metric_value, metric_unit, evidence_quote, and source_page. "
        "If the tool output contains proof and source pages, those must be copied into evidence_quote and source_page respectively. "
        "CRITICAL PAGE RULE: The `source_page` value MUST come from the index numbers in the `[Source Pages: ...]` string anywhere in the PDF tool output. Ignore any printed page numbers that appear inside the report text itself."
    )
    messages.append(HumanMessage(content=wake_up_prompt))

    # The final structured call
    final_corporate_profile = structured_llm_agent2.invoke(messages)

    draft_metric_results = [metric.model_dump() for metric in final_corporate_profile.extracted_metrics]
    missing_metrics = [
        metric for metric in draft_metric_results if _is_missing_metric_value(metric.get("extracted_metric_value"))
    ]
    successful_pages = []
    # 🔴 IMPROVED REGEX: Handles newlines and varied whitespace
    # This looks for "Source Pages:" followed by brackets containing numbers
    pattern = r"Source Pages:\s*\[([\d,\s]+)\]"
    
    for msg in reversed(messages):
        content_str = str(msg.content)
        match = re.search(pattern, content_str, re.IGNORECASE)
        if match:
            pages_str = match.group(1)
            # Split by comma, strip spaces, convert to int
            successful_pages = sorted({int(p.strip()) for p in pages_str.split(",") if p.strip().isdigit()})
            break 
            
  

    if missing_metrics and successful_pages:
        print("LOG: Triggering Precision Harvest...")
        
        # 1. Identify EXACTLY what is missing so we can focus the LLM
        missing_metric_names = [m.get("metric_name") for m in missing_metrics]
        print(f"DEBUG: Hunting specifically for: {missing_metric_names}")
        
        pages_to_harvest = set()
        for page_number in successful_pages:
            for candidate_page in (page_number - 1, page_number, page_number + 1):
                if candidate_page >= 0:
                    pages_to_harvest.add(candidate_page)
           
        sorted_pages_to_harvest = sorted(pages_to_harvest)
        full_page_context = []
                
        for human_page in sorted_pages_to_harvest:
            try:
                # 1. Convert to 0-based ONLY for the PDF tool to prevent crashes/skips
                machine_index = human_page - 1
                page_text = read_sustainability_report_by_page.invoke({"page_number": int(machine_index)})
                        
                    # 2. Use the exact human page number for the text file logging
                if page_text and page_text.strip():
                    full_page_context.append(f"--- START PAGE {human_page} ---\n{page_text}\n--- END PAGE {human_page} ---")
                else:
                    full_page_context.append(f"--- START PAGE {human_page} ---\n[WARNING: PDF LOADER EXTRACTED ZERO TEXT]\n--- END PAGE {human_page} ---")
                            
            except Exception as exc:
                    full_page_context.append(f"[Page {human_page}] ERROR: {exc}")
        if full_page_context:
            precision_context = "\n\n".join(full_page_context)
            
            
            # 2. THE FIX: A highly aggressive, focused prompt
            precision_harvest_prompt = HumanMessage(
                content=(
                    f"You are an expert data auditor. Review the following pages from an ESG report.\n"
                    f"Your ONLY job is to find the values for these specific missing metrics: {missing_metric_names}.\n\n"
                    f"CRITICAL RULES:\n"
                    f"1. YOU MUST NOT change any metrics that were previously found. Retain the existing values for the ones not listed above.\n"
                    f"2. Look at EVERY SINGLE LINE of the provided text for the missing metrics.\n"
                    f"3. CRITICAL PAGE RULE: Rely ONLY on the '--- START PAGE X ---' headers provided below. "
                    f"IGNORE any printed page numbers (e.g., 'Page 204') found in the document text—they are often misleading.\n"
                    f"4. If a missing metric is genuinely not present in this text, return N/A.\n\n"
                    f"Text Context:\n{precision_context}"
                )
            )
            # We append this strongly worded prompt to force it to look again
            messages.append(precision_harvest_prompt)
            final_corporate_profile = structured_llm_agent2.invoke(messages)
    else:
        print("LOG: Harvest skipped (either no missing metrics or no pages found).")
        
    return {
        **state,
        "discovered_company": final_corporate_profile.discovered_company,
        "reporting_year": final_corporate_profile.reporting_year,
        "metric_results": [metric.model_dump() for metric in final_corporate_profile.extracted_metrics],
        "cso_name": final_corporate_profile.cso_name,
        "designation": final_corporate_profile.designation,
        "email": final_corporate_profile.email,
        "discovery_context": final_corporate_profile.discovery_context,
        "next_step": "agent_3_gap_analyst",
    }