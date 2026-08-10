"""
Smart Notifications for Calendar Management: fires a reminder ~24 hours and ~12 hours
before an event's start_time. Designed to be called on a schedule (cron/Celery beat)
via the /api/calendar/reminders/run endpoint; the Communication Hub module is the
actual delivery channel (email/WhatsApp) — this service returns drafted messages plus
which event+window they belong to, which the Communication Hub can then send.
"""
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models.calendar_event import CalendarEvent, EventStatus


def draft_event_reminder(event: CalendarEvent, hours_before: int) -> str:
    return (
        f"Reminder: \"{event.title}\" starts in about {hours_before} hours "
        f"({event.start_time.strftime('%Y-%m-%d %H:%M')})."
        + (f" Location: {event.location}." if event.location else "")
    )


def run_event_reminders(db: Session, company_id) -> list[dict]:
    now = datetime.utcnow()
    upcoming = (
        db.query(CalendarEvent)
        .filter(
            CalendarEvent.company_id == company_id,
            CalendarEvent.status == EventStatus.scheduled,
            CalendarEvent.start_time > now,
            CalendarEvent.start_time <= now + timedelta(hours=24, minutes=15),
        )
        .all()
    )

    results = []
    for event in upcoming:
        hours_until = (event.start_time - now).total_seconds() / 3600

        if not event.reminder_24h_sent and 23.75 <= hours_until <= 24.25:
            results.append({
                "event_id": str(event.id),
                "window": "24h",
                "message": draft_event_reminder(event, 24),
            })
            event.reminder_24h_sent = True

        if not event.reminder_12h_sent and 11.75 <= hours_until <= 12.25:
            results.append({
                "event_id": str(event.id),
                "window": "12h",
                "message": draft_event_reminder(event, 12),
            })
            event.reminder_12h_sent = True

    db.commit()
    return results
