from __future__ import annotations

import re
from typing import Dict


def extract_contact_info(report_text: str) -> Dict[str, str]:
    patterns = {
        "name": r"(?:\d+\.\s*)?Designated ESG Compliance Officer:\s*(.+)",
        "designation": r"(?:\d+\.\s*)?Role/Designation:\s*(.+)",
        "email": r"(?:\d+\.\s*)?Official Office Email Address:\s*(.+)",
        "phone": r"(?:\d+\.\s*)?Direct Office Telephone:\s*(.+)",
        "linkedin": r"(?:\d+\.\s*)?LinkedIn Profile:\s*(.+)",
    }

    contact: Dict[str, str] = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, report_text)
        contact[key] = match.group(1).strip() if match else ""
    return contact
