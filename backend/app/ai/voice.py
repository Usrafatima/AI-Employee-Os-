from __future__ import annotations

import io
import tempfile
from pathlib import Path

from fastapi import HTTPException, status


def _mime_from(filename: str) -> str:
    suffix = Path(filename or "").suffix.lower()
    mime_map = {
        ".wav": "audio/wav",
        ".mp3": "audio/mpeg",
        ".ogg": "audio/ogg",
        ".opus": "audio/ogg",
        ".m4a": "audio/mp4",
        ".aac": "audio/aac",
        ".flac": "audio/flac",
        ".webm": "audio/webm",
    }
    return mime_map.get(suffix, "audio/webm")


def _transcribe_with_gemini(audio_bytes: bytes, filename: str) -> str | None:
    from app.ai.gemini_adapter import GeminiAdapter

    adapter = GeminiAdapter()
    if not adapter.available:
        return None
    return adapter.transcribe_audio(audio_bytes, _mime_from(filename))


def _transcribe_with_whisper(audio_bytes: bytes, filename: str) -> str:
    """Fallback using faster-whisper (needs the package; downloads a model on first use)."""
    try:
        from faster_whisper import WhisperModel  # type: ignore
    except ImportError:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Voice transcription unavailable. Set GEMINI_API_KEY (recommended) or install faster-whisper.",
        )

    suffix = Path(filename or "").suffix or ".webm"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=True) as tmp:
        tmp.write(audio_bytes)
        tmp.flush()
        model = WhisperModel("base", device="cpu", compute_type="int8")
        segments, _info = model.transcribe(tmp.name, beam_size=1)
        parts = [segment.text for segment in segments]
    return " ".join(parts).strip()


def transcribe(audio_bytes: bytes, filename: str = "voice.webm") -> str:
    """Transcribe an audio file into text.

    Uses Gemini (fast, no extra downloads) when an API key is configured, and
    falls back to faster-whisper otherwise.
    """
    if not audio_bytes:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty audio file.")

    # Try Gemini first (reliable, no model download).
    text = _transcribe_with_gemini(audio_bytes, filename)
    if text:
        return text

    # Fallback: faster-whisper.
    try:
        text = _transcribe_with_whisper(audio_bytes, filename)
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not transcribe the audio. Please check the audio file and try again.",
        )

    if not text:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Could not transcribe any speech from the audio.")
    return text