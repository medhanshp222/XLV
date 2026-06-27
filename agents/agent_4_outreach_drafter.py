import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from state import AgentState

load_dotenv(override=True)


def agent_4_outreach_drafter(state: AgentState) -> AgentState:
    llm_agent4 = ChatGoogleGenerativeAI(
        model="gemini-3.1-flash-lite",
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0.7,
    )

    company_name = state["discovered_company"]
    cso_name = state["cso_name"]
    cso_title = state["designation"]
    framework_rules = state["raw_laws_text"]
    audit_verdict = state["compliance_status"]
    audit_reasoning = state["audit_reasoning"]

    prompt_text = (
        "You are an expert enterprise sales copywriter specializing in ESG and corporate compliance software.\n"
        "Your goal is to draft a highly professional, cold outreach email to a corporate executive.\n\n"
        "Context Given:\n"
        f"- Target Company: {company_name}\n"
        f"- Recipient Name: {cso_name}\n"
        f"- Recipient Title: {cso_title}\n"
        f"- New Regulation: {framework_rules}\n"
        f"- Audit Status: {audit_verdict}\n"
        f"- Audit Rationale: {audit_reasoning}\n\n"
        "Guidelines:\n"
        "1. Keep it professional, consultative, and respectful. Do not sound alarmist or like you are accusing them.\n"
        "2. Explicitly reference the newly transitioning Indian Carbon Market (ICM) intensity targets.\n"
        "3. Highlight that tracking unit-specific baselines dynamically can be challenging.\n"
        "4. Since direct email was N/A, add a small placeholder note at the top indicating this should be sent via LinkedIn message if needed.\n"
        "5. Pitch an introductory call to showcase how our automated compliance platform handles dynamic intensity forecasting."
    )

    response = llm_agent4.invoke(prompt_text)

    # Safely extract the string if Gemini returns a list block
    draft_content = response.content
    if isinstance(draft_content, list):
        draft_content = "".join([
            block.get("text", "") for block in draft_content if isinstance(block, dict) and "text" in block
        ])

    return {
        **state,
        "final_outreach_draft": draft_content,
        "next_step": "end",
    }
