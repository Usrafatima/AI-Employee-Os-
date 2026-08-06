from __future__ import annotations

from .tools import list_tools

# Intent classification keywords (English + common Hinglish terms used by the team).
_SUMMARY_KEYWORDS = (
    "summary", "summar", "overview", "report", "status", "dashboard",
    "chal raha", "kya hal", "update", "analytics",
)
_BUSINESS_KEYWORDS = (
    "add", "create", "new", "ban", "banavo", "karo", "insert", "register",
    "make a", "schedule",
)
_PRIORITY_KEYWORDS = (
    "priority", "today", "aaj", "urgent", "important", "morning", "daily",
    "kitne kaam", "what's on",
)
_KNOWLEDGE_KEYWORDS = (
    "knowledge", "kb", "company info", "policy", "procedure", "guideline",
    "document", "baare me", "about the company",
)


def classify_intent(message: str) -> str:
    """Classify the user's message into a coarse intent bucket."""
    text = message.lower()
    if any(k in text for k in _BUSINESS_KEYWORDS) and any(w in text for w in ("customer", "lead")):
        return "business_action"
    if any(k in text for k in _SUMMARY_KEYWORDS):
        return "summary"
    if any(k in text for k in _PRIORITY_KEYWORDS):
        return "priority"
    if any(k in text for k in _KNOWLEDGE_KEYWORDS):
        return "knowledge"
    return "general"


def detect_tool(message: str) -> str | None:
    """Detect a supported business tool from the message, if any."""
    text = message.lower()
    wants_create = any(k in text for k in _BUSINESS_KEYWORDS)
    if wants_create and "lead" in text:
        return "create_lead"
    if wants_create and "customer" in text:
        return "create_customer"
    if any(k in text for k in _SUMMARY_KEYWORDS):
        return "crm_summary"
    return None


def build_plan(message: str) -> list[str]:
    """Return a short ordered step list (multi-step reasoning), shown to the user."""
    tool = detect_tool(message)
    steps: list[str] = []
    if tool is not None:
        steps.append("Request understood as a business action")
        if list_tools().get(tool, {}).get("requires_approval"):
            steps.append("Confirm the proposed action with the user")
        steps.append("Execute via the existing business service")
        steps.append("Report the result")
    else:
        steps.append("Understand the request")
        steps.append("Gather relevant context (knowledge base / history)")
        steps.append("Compose a helpful answer")
    return steps
