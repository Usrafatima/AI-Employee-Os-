"""
Thin wrapper around the OpenAI API used by all Productivity Suite features:
- Document summarization + entity extraction
- Document Q&A (RAG-lite: relevant text is passed as context)
- Meeting summarization + action item / deadline extraction
- Knowledge base semantic search fallback (keyword search is primary; AI is used to rank/answer)

Kept as a single module so the API key / model / error handling is configured once.
"""
import json
from typing import Optional

from openai import OpenAI

from app.core.config import settings

_client: Optional[OpenAI] = None


def get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=settings.OPENAI_API_KEY)
    return _client


def _chat(system_prompt: str, user_prompt: str, json_mode: bool = False) -> str:
    client = get_client()
    kwargs = {}
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
        **kwargs,
    )
    return response.choices[0].message.content or ""


def summarize_document(text: str, document_type: str) -> dict:
    """Returns {summary: str, key_entities: dict}"""
    system = (
        "You are a document intelligence assistant for a business platform. "
        "Summarize the document concisely (3-6 sentences) and extract key entities "
        "(dates, amounts, parties/names, obligations/deadlines) as JSON. "
        f"The document type is: {document_type}. "
        'Respond ONLY as JSON: {"summary": "...", "key_entities": {"dates": [], '
        '"amounts": [], "parties": [], "obligations": []}}'
    )
    truncated = text[:12000]
    raw = _chat(system, truncated, json_mode=True)
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        parsed = {"summary": raw, "key_entities": {}}
    return parsed


def answer_document_question(document_text: str, question: str) -> str:
    system = (
        "You are an AI assistant answering questions strictly using the provided document text. "
        "If the answer isn't in the document, say so clearly. Be concise and direct."
    )
    user = f"DOCUMENT TEXT:\n{document_text[:12000]}\n\nQUESTION: {question}"
    return _chat(system, user)


def summarize_meeting(transcript: str) -> dict:
    """Returns {summary, action_items: [...], deadlines: [...]}"""
    system = (
        "You are a meeting assistant. Given a meeting transcript, produce: "
        "1) a concise bullet-point summary, 2) a list of action items with owner if mentioned, "
        "3) a list of deadlines/dates mentioned. "
        'Respond ONLY as JSON: {"summary": "...", "action_items": ["..."], "deadlines": ["..."]}'
    )
    raw = _chat(system, transcript[:15000], json_mode=True)
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        parsed = {"summary": raw, "action_items": [], "deadlines": []}
    return parsed


def parse_event_from_text(instruction: str, reference_datetime: str) -> dict:
    """
    Powers Calendar Management's voice/text scheduling: turns a natural language
    instruction into a structured event. reference_datetime anchors relative phrases
    like 'Friday at 3pm' or 'tomorrow'.
    Returns {title, start_time (ISO 8601), end_time (ISO 8601 or null), location, attendees}
    """
    system = (
        "You extract calendar events from natural language scheduling instructions. "
        f"The current date/time is {reference_datetime}. Resolve relative dates "
        "(e.g. 'Friday', 'tomorrow', 'next week') against it. "
        'Respond ONLY as JSON: {"title": "...", "start_time": "ISO 8601", '
        '"end_time": "ISO 8601 or null", "location": "... or null", "attendees": "... or null"}'
    )
    raw = _chat(system, instruction, json_mode=True)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"title": instruction[:255], "start_time": reference_datetime, "end_time": None,
                "location": None, "attendees": None}


def answer_knowledge_query(context_snippets: list[str], question: str) -> str:
    system = (
        "You are the company's AI knowledge assistant. Answer the question using only the "
        "provided knowledge base snippets. Cite which snippet number you used. If not found, say so."
    )
    context = "\n\n".join(f"[{i+1}] {s}" for i, s in enumerate(context_snippets))
    user = f"KNOWLEDGE SNIPPETS:\n{context}\n\nQUESTION: {question}"
    return _chat(system, user)
