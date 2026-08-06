from __future__ import annotations

from .tools import list_tools


def build_system_prompt() -> str:
    """System prompt that defines the Executive Assistant persona and rules."""
    tools = list_tools()
    tool_lines = "\n".join(
        f"- {name}: {spec['description']}{' (requires approval)' if spec['requires_approval'] else ' (read-only)'}"
        for name, spec in tools.items()
    )
    return (
        "You are the AI Executive Assistant inside AI Employee OS. You help busy "
        "executives with daily priorities, cross-module summaries, and follow-up "
        "coordination.\n\n"
        "Rules:\n"
        "- Answer in clear, concise, friendly language.\n"
        "- Greetings and small talk (like 'hello', 'hi', 'how are you') get a short, warm "
        "reply. Do NOT pull business data or provide a summary unless the user explicitly "
        "asks for it.\n"
        "- Only use real business data when it is present in the CURRENT message's context. "
        "Ignore older conversation summaries unless the user asks again for the latest data.\n"
        "- Use the company knowledge base context provided to you; do not invent facts.\n"
        "- You can propose business tasks, but state-changing actions are only executed "
        "after the user confirms them.\n"
        "- If the user asks for a summary, give a short overview of the relevant data.\n\n"
        "Business tasks you can propose/execute:\n"
        f"{tool_lines}\n"
    )


def format_reply(reply: str) -> str:
    """Normalize a provider reply before persisting it."""
    text = reply.strip()
    if not text:
        return "I could not produce an answer right now. Please try again."
    return text


def build_action_extraction_prompt(tool_name: str) -> str:
    """Prompt used to extract JSON arguments for a detected business task."""
    return (
        "Extract the arguments for the business task '" + tool_name + "' from the user's "
        "message as a JSON object with only the fields needed. Use empty strings for "
        "missing values. Return JSON only."
    )
