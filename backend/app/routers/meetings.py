import json
import os
import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.meeting import Meeting, MeetingStatus
from app.models.task import Task, TaskPriority
from app.schemas.meeting import MeetingCreate, MeetingOut
from app.services import transcription_service, ai_service

router = APIRouter(tags=["Meeting Assistant"])


@router.post("", response_model=MeetingOut, status_code=201)
def create_meeting(payload: MeetingCreate, db: Session = Depends(get_db)):
    meeting = Meeting(**payload.model_dump())
    db.add(meeting)
    db.commit()
    db.refresh(meeting)
    return meeting


@router.post("/{meeting_id}/upload-audio", response_model=MeetingOut)
async def upload_audio(meeting_id: uuid.UUID, file: UploadFile = File(...), db: Session = Depends(get_db)):
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(404, "Meeting not found")

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    ext = file.filename.split(".")[-1].lower()
    saved_path = os.path.join(settings.UPLOAD_DIR, f"{uuid.uuid4()}.{ext}")
    with open(saved_path, "wb") as f:
        f.write(await file.read())

    meeting.audio_file_path = saved_path
    meeting.status = MeetingStatus.recorded
    db.commit()
    db.refresh(meeting)
    return meeting


@router.post("/{meeting_id}/transcribe-and-summarize", response_model=MeetingOut)
def transcribe_and_summarize(meeting_id: uuid.UUID, create_tasks: bool = True, db: Session = Depends(get_db)):
    """
    Full pipeline: Whisper transcription -> AI summary + action items + deadlines.
    Optionally auto-creates Task Manager entries for each action item (create_tasks=True),
    matching the "Deadline extraction" + cross-module automation described in the project brief.
    """
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(404, "Meeting not found")
    if not meeting.audio_file_path:
        raise HTTPException(400, "No audio uploaded for this meeting yet")

    meeting.status = MeetingStatus.transcribing
    db.commit()

    try:
        transcript = transcription_service.transcribe_audio(meeting.audio_file_path)
        result = ai_service.summarize_meeting(transcript)

        meeting.transcript = transcript
        meeting.ai_summary = result.get("summary", "")
        meeting.action_items = json.dumps(result.get("action_items", []))
        meeting.deadlines_extracted = json.dumps(result.get("deadlines", []))
        meeting.status = MeetingStatus.summarized

        if create_tasks:
            for item in result.get("action_items", []):
                db.add(Task(
                    company_id=meeting.company_id,
                    title=item[:255] if isinstance(item, str) else str(item)[:255],
                    description=f"Auto-created from meeting: {meeting.title}",
                    priority=TaskPriority.medium,
                    source="meeting",
                    source_reference_id=meeting.id,
                    created_by=meeting.created_by,
                ))
    except Exception as e:
        meeting.status = MeetingStatus.failed
        meeting.ai_summary = f"Processing failed: {str(e)}"

    db.commit()
    db.refresh(meeting)
    return meeting


@router.get("", response_model=List[MeetingOut])
def list_meetings(company_id: uuid.UUID, db: Session = Depends(get_db)):
    return (
        db.query(Meeting)
        .filter(Meeting.company_id == company_id)
        .order_by(Meeting.created_at.desc())
        .all()
    )


@router.get("/{meeting_id}", response_model=MeetingOut)
def get_meeting(meeting_id: uuid.UUID, db: Session = Depends(get_db)):
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(404, "Meeting not found")
    return meeting


@router.delete("/{meeting_id}", status_code=204)
def delete_meeting(meeting_id: uuid.UUID, db: Session = Depends(get_db)):
    meeting = db.query(Meeting).filter(Meeting.id == meeting_id).first()
    if not meeting:
        raise HTTPException(404, "Meeting not found")
    if meeting.audio_file_path and os.path.exists(meeting.audio_file_path):
        os.remove(meeting.audio_file_path)
    db.delete(meeting)
    db.commit()