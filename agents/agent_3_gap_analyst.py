import os
from typing import Literal
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from state import AgentState

load_dotenv(override=True)


class ComplianceVerdict(BaseModel):
    regulatory_limit_found: str = Field(description="The numeric legal limit or framework rules extracted from the law.")
    reported_metric_found: str = Field(description="The company's current reported metric.")
    compliance_status: Literal["COMPLIANT", "NON-COMPLIANT", "COMPLIANCE OPAQUE - AUDIT REQUIRED"] = Field(
        description="Must be one of: 'COMPLIANT', 'NON-COMPLIANT', or 'COMPLIANCE OPAQUE - AUDIT REQUIRED'."
    )
    gap_calculation: str = Field(description="The mathematical difference between current reality and the law. State 'N/A' if math isn't possible.")
    verdict_reasoning: str = Field(description="A brief explanation analyzing current performance against the mandate, ignoring future targets.")


def agent_3_gap_analyst(state: AgentState) -> AgentState:
    llm_agent3 = ChatGoogleGenerativeAI(
        model="gemini-3.1-flash-lite",
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0,
    )
    structured_auditor = llm_agent3.with_structured_output(ComplianceVerdict)

    laws_input = state["raw_laws_text"]
    company_metrics_input = state["company_emission_metric"]
    company_name_input = state["discovered_company"]

    prompt_text = (
        "You are a strict corporate compliance auditor.\n"
        f"Target Company: {company_name_input}\n"
        f"Regulatory Framework found by Agent 1: {laws_input}\n"
        f"Company Metrics found by Agent 2: {company_metrics_input}\n\n"
        "Task:\n"
        "1. Compare the company's current performance against the regulatory limits or guidelines.\n"
        "2. Apply these rules exactly: \n"
        "   - If the legal framework says the limits are site-specific, governed by Consent to Operate (CTO/CFO), or if the company metric is 'N/A', classify the result as 'COMPLIANCE OPAQUE - AUDIT REQUIRED'.\n"
        "   - If the status is 'COMPLIANCE OPAQUE - AUDIT REQUIRED', set gap_calculation to 'N/A' and make the reasoning explicitly note that public reporting lacks the facility-specific baselines required to verify adherence to local CFO mandates.\n"
        "   - Otherwise, determine if they are currently COMPLIANT or NON-COMPLIANT (ignore their future targets like 2030; look at current data).\n"
        "3. Estimate the gap and write a concise audit verdict."
    )

    final_verdict = structured_auditor.invoke(prompt_text)

    return {
        **state,
        "compliance_status": final_verdict.compliance_status,
        "audit_reasoning": final_verdict.verdict_reasoning,
        "next_step": "agent_4_outreach_drafter",
    }
