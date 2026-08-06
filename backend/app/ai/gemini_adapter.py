from __future__ import annotations

import json
from typing import Any

from app.core.config import settings


class GeminiAdapter:
    """Provider adapter for Google Gemini.

    Keeps the AI provider behind a single adapter so the rest of the module
    never depends on the SDK directly. Degrades gracefully when the package
    or API key is not available (returns ``None`` instead of crashing).
    """

    def __init__(self) -> None:
        self.api_key = settings.GEMINI_API_KEY
        self.model_name = settings.GEMINI_MODEL
        self._available = False
        try:
            import google.generativeai as genai  # type: ignore

            self._genai = genai
            if self.api_key:
                genai.configure(api_key=self.api_key)
                self._available = True
        except ImportError:
            self._genai = None

    @property
    def available(self) -> bool:
        return self._available

    def generate(self, system_prompt: str, history: list[dict[str, str]], user_message: str) -> str | None:
        """Return the assistant reply text, or ``None`` when the provider is unavailable."""
        if not self._available or self._genai is None:
            return None
        try:
            model = self._genai.GenerativeModel(
                self.model_name,
                system_instruction=system_prompt,
            )
            chat = model.start_chat(history=self._to_chat_history(history))
            response = chat.send_message(user_message)
            return response.text.strip()
        except Exception:
            return None

    def extract_structured(self, system_prompt: str, user_message: str) -> dict[str, Any]:
        """Ask the model for a JSON object (used to fill tool arguments)."""
        if not self._available or self._genai is None:
            return {}
        try:
            model = self._genai.GenerativeModel(self.model_name, system_instruction=system_prompt)
            response = model.generate_content(user_message)
            return self._parse_json(response.text)
        except Exception:
            return {}

    def transcribe_audio(self, audio_bytes: bytes, mime_type: str = "audio/webm") -> str | None:
        """Transcribe an audio clip with Gemini. Returns the spoken text, or ``None`` on failure."""
        if not self._available or self._genai is None:
            return None
        try:
            import base64

            model = self._genai.GenerativeModel(self.model_name)
            response = model.generate_content(
                [
                    {
                        "inline_data": {
                            "mime_type": mime_type,
                            "data": base64.b64encode(audio_bytes).decode("utf-8"),
                        }
                    },
                    "Transcribe the spoken audio. Return only the spoken text with no commentary.",
                ]
            )
            text = response.text.strip()
            return text or None
        except Exception:
            return None

    def _to_chat_history(self, history: list[dict[str, str]]) -> list[dict[str, Any]]:
        # Gemini expects roles "user" and "model"; our stored roles are "user"/"assistant".
        parts: list[dict[str, Any]] = []
        for item in history:
            role = "model" if item.get("role") == "assistant" else "user"
            parts.append({"role": role, "parts": [item.get("content", "")]})
        return parts

    @staticmethod
    def _parse_json(text: str | None) -> dict[str, Any]:
        if not text:
            return {}
        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`")
            if cleaned.startswith("json"):
                cleaned = cleaned[4:]
        try:
            start = cleaned.find("{")
            end = cleaned.rfind("}")
            if start != -1 and end != -1 and end > start:
                return json.loads(cleaned[start : end + 1])
        except (ValueError, TypeError):
            pass
        return {}
