from __future__ import annotations

import logging
import smtplib
from email.mime.text import MIMEText

from app.core.config import settings

logger = logging.getLogger(__name__)


def send_email(to_email: str, subject: str | None, body: str) -> None:
    """Send an email via SMTP using settings from the environment.

    If SMTP is not configured (no SMTP_HOST/SMTP_USER/SMTP_PASSWORD), this
    falls back to a "dry run" that just logs what would be sent, so the rest
    of the Communication Hub pipeline stays fully testable without live
    credentials.
    """
    if not settings.SMTP_HOST or not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        logger.info("[MAILER DRY RUN] To: %s | Subject: %s | Body: %s", to_email, subject, body)
        return

    msg = MIMEText(body)
    msg["Subject"] = subject or "(no subject)"
    msg["From"] = settings.EMAILS_FROM_EMAIL or settings.SMTP_USER
    msg["To"] = to_email

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        if settings.SMTP_TLS:
            server.starttls()
        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.sendmail(msg["From"], [to_email], msg.as_string())
