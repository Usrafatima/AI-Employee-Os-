from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.ai.voice import transcribe
from app.database.session import get_db
from app.schemas.ai import (
    ActionConfirmRequest,
    ActionConfirmResponse,
    ActivityLogResponse,
    ChatRequest,
    ChatResponse,
    ConversationCreate,
    ConversationResponse,
    KnowledgeCreate,
    KnowledgeResponse,
    MessageResponse,
)
from app.services.ai_service import AIAssistantService

router = APIRouter()


@router.get("/")
def get_ai_status():
    return {"module": "AI Executive Assistant", "status": "active"}


@router.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest, db: Session = Depends(get_db)):
    """Natural-language chat with context memory and knowledge-base grounding."""
    return AIAssistantService.chat(db, payload.message, payload.conversation_id)


@router.post("/conversations", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
def create_conversation(payload: ConversationCreate, db: Session = Depends(get_db)):
    return AIAssistantService.create_conversation(db, title=payload.title)


@router.get("/conversations", response_model=list[ConversationResponse])
def list_conversations(db: Session = Depends(get_db)):
    return AIAssistantService.list_conversations(db)


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
def get_conversation(conversation_id: int, db: Session = Depends(get_db)):
    return AIAssistantService.get_conversation(db, conversation_id)


@router.get("/conversations/{conversation_id}/messages", response_model=list[MessageResponse])
def list_messages(conversation_id: int, db: Session = Depends(get_db)):
    return AIAssistantService.list_messages(db, conversation_id)


@router.post("/knowledge", response_model=KnowledgeResponse, status_code=status.HTTP_201_CREATED)
def add_knowledge(payload: KnowledgeCreate, db: Session = Depends(get_db)):
    """Add an entry to the company knowledge base."""
    return AIAssistantService.add_knowledge(db, payload.model_dump())


@router.get("/knowledge", response_model=list[KnowledgeResponse])
def list_knowledge(q: Optional[str] = Query(default=None), db: Session = Depends(get_db)):
    return AIAssistantService.list_knowledge(db, q=q)


@router.get("/activities", response_model=list[ActivityLogResponse])
def list_activities(limit: int = Query(default=50, ge=1, le=200), db: Session = Depends(get_db)):
    """Audit log of assistant requests and actions."""
    return AIAssistantService.list_activities(db, limit=limit)


@router.post("/actions/confirm", response_model=ActionConfirmResponse)
def confirm_action(payload: ActionConfirmRequest, db: Session = Depends(get_db)):
    """Approval gate — executes a proposed business task after user confirmation."""
    return AIAssistantService.confirm_action(db, payload.conversation_id, payload.action, payload.arguments)


@router.post("/voice", response_model=ChatResponse)
async def voice_chat(
    audio: UploadFile = File(..., description="Audio file to transcribe"),
    conversation_id: Optional[int] = Form(default=None),
    db: Session = Depends(get_db),
):
    """Voice command: transcribe the audio and run it through the assistant."""
    content = await audio.read()
    if not content:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty audio file.")
    text = transcribe(content, audio.filename or "voice.webm")
    return AIAssistantService.chat(db, text, conversation_id)
