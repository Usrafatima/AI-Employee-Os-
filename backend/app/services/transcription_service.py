"""Transcribes meeting audio using OpenAI Whisper API."""
from app.services.ai_service import get_client


def transcribe_audio(file_path: str) -> str:
    client = get_client()
    with open(file_path, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
        )
    return transcript.text
