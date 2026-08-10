import uuid
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.calendar_event import CalendarEvent, EventStatus, EventSource
from app.schemas.calendar_event import (
    CalendarEventCreate,
    CalendarEventUpdate,
    CalendarEventOut,
    CalendarEventFromText,
)
from app.services import ai_service, calendar_reminder_service

router = APIRouter(tags=["Calendar Management"])


@router.post("", response_model=CalendarEventOut, status_code=201)
def create_event(payload: CalendarEventCreate, db: Session = Depends(get_db)):
    event = CalendarEvent(**payload.model_dump())
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


@router.post("/schedule-from-text", response_model=CalendarEventOut, status_code=201)
def schedule_from_text(payload: CalendarEventFromText, db: Session = Depends(get_db)):
    """
    Voice/text scheduling entry point: takes a raw instruction like
    'Schedule a call with the vendor next Tuesday at 2pm' and creates the event.
    The AI Executive Assistant / voice pipeline (owned by another module) is expected
    to forward the transcribed instruction here.
    """
    parsed = ai_service.parse_event_from_text(
        payload.instruction, reference_datetime=datetime.utcnow().isoformat()
    )
    try:
        start_time = datetime.fromisoformat(parsed["start_time"])
    except (KeyError, ValueError, TypeError):
        raise HTTPException(422, "Couldn't determine a valid date/time from that instruction.")

    end_time = None
    if parsed.get("end_time"):
        try:
            end_time = datetime.fromisoformat(parsed["end_time"])
        except ValueError:
            end_time = None

    event = CalendarEvent(
        company_id=payload.company_id,
        title=parsed.get("title") or payload.instruction[:255],
        start_time=start_time,
        end_time=end_time,
        location=parsed.get("location"),
        attendees=parsed.get("attendees"),
        source=EventSource.voice,
        created_by=payload.created_by,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


@router.get("", response_model=List[CalendarEventOut])
def list_events(company_id: uuid.UUID, db: Session = Depends(get_db)):
    return (
        db.query(CalendarEvent)
        .filter(CalendarEvent.company_id == company_id)
        .order_by(CalendarEvent.start_time.asc())
        .all()
    )


@router.get("/{event_id}", response_model=CalendarEventOut)
def get_event(event_id: uuid.UUID, db: Session = Depends(get_db)):
    event = db.query(CalendarEvent).filter(CalendarEvent.id == event_id).first()
    if not event:
        raise HTTPException(404, "Event not found")
    return event


@router.patch("/{event_id}", response_model=CalendarEventOut)
def update_event(event_id: uuid.UUID, payload: CalendarEventUpdate, db: Session = Depends(get_db)):
    event = db.query(CalendarEvent).filter(CalendarEvent.id == event_id).first()
    if not event:
        raise HTTPException(404, "Event not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(event, field, value)
    db.commit()
    db.refresh(event)
    return event


@router.delete("/{event_id}", status_code=204)
def delete_event(event_id: uuid.UUID, db: Session = Depends(get_db)):
    event = db.query(CalendarEvent).filter(CalendarEvent.id == event_id).first()
    if not event:
        raise HTTPException(404, "Event not found")
    db.delete(event)
    db.commit()


@router.post("/reminders/run")
def run_reminders(company_id: uuid.UUID, db: Session = Depends(get_db)):
    """
    Checks for events starting in ~24h or ~12h and drafts reminder messages.
    Intended to run on a schedule; actual delivery (email/WhatsApp) is handled
    by the Communication Hub module using these drafted messages.
    """
    return {"reminders": calendar_reminder_service.run_event_reminders(db, company_id)}