"""Optional SMTP email notifications (no-op when SMTP_ENABLED is false)."""
from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage

from .config import settings

logger = logging.getLogger(__name__)


def send_email(to: str, subject: str, body: str) -> bool:
    if not settings.smtp_enabled or not to:
        logger.info("SMTP disabled -- skipping email to %s (%s)", to, subject)
        return False
    try:
        msg = EmailMessage()
        msg["From"] = settings.smtp_from
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content(body)
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as server:
            server.starttls()
            if settings.smtp_user:
                server.login(settings.smtp_user, settings.smtp_pass)
            server.send_message(msg)
        return True
    except Exception as exc:  # pragma: no cover - network guard
        logger.warning("Email send failed: %s", exc)
        return False


def welcome_email(name: str, to: str) -> None:
    send_email(
        to,
        f"Welcome to {settings.app_name}!",
        f"Hi {name},\n\nYour {settings.app_name} account is ready. "
        f"Post your property, shortlist favourites and connect with owners directly.\n\n"
        f"Happy house hunting!\n-- {settings.app_name}",
    )


def enquiry_email(owner_name: str, to: str, property_title: str, sender: str, message: str, phone: str) -> None:
    send_email(
        to,
        f"New enquiry for {property_title}",
        f"Hi {owner_name},\n\nYou received an enquiry from {sender}.\n"
        f"Phone: {phone or 'not provided'}\n\nMessage:\n{message}\n\n"
        f"Reply from your {settings.app_name} dashboard.\n-- {settings.app_name}",
    )
