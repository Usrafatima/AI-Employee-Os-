from __future__ import annotations

import logging

from apscheduler.schedulers.background import BackgroundScheduler

from app.database.session import SessionLocal
from app.services.communication_service import CommunicationService

logger = logging.getLogger(__name__)

_scheduler: BackgroundScheduler | None = None


def _scan_job() -> None:
    db = SessionLocal()
    try:
        created = CommunicationService.scan_and_create_reminders(db)
        if created:
            logger.info("Reminder scan created %d notification(s)", created)
    finally:
        db.close()


def start_reminder_scheduler() -> None:
    global _scheduler
    if _scheduler is not None:
        return
    _scheduler = BackgroundScheduler()
    _scheduler.add_job(_scan_job, "interval", minutes=5, id="comm_reminder_scan")
    _scheduler.start()
    logger.info("[scheduler] Communication Hub reminder scan started (every 5 min).")
