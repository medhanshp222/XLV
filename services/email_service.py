import os
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Dict

from dotenv import load_dotenv

load_dotenv(override=True)


def _send_via_smtp(to: str, subject: str, body: str, sender: str) -> Dict[str, Any]:
    host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER")
    password = os.getenv("SMTP_PASSWORD")

    if not user or not password:
        raise ValueError("SMTP_USER and SMTP_PASSWORD must be set to use SMTP sending")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = to
    part = MIMEText(body, "html")
    msg.attach(part)

    try:
        try:
            import certifi
            context = ssl.create_default_context(cafile=certifi.where())
        except Exception:
            context = ssl.create_default_context()
        with smtplib.SMTP(host, port, timeout=30) as server:
            server.starttls(context=context)
            server.login(user, password)
            server.sendmail(sender, [to], msg.as_string())
    except smtplib.SMTPAuthenticationError:
        raise ValueError("SMTP authentication failed. Check SMTP_USER and SMTP_PASSWORD (use an app password if using Gmail).")
    except Exception as exc:
        raise RuntimeError(f"SMTP send failed: {exc}") from exc

    return {"method": "smtp", "recipient": to, "subject": subject}


def send_email(to: str, subject: str, body: str, sender: str | None = None) -> Dict[str, Any]:
    if not to or str(to).strip().upper() == "N/A":
        raise ValueError("Recipient email is required and must be a valid address")

    if not subject:
        raise ValueError("Email subject is required")

    if not body:
        raise ValueError("Email body is required")

    if not sender:
        sender = os.getenv("EMAIL_FROM") or os.getenv("SMTP_USER")
        if not sender:
            raise ValueError("EMAIL_FROM or SMTP_USER must be set to determine the sender address")

    return _send_via_smtp(to=to, subject=subject, body=body, sender=sender)
