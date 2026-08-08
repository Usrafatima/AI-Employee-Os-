from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.communication import (
    CalendarEventCreate,
    CalendarEventFromText,
    CalendarEventResponse,
    DraftUpdate,
    EmailLogResponse,
    EmailSendRequest,
    IncomingMessageCreate,
    IncomingMessageResult,
    MessageResponse,
    NotificationResponse,
    WhatsAppSendRequest,
)
from app.services.communication_service import CommunicationService

router = APIRouter()


@router.get("/health")
def get_communication_status():
    return {"module": "Communication Hub", "status": "active"}


# ---- Conversation history ---------------------------------------------------

@router.get("/customers/{customer_id}/messages", response_model=list[MessageResponse])
def get_conversation_history(customer_id: int, db: Session = Depends(get_db)):
    return CommunicationService.get_conversation_history(db, customer_id)


# ---- Messages / AI draft approval workflow -----------------------------------

@router.post("/messages/incoming", response_model=IncomingMessageResult, status_code=status.HTTP_201_CREATED)
def log_incoming_message(payload: IncomingMessageCreate, db: Session = Depends(get_db)):
    return CommunicationService.log_incoming_message(db, payload.customer_id, payload.channel, payload.content)


@router.get("/messages/pending-approval", response_model=list[MessageResponse])
def list_pending_approval(db: Session = Depends(get_db)):
    return CommunicationService.list_pending_approval(db)


@router.patch("/messages/{message_id}/draft", response_model=MessageResponse)
def update_draft(message_id: int, payload: DraftUpdate, db: Session = Depends(get_db)):
    return CommunicationService.update_draft(db, message_id, payload.content)


@router.post("/messages/{message_id}/approve", response_model=MessageResponse)
def approve_message(message_id: int, db: Session = Depends(get_db)):
    return CommunicationService.approve_message(db, message_id)


@router.post("/messages/{message_id}/reject", response_model=MessageResponse)
def reject_message(message_id: int, db: Session = Depends(get_db)):
    return CommunicationService.reject_message(db, message_id)


# ---- Direct email (quotations / invoices / follow-ups) ----------------------

@router.post("/email/send", response_model=EmailLogResponse, status_code=status.HTTP_201_CREATED)
def send_direct_email(payload: EmailSendRequest, db: Session = Depends(get_db)):
    return CommunicationService.send_direct_email(db, payload.to_email, payload.subject, payload.body, payload.customer_id)


@router.get("/email/history", response_model=list[EmailLogResponse])
def email_history(db: Session = Depends(get_db)):
    return CommunicationService.email_history(db)


# ---- WhatsApp -----------------------------------------------------------------

@router.post("/whatsapp/send", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def send_whatsapp(payload: WhatsAppSendRequest, db: Session = Depends(get_db)):
    return CommunicationService.send_whatsapp(db, payload.customer_id, payload.content)


# ---- Calendar -------------------------------------------------------------------

@router.post("/calendar/events", response_model=CalendarEventResponse, status_code=status.HTTP_201_CREATED)
def create_event(payload: CalendarEventCreate, db: Session = Depends(get_db)):
    return CommunicationService.create_event(db, payload.customer_id, payload.title, payload.description, payload.event_time, payload.created_via)


@router.post("/calendar/events/from-text", response_model=CalendarEventResponse, status_code=status.HTTP_201_CREATED)
def create_event_from_text(payload: CalendarEventFromText, db: Session = Depends(get_db)):
    return CommunicationService.create_event_from_text(db, payload.text, payload.customer_id, payload.created_via)


@router.get("/calendar/events", response_model=list[CalendarEventResponse])
def list_events(db: Session = Depends(get_db)):
    return CommunicationService.list_events(db)


# ---- Notifications ------------------------------------------------------------

@router.get("/notifications", response_model=list[NotificationResponse])
def list_notifications(db: Session = Depends(get_db)):
    return CommunicationService.list_notifications(db)


@router.post("/notifications/scan-now")
def scan_now(db: Session = Depends(get_db)):
    created = CommunicationService.scan_and_create_reminders(db)
    return {"ok": True, "notifications_created": created}
