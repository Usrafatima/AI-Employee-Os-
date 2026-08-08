from app.database.session import Base
from app.models.ai import AIActivityLog, AIConversation, AIMessage, KnowledgeEntry
from app.models.crm import ActivityLog, CRMUpdate, Conversation, Customer, Lead

__all__ = [
    "Base",
    "Customer",
    "Lead",
    "Conversation",
    "ActivityLog",
    "CRMUpdate",
    "AIConversation",
    "AIMessage",
    "KnowledgeEntry",
    "AIActivityLog",
]
