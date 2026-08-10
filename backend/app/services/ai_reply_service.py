from __future__ import annotations

from app.ai.gemini_adapter import GeminiAdapter

_adapter = GeminiAdapter()


def generate_ai_reply(customer_message: str, customer_name: str) -> str:
    """Generate a draft reply to a customer message.

    Uses the shared GeminiAdapter (same provider as the AI Executive
    Assistant module) when an API key is configured; otherwise falls back to
    a simple template so the approval workflow is fully testable without a
    live key.
    """
    if getattr(_adapter, "_available", False):
        prompt = (
            f"You are a customer support assistant. A customer named {customer_name} sent this "
            f"message: \"{customer_message}\". Write a short, professional reply (3-4 sentences)."
        )
        try:
            reply = _adapter._genai.GenerativeModel(_adapter.model_name).generate_content(prompt).text
            if reply:
                return reply.strip()
        except Exception:
            pass  # fall through to template

    return (
        f"Hi {customer_name},\n\n"
        f"Thanks for reaching out. Regarding your message: \"{customer_message}\"\n\n"
        "Our team has reviewed this and will follow up shortly with the details you need. "
        "In the meantime, let us know if there's anything else we can help with.\n\n"
        "Best regards,\nSupport Team"
    )
