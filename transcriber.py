from abc import ABC, abstractmethod
import httpx
from config import GROQ_API_KEY, OPENAI_API_KEY, TRANSCRIPTION_PROVIDER


class Transcriber(ABC):
    @abstractmethod
    def transcribe(self, audio_bytes: bytes) -> str:
        pass


class GroqTranscriber(Transcriber):
    def transcribe(self, audio_bytes: bytes) -> str:
        try:
            resp = httpx.post(
                "https://api.groq.com/openai/v1/audio/transcriptions",
                headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
                files={"file": ("audio.wav", audio_bytes, "audio/wav")},
                data={"model": "whisper-large-v3-turbo"},
                timeout=30,
            )
            resp.raise_for_status()
            return resp.json().get("text", "")
        except Exception as e:
            return f"[Transcription failed: {e}]"


class OpenAITranscriber(Transcriber):
    def transcribe(self, audio_bytes: bytes) -> str:
        try:
            resp = httpx.post(
                "https://api.openai.com/v1/audio/transcriptions",
                headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
                files={"file": ("audio.wav", audio_bytes, "audio/wav")},
                data={"model": "whisper-1"},
                timeout=30,
            )
            resp.raise_for_status()
            return resp.json().get("text", "")
        except Exception as e:
            return f"[Transcription failed: {e}]"


def get_transcriber() -> Transcriber:
    if TRANSCRIPTION_PROVIDER == "openai":
        return OpenAITranscriber()
    return GroqTranscriber()
