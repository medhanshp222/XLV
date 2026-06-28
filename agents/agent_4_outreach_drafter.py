import json
import os
from typing import Any

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from state import AgentState

load_dotenv(override=True)


def _extract_text(response: Any) -> str:
    text = response.content
    if isinstance(text, list):
        text = "".join(
            block.get("text", "") for block in text if isinstance(block, dict)
        )
    return str(text or "").strip()


def _parse_json(text: str) -> dict:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # If the model returns surrounding text, attempt to extract the first JSON block.
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start : end + 1])
            except json.JSONDecodeError:
                pass
    return {}


def _build_prompt(state: AgentState) -> str:
    return (
        "You are an expert enterprise sales copywriter specializing in ESG and corporate compliance software.\n"
        "Use the context below to create a polished outreach email.\n\n"
        "Context:\n"
        f"- Target Company: {state.get('discovered_company', '')}\n"
        f"- Recipient Name: {state.get('cso_name', '')}\n"
        f"- Recipient Title: {state.get('designation', '')}\n"
        f"- New Regulation: {state.get('raw_laws_text', '')}\n"
        f"- Audit Status: {state.get('compliance_status', '')}\n"
        f"- Audit Rationale: {state.get('audit_reasoning', '')}\n\n"
        "Requirements:\n"
        "1. Write a subject line no longer than 80 characters.\n"
        "2. Write an HTML email body with short paragraphs and professional tone.\n"
        "3. Mention the Indian Carbon Market and unit-specific intensity baselining.\n"
        "4. Keep the email consultative and avoid sounding alarmist.\n"
        "5. Return only valid JSON with keys: subject, body.\n"
        "Example response:\n"
        "{\n"
        "  \"subject\": \"...\",\n"
        "  \"body\": \"<p>...</p>\"\n"
        "}\n"
    )


def _create_outreach_email(state: AgentState) -> tuple[str, str, str]:
    llm_agent4 = ChatGoogleGenerativeAI(
        model="gemini-3.1-flash-lite",
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0.7,
    )

    prompt_text = _build_prompt(state)
    response = llm_agent4.invoke(prompt_text)
    extracted = _extract_text(response)
    parsed = _parse_json(extracted)

    subject = parsed.get("subject", f"Improve ESG compliance for {state.get('discovered_company', '').strip()}")
    body = parsed.get("body", extracted)

    return subject, body, extracted


def agent_4_outreach_drafter(state: AgentState) -> AgentState:
    subject, body, draft_content = _create_outreach_email(state)
    return {
        **state,
        "final_outreach_draft": draft_content,
        "outreach_email_subject": subject,
        "outreach_email_body": body,
        "next_step": "end",
    }
