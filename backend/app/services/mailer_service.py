from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage
from typing import Sequence

from app.core.config import settings

logger = logging.getLogger(__name__)

#: An attachment as ``(filename, content, mime_type)``, e.g.
#: ``("INV-2026-001.pdf", b"%PDF-1.4...", "application/pdf")``.
Attachment = tuple[str, bytes, str]


def send_email(
    to_email: str,
    subject: str | None,
    body: str,
    attachments: Sequence[Attachment] | None = None,
) -> None:
    """Send an email via SMTP using settings from the environment.

    If SMTP is not configured (no SMTP_HOST/SMTP_USER/SMTP_PASSWORD), this
    falls back to a "dry run" that just logs what would be sent, so the rest
    of the Communication Hub pipeline stays fully testable without live
    credentials.

    ``attachments`` is optional and defaults to none, so existing callers are
    unaffected. The Finance module uses it to attach quotation, invoice and
    receipt PDFs.
    """
    if not settings.SMTP_HOST or not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        logger.info(
            "[MAILER DRY RUN] To: %s | Subject: %s | Attachments: %s | Body: %s",
            to_email,
            subject,
            [name for name, _, _ in attachments] if attachments else [],
            body,
        )
        return

    msg = EmailMessage()
    msg["Subject"] = subject or "(no subject)"
    msg["From"] = settings.EMAILS_FROM_EMAIL or settings.SMTP_USER
    msg["To"] = to_email
    msg.set_content(body)

    for filename, content, mime_type in attachments or []:
        maintype, _, subtype = mime_type.partition("/")
        msg.add_attachment(
            content,
            maintype=maintype or "application",
            subtype=subtype or "octet-stream",
            filename=filename,
        )

    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        if settings.SMTP_TLS:
            server.starttls()
        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.send_message(msg)
