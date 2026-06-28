import os
import re
from typing import Literal
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from state import AgentState

load_dotenv(override=True)


class ComplianceVerdict(BaseModel):
    regulatory_limit_found: str = Field(description="The numeric target or framework rule extracted from the law for the requested metric.")
    reported_metric_found: str = Field(description="The company's current reported value for the requested metric.")
    compliance_status: Literal["COMPLIANT", "NON-COMPLIANT", "COMPLIANCE OPAQUE - AUDIT REQUIRED", "NO STATUTORY MANDATE"] = Field(
        description="Must be one of: 'COMPLIANT', 'NON-COMPLIANT', 'COMPLIANCE OPAQUE - AUDIT REQUIRED', or 'NO STATUTORY MANDATE'."
    )
    gap_calculation: str = Field(description="The shortfall or delta between the company’s reported metric and the regulatory target. State 'N/A' if math isn't possible.")
    verdict_reasoning: str = Field(description="A brief explanation analyzing current performance against the requested metric target, ignoring future targets.")


def _extract_numeric_value(text: str | None) -> float | None:
    if not text:
        return None
    match = re.search(r"(-?\d+(?:\.\d+)?)", str(text))
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
    primary_metric_name = state.get("primary_metric_name") or "requested metric"
    numeric_target_input = state.get("numeric_target")
    company_name_input = state["discovered_company"]

    normalized_target = str(numeric_target_input or "").strip().lower()
    no_mandate_detected = normalized_target in {"", "n/a", "none"} or "no statutory mandate" in normalized_target or "no mandate" in normalized_target

    if no_mandate_detected:
        return {
            **state,
            "compliance_status": "NO STATUTORY MANDATE",
            "audit_reasoning": "No specific numeric target is mandated by current regulations. Performance is measured against internal baselines.",
            "next_step": "agent_4_outreach_drafter",
        }

    prompt_text = (
        "You are a strict corporate compliance auditor.\n"
        f"Target Company: {company_name_input}\n"
        f"Requested metric: {primary_metric_name}\n"
        f"Numeric target from Agent 1: {numeric_target_input}\n"
        f"Regulatory Framework found by Agent 1: {laws_input}\n"
        f"Company Metrics found by Agent 2: {company_metrics_input}\n\n"
        "Task:\n"
        f"1. Compare the company's current reported value for {primary_metric_name} against the official target or mandate found by Agent 1.\n"
        "2. Apply these rules exactly: \n"
        "   - If the company metric is blank, 'N/A', 'Metric not found', or otherwise opaque, classify the result as 'COMPLIANCE OPAQUE - AUDIT REQUIRED'.\n"
        "   - If the company's reported value is lower than the target, classify as 'NON-COMPLIANT'.\n"
        "   - If the company's reported value is equal to or higher than the target, classify as 'COMPLIANT'.\n"
        "   - If the status is 'COMPLIANCE OPAQUE - AUDIT REQUIRED', set gap_calculation to 'N/A' and explicitly state that the metric could not be located in the public reports.\n"
        "3. Calculate the numeric difference between the company's reported value and the target when it is mathematically meaningful."
    )

    final_verdict = structured_auditor.invoke(prompt_text)

    regulatory_target = _extract_numeric_value(laws_input)
    company_value = _extract_numeric_value(company_metrics_input)

    if (
        company_metrics_input
        and company_metrics_input.strip().lower() not in {"", "n/a", "metric not found"}
        and regulatory_target is not None
        and company_value is not None
    ):
        delta = regulatory_target - company_value
        if delta > 0:
            final_verdict.compliance_status = "NON-COMPLIANT"
            final_verdict.gap_calculation = f"{delta:.2f}"
            final_verdict.verdict_reasoning = (
                f"{company_name_input} reports {company_metrics_input}, which is below the target of {regulatory_target:.2f}."
            )
        else:
            final_verdict.compliance_status = "COMPLIANT"
            final_verdict.gap_calculation = "0.00"
            final_verdict.verdict_reasoning = (
                f"{company_name_input} reports {company_metrics_input}, which meets or exceeds the target of {regulatory_target:.2f}."
            )
    else:
        final_verdict.compliance_status = "COMPLIANCE OPAQUE - AUDIT REQUIRED"
        final_verdict.gap_calculation = "N/A"
        final_verdict.verdict_reasoning = (
            f"The metric could not be located in the public reports for {primary_metric_name}."
        )

    final_verdict.regulatory_limit_found = f"{regulatory_target:.2f}" if regulatory_target is not None else "N/A"
    final_verdict.reported_metric_found = company_metrics_input or "N/A"

    return {
        **state,
        "compliance_status": final_verdict.compliance_status,
        "audit_reasoning": final_verdict.verdict_reasoning,
        "next_step": "agent_4_outreach_drafter",
    }
