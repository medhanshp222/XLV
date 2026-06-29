import os
import re
from typing import Literal
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from state import AgentState

load_dotenv(override=True)


class ComplianceVerdict(BaseModel):
    regulatory_limit_found: str = Field(description="The numeric RCO target or framework rules extracted from the law.")
    reported_metric_found: str = Field(description="The company's current renewable energy percentage.")
    compliance_status: Literal["COMPLIANT", "NON-COMPLIANT", "COMPLIANCE OPAQUE - AUDIT REQUIRED"] = Field(
        description="Must be one of: 'COMPLIANT', 'NON-COMPLIANT', or 'COMPLIANCE OPAQUE - AUDIT REQUIRED'."
    )
    gap_calculation: str = Field(description="The percentage-point shortfall between the company’s current renewable percentage and the mandated RCO target. State 'N/A' if math isn't possible.")
    verdict_reasoning: str = Field(description="A brief explanation analyzing current performance against the renewable mandate, ignoring future targets.")


def _extract_percentage(text: str | None) -> float | None:
    if not text:
        return None
    match = re.search(r"(\d+(?:\.\d+)?)\s*%", str(text))
    if match:
        return float(match.group(1))
    return None


def agent_3_gap_analyst(state: AgentState) -> AgentState:
    llm_agent3 = ChatGoogleGenerativeAI(
        model="gemini-3.1-flash-lite",
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0,
    )
    structured_auditor = llm_agent3.with_structured_output(ComplianceVerdict)

    laws_input = state["raw_laws_text"]
    company_metrics_input = state.get("extracted_metric_value") or state.get("company_emission_metric") or ""
    company_name_input = state["discovered_company"]

    prompt_text = (
        "You are a strict corporate compliance auditor.\n"
        f"Target Company: {company_name_input}\n"
        f"Regulatory Framework found by Agent 1: {laws_input}\n"
        f"Company Metrics found by Agent 2: {company_metrics_input}\n\n"
        "Task:\n"
        "1. Compare the company's current renewable energy percentage against the official Renewable Consumption Obligation (RCO) target.\n"
        "2. Apply these rules exactly: \n"
        "   - If the company metric is 'N/A' or the data is otherwise opaque, classify the result as 'COMPLIANCE OPAQUE - AUDIT REQUIRED'.\n"
        "   - If the company's renewable percentage is lower than the mandated RCO target, classify as 'NON-COMPLIANT'.\n"
        "   - If the company's renewable percentage is equal to or higher than the mandated RCO target, classify as 'COMPLIANT'.\n"
        "   - If the status is 'COMPLIANCE OPAQUE - AUDIT REQUIRED', set gap_calculation to 'N/A' and make the reasoning explicitly note that public reporting lacks the facility-specific baselines required to verify adherence to the RCO mandate.\n"
        "3. Subtract the company's current percentage from the target percentage to show the exact percentage shortfall in gap_calculation."
    )

    final_verdict = structured_auditor.invoke(prompt_text)

    regulatory_target = _extract_percentage(laws_input)
    company_percentage = _extract_percentage(company_metrics_input)

    if company_metrics_input and company_metrics_input.lower() != "n/a" and regulatory_target is not None and company_percentage is not None:
        shortfall = regulatory_target - company_percentage
        if shortfall > 0:
            final_verdict.compliance_status = "NON-COMPLIANT"
            final_verdict.gap_calculation = f"{shortfall:.2f} percentage points"
            final_verdict.verdict_reasoning = (
                f"{company_name_input} reports {company_metrics_input}, which is below the mandated RCO target of {regulatory_target:.2f}%."
            )
        else:
            final_verdict.compliance_status = "COMPLIANT"
            final_verdict.gap_calculation = "0.00 percentage points"
            final_verdict.verdict_reasoning = (
                f"{company_name_input} reports {company_metrics_input}, which meets or exceeds the mandated RCO target of {regulatory_target:.2f}%."
            )
    else:
        final_verdict.compliance_status = "COMPLIANCE OPAQUE - AUDIT REQUIRED"
        final_verdict.gap_calculation = "N/A"
        final_verdict.verdict_reasoning = (
            "Public reporting lacks the facility-specific baselines required to verify adherence to the RCO mandate."
        )

    final_verdict.regulatory_limit_found = f"{regulatory_target:.2f}%" if regulatory_target is not None else "N/A"
    final_verdict.reported_metric_found = company_metrics_input or "N/A"

    return {
        **state,
        "compliance_status": final_verdict.compliance_status,
        "audit_reasoning": final_verdict.verdict_reasoning,
        "next_step": "agent_4_outreach_drafter",
    }
