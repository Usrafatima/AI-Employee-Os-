from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Sequence

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.communication import (
    CalendarEvent,
    EmailLog,
    EmailStatus,
    Message,
    MessageStatus,
    Notification,
)
from app.models.crm import Customer
from app.services.ai_reply_service import generate_ai_reply
from app.services.mailer_service import Attachment, send_email

logger = logging.getLogger(__name__)


class CommunicationService:
    # ---- Customers / conversation history -----------------------------------

    @staticmethod
    def _get_customer_or_404(db: Session, customer_id: int) -> Customer:
        customer = db.get(Customer, customer_id)
        if not customer:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found")
        return customer

    @staticmethod
    def get_conversation_history(db: Session, customer_id: int) -> list[Message]:
        CommunicationService._get_customer_or_404(db, customer_id)
        return (
            db.query(Message)
            .filter(Message.customer_id == customer_id)
            .order_by(Message.created_at.asc())
            .all()
        )

    # ---- Incoming messages + AI draft ----------------------------------------

    @staticmethod
    def log_incoming_message(db: Session, customer_id: int, channel: str, content: str) -> dict[str, Any]:
        customer = CommunicationService._get_customer_or_404(db, customer_id)

        incoming = Message(
            customer_id=customer_id,
            direction="incoming",
            channel=channel,
            content=content,
            ai_generated=False,
            status=MessageStatus.SENT.value,
        )
        db.add(incoming)
        db.flush()

        draft_text = generate_ai_reply(content, customer.full_name)
        draft = Message(
            customer_id=customer_id,
            direction="outgoing",
            channel=channel,
            content=draft_text,
            ai_generated=True,
            status=MessageStatus.PENDING_APPROVAL.value,
        )
        db.add(draft)
        db.commit()
        db.refresh(incoming)
        db.refresh(draft)
        return {"incoming": incoming, "ai_draft": draft}

    @staticmethod
    def list_pending_approval(db: Session) -> list[Message]:
        return (
            db.query(Message)
            .filter(Message.status == MessageStatus.PENDING_APPROVAL.value)
            .order_by(Message.created_at.asc())
            .all()
        )

    @staticmethod
    def update_draft(db: Session, message_id: int, content: str) -> Message:
        message = db.get(Message, message_id)
        if not message:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")
        if message.status != MessageStatus.PENDING_APPROVAL.value:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Message is not editable")
        message.content = content
        db.commit()
        db.refresh(message)
        return message

    @staticmethod
    def approve_message(db: Session, message_id: int) -> Message:
        message = db.get(Message, message_id)
        if not message:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")
        if message.status != MessageStatus.PENDING_APPROVAL.value:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Cannot approve message with status {message.status}")

        customer = CommunicationService._get_customer_or_404(db, message.customer_id)

        if message.channel == "email":
            email_log = EmailLog(
                message_id=message.id,
                to_email=customer.email,
                subject="Re: your message",
                body=message.content,
                status=EmailStatus.PENDING.value,
            )
            db.add(email_log)
            db.flush()
            try:
                send_email(customer.email, "Re: your message", message.content)
                email_log.status = EmailStatus.SENT.value
                email_log.sent_at = datetime.utcnow()
            except Exception as exc:  # noqa: BLE001
                email_log.status = EmailStatus.FAILED.value
                email_log.error = str(exc)
                message.status = MessageStatus.APPROVED.value
                db.commit()
                raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Email send failed: {exc}") from exc
        elif message.channel == "whatsapp":
            logger.info("[WHATSAPP SIMULATED] To %s: %s", customer.phone or customer.full_name, message.content)

        message.status = MessageStatus.SENT.value
        db.commit()
        db.refresh(message)
        return message

    @staticmethod
    def reject_message(db: Session, message_id: int) -> Message:
        message = db.get(Message, message_id)
        if not message:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")
        if message.status != MessageStatus.PENDING_APPROVAL.value:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot reject this message")
        message.status = MessageStatus.REJECTED.value
        db.commit()
        db.refresh(message)
        return message

    # ---- Direct email (quotations / invoices / follow-ups) -------------------

    @staticmethod
    def send_direct_email(
        db: Session,
        to_email: str,
        subject: str | None,
        body: str,
        customer_id: int | None,
        attachments: Sequence[Attachment] | None = None,
    ) -> EmailLog:
        """Send an email and record it in the email log.

        ``attachments`` is optional and defaults to none, so existing callers
        are unaffected. The Finance module passes generated quotation, invoice
        and receipt PDFs through it.
        """
        if customer_id is not None:
            CommunicationService._get_customer_or_404(db, customer_id)

        email_log = EmailLog(to_email=to_email, subject=subject, body=body, status=EmailStatus.PENDING.value)
        db.add(email_log)
        db.flush()

        if customer_id is not None:
            db.add(Message(customer_id=customer_id, direction="outgoing", channel="email", content=body, ai_generated=False, status=MessageStatus.SENT.value))

        try:
            send_email(to_email, subject, body, attachments=attachments)
            email_log.status = EmailStatus.SENT.value
            email_log.sent_at = datetime.utcnow()
        except Exception as exc:  # noqa: BLE001
            email_log.status = EmailStatus.FAILED.value
            email_log.error = str(exc)
            db.commit()
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Email send failed: {exc}") from exc

        db.commit()
        db.refresh(email_log)
        return email_log

    @staticmethod
    def email_history(db: Session) -> list[EmailLog]:
        return db.query(EmailLog).order_by(EmailLog.created_at.desc()).all()

    # ---- WhatsApp (simulated until a live API is wired up) -------------------

    @staticmethod
    def send_whatsapp(db: Session, customer_id: int, content: str) -> Message:
        customer = CommunicationService._get_customer_or_404(db, customer_id)
        logger.info("[WHATSAPP SIMULATED] To %s: %s", customer.phone or customer.full_name, content)
        message = Message(customer_id=customer_id, direction="outgoing", channel="whatsapp", content=content, ai_generated=False, status=MessageStatus.SENT.value)
        db.add(message)
        db.commit()
        db.refresh(message)
        return message

    # ---- Calendar --------------------------------------------------------------

    @staticmethod
    def create_event(db: Session, customer_id: int | None, title: str, description: str | None, event_time: datetime, created_via: str) -> CalendarEvent:
        if customer_id is not None:
            CommunicationService._get_customer_or_404(db, customer_id)
        event = CalendarEvent(customer_id=customer_id, title=title, description=description, event_time=event_time, created_via=created_via)
        db.add(event)
        db.commit()
        db.refresh(event)
        return event

    @staticmethod
    def create_event_from_text(db: Session, text: str, customer_id: int | None, created_via: str) -> CalendarEvent:
        try:
            from dateparser.search import search_dates  # type: ignore
        except ImportError:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="dateparser package is not installed")

        results = search_dates(text, settings={"PREFER_DATES_FROM": "future"})
        if not results:
            raise HTTPException(status_code=422, detail="Could not detect a date/time in the given text")

        matched_phrase, event_time = results[0]
        title = text.replace(matched_phrase, "").strip(" ,.-") or "Scheduled event"
        return CommunicationService.create_event(db, customer_id, title, text, event_time, created_via)

    @staticmethod
    def list_events(db: Session) -> list[CalendarEvent]:
        return db.query(CalendarEvent).order_by(CalendarEvent.event_time.asc()).all()

    # ---- Notifications -----------------------------------------------------------

    @staticmethod
    def list_notifications(db: Session) -> list[Notification]:
        return db.query(Notification).order_by(Notification.created_at.desc()).all()

    @staticmethod
    def scan_and_create_reminders(db: Session) -> int:
        """Scan upcoming events and create 24h/12h reminder notifications.
        Called both by the background scheduler and by the manual scan-now endpoint.
        """
        now = datetime.utcnow()
        created = 0
        events = db.query(CalendarEvent).filter(CalendarEvent.event_time > now).all()

        for event in events:
            hours_until = (event.event_time - now).total_seconds() / 3600
            for reminder_type, window_hours in (("24h", 24), ("12h", 12)):
                if not (window_hours - 0.25 < hours_until <= window_hours):
                    continue
                exists = (
                    db.query(Notification)
                    .filter(Notification.event_id == event.id, Notification.type == reminder_type)
                    .first()
                )
                if exists:
                    continue

                message = f'Reminder: "{event.title}" is coming up at {event.event_time.isoformat()} (in ~{reminder_type}).'
                notification = Notification(event_id=event.id, type=reminder_type, sent=False, message=message)
                db.add(notification)
                db.flush()

                if event.customer_id:
                    customer = db.get(Customer, event.customer_id)
                    if customer and customer.email:
                        try:
                            send_email(customer.email, f"Reminder: {event.title}", message)
                            notification.sent = True
                        except Exception:  # noqa: BLE001
                            logger.exception("Failed to send reminder email")
                created += 1

        db.commit()
        return created
