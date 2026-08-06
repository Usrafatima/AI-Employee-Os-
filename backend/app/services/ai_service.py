from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.ai import orchestrator
from app.ai.executive_assistant import (
    build_action_extraction_prompt,
    build_system_prompt,
    format_reply,
)
from app.ai.gemini_adapter import GeminiAdapter
from app.ai.tools import execute_tool, tool_requires_approval
from app.models.ai import AIActivityLog, AIConversation, AIMessage, KnowledgeEntry

_adapter_instance: GeminiAdapter | None = None


class AIAssistantService:
    """Business use cases for the AI Executive Assistant module."""

    # ------------------------------------------------------------------
    # Conversations (context memory)
    # ------------------------------------------------------------------
    @staticmethod
    def create_conversation(db: Session, title: str | None = None) -> AIConversation:
        conversation = AIConversation(title=title or "New conversation")
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        return conversation

    @staticmethod
    def list_conversations(db: Session) -> list[AIConversation]:
        return db.query(AIConversation).order_by(AIConversation.updated_at.desc()).all()

    @staticmethod
    def get_conversation(db: Session, conversation_id: int) -> AIConversation:
        conversation = db.query(AIConversation).filter(AIConversation.id == conversation_id).first()
        if conversation is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")
        return conversation

    @staticmethod
    def list_messages(db: Session, conversation_id: int) -> list[AIMessage]:
        AIAssistantService.get_conversation(db, conversation_id)
        return (
            db.query(AIMessage)
            .filter(AIMessage.conversation_id == conversation_id)
            .order_by(AIMessage.created_at.asc())
            .all()
        )

    # ------------------------------------------------------------------
    # Knowledge base (company knowledge)
    # ------------------------------------------------------------------
    @staticmethod
    def add_knowledge(db: Session, payload: dict[str, Any]) -> KnowledgeEntry:
        entry = KnowledgeEntry(**payload)
        db.add(entry)
        db.commit()
        db.refresh(entry)
        return entry

    @staticmethod
    def list_knowledge(db: Session, q: str | None = None) -> list[KnowledgeEntry]:
        query = db.query(KnowledgeEntry)
        if q:
            query = query.filter(
                or_(
                    KnowledgeEntry.title.ilike(f"%{q}%"),
                    KnowledgeEntry.content.ilike(f"%{q}%"),
                    KnowledgeEntry.category.ilike(f"%{q}%"),
                )
            )
        return query.order_by(KnowledgeEntry.updated_at.desc()).all()

    @staticmethod
    def _search_knowledge(db: Session, text: str, limit: int = 5) -> list[KnowledgeEntry]:
        words = [word for word in text.split() if len(word) > 2][:10]
        if not words:
            return []
        conditions = [
            KnowledgeEntry.title.ilike(f"%{word}%") for word in words
        ] + [
            KnowledgeEntry.content.ilike(f"%{word}%") for word in words
        ]
        return (
            db.query(KnowledgeEntry)
            .filter(or_(*conditions))
            .order_by(KnowledgeEntry.updated_at.desc())
            .limit(limit)
            .all()
        )

    # ------------------------------------------------------------------
    # Audit / activity logging
    # ------------------------------------------------------------------
    @staticmethod
    def log_activity(
        db: Session,
        *,
        kind: str,
        request: str,
        response: str,
        intent: str | None = None,
        status: str = "completed",
    ) -> AIActivityLog:
        activity = AIActivityLog(kind=kind, request=request, response=response, intent=intent, status=status)
        db.add(activity)
        db.commit()
        db.refresh(activity)
        return activity

    @staticmethod
    def list_activities(db: Session, limit: int = 50) -> list[AIActivityLog]:
        return (
            db.query(AIActivityLog)
            .order_by(AIActivityLog.created_at.desc())
            .limit(limit)
            .all()
        )

    # ------------------------------------------------------------------
    # Core assistant flow
    # ------------------------------------------------------------------
    @staticmethod
    def chat(db: Session, message: str, conversation_id: int | None = None) -> dict[str, Any]:
        conversation = AIAssistantService._get_or_create_conversation(db, conversation_id, message)
        history = AIAssistantService._load_history(db, conversation.id)

        intent = orchestrator.classify_intent(message)
        tool_name = orchestrator.detect_tool(message)
        plan = orchestrator.build_plan(message)
        knowledge = AIAssistantService._search_knowledge(db, message)

        kb_context = "\n".join(f"- {entry.title}: {entry.content}" for entry in knowledge)
        if not kb_context:
            kb_context = "No company knowledge matched this request."

        adapter = AIAssistantService._get_adapter()
        system_prompt = build_system_prompt()

        proposed_action: dict[str, Any] | None = None
        live_context = f"\n\n[Company knowledge base]\n{kb_context}\n"

        if tool_name is not None and tool_requires_approval(tool_name):
            # State-changing action: propose it, execute only after confirmation.
            if adapter.available:
                arguments = adapter.extract_structured(build_action_extraction_prompt(tool_name), message)
            else:
                arguments = {}
            proposed_action = {
                "action": tool_name,
                "arguments": arguments,
                "requires_approval": True,
            }
            message_for_model = message + live_context + f"\n[Detected business task to propose: {tool_name}]"
        elif tool_name is not None:
            # Read-only tool: run it now and feed the result into the answer.
            result = execute_tool(db, tool_name, {})
            if result.get("success"):
                live_context += f"\n[Live business data]\n{result.get('result')}\n"
            message_for_model = message + live_context
        else:
            message_for_model = message + live_context

        reply = None
        if adapter.available:
            reply = adapter.generate(system_prompt, history, message_for_model)

        if reply is None:
            reply = AIAssistantService._fallback_reply(message, tool_name, proposed_action)

        reply = format_reply(reply)

        db.add_all(
            [
                AIMessage(conversation_id=conversation.id, role="user", content=message),
                AIMessage(conversation_id=conversation.id, role="assistant", content=reply),
            ]
        )
        db.commit()

        AIAssistantService.log_activity(db, kind="chat", request=message, response=reply, intent=intent)

        return {
            "reply": reply,
            "conversation_id": conversation.id,
            "plan": plan,
            "proposed_action": proposed_action,
            "created_at": datetime.utcnow(),
        }

    @staticmethod
    def confirm_action(db: Session, conversation_id: int, action: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Approval gate: only here are state-changing business tasks executed."""
        AIAssistantService.get_conversation(db, conversation_id)
        result = execute_tool(db, action, arguments)
        status_text = "approved" if result.get("success") else "failed"

        AIAssistantService.log_activity(
            db,
            kind="action",
            request=f"{action}: {arguments}",
            response=result.get("message", ""),
            intent=action,
            status=status_text,
        )

        result_message = result.get("message", "")
        db.add(AIMessage(conversation_id=conversation_id, role="assistant", content=f"[Action result] {result_message}"))
        db.commit()

        return {
            "success": result.get("success", False),
            "tool": action,
            "message": result_message,
            "result": result.get("result"),
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _get_or_create_conversation(db: Session, conversation_id: int | None, message: str) -> AIConversation:
        if conversation_id is not None:
            return AIAssistantService.get_conversation(db, conversation_id)
        title = message.strip()[:80] or "New conversation"
        return AIAssistantService.create_conversation(db, title=title)

    @staticmethod
    def _load_history(db: Session, conversation_id: int, limit: int = 20) -> list[dict[str, str]]:
        messages = (
            db.query(AIMessage)
            .filter(AIMessage.conversation_id == conversation_id)
            .order_by(AIMessage.created_at.desc())
            .limit(limit)
            .all()
        )
        messages.reverse()
        return [{"role": item.role, "content": item.content} for item in messages]

    @staticmethod
    def _fallback_reply(message: str, tool_name: str | None, proposed_action: dict[str, Any] | None) -> str:
        if proposed_action is not None:
            return (
                "Main is samay AI provider key ke bina sirf propose kar sakta hoon. "
                f"Maine aapka request samjha: '{tool_name}'. "
                "Neeche Confirm button dabayein, to main CRM service se yeh task execute karunga. "
                "Full responses ke liye `.env` me GEMINI_API_KEY set karein."
            )
        if tool_name is not None:
            return (
                "Maine request samjhi aur read-only business data bhi le liya hai. "
                "AI provider key set nahi hai (GEMINI_API_KEY), isliye detailed answer ke liye "
                "key add karke dobara poochhein."
            )
        return (
            "Main aapka AI Executive Assistant hoon, lekin abhi Gemini API key set nahi hai. "
            "`.env` me GEMINI_API_KEY daalne ke baad main natural language me jawab de sakta hoon. "
            "Aap company knowledge base add karke mujhe aur samajhdaar bana sakte hain."
        )

    @staticmethod
    def _get_adapter() -> GeminiAdapter:
        global _adapter_instance
        if _adapter_instance is None:
            _adapter_instance = GeminiAdapter()
        return _adapter_instance
