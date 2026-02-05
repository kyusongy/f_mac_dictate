from abc import ABC, abstractmethod
import httpx
from config import GROQ_API_KEY, OPENAI_API_KEY, TRANSCRIPTION_PROVIDER, WHISPER_PROMPT, WHISPER_MODEL


class TranscriptionError(Exception):
    pass


class Transcriber(ABC):
    @abstractmethod
    def transcribe(self, audio_bytes: bytes) -> str:
        pass

    def close(self):
        pass


class GroqTranscriber(Transcriber):
    def __init__(self):
        self.client = httpx.Client(
            base_url="https://api.groq.com/openai/v1",
            headers={"Authorization": f"Bearer {GROQ_API_KEY}"},
            timeout=30,
        )

    def transcribe(self, audio_bytes: bytes) -> str:
        try:
            data = {"model": WHISPER_MODEL}
            if WHISPER_PROMPT:
                data["prompt"] = WHISPER_PROMPT
            resp = self.client.post(
                "/audio/transcriptions",
                files={"file": ("audio.wav", audio_bytes, "audio/wav")},
                data=data,
            )
            resp.raise_for_status()
            return resp.json().get("text", "")
        except Exception as e:
            raise TranscriptionError(str(e)) from e

    def close(self):
        self.client.close()


class OpenAITranscriber(Transcriber):
    def __init__(self):
        self.client = httpx.Client(
            base_url="https://api.openai.com/v1",
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
            timeout=30,
        )

    def transcribe(self, audio_bytes: bytes) -> str:
        try:
            data = {"model": WHISPER_MODEL}
            if WHISPER_PROMPT:
                data["prompt"] = WHISPER_PROMPT
            resp = self.client.post(
                "/audio/transcriptions",
                files={"file": ("audio.wav", audio_bytes, "audio/wav")},
                data=data,
            )
            resp.raise_for_status()
            return resp.json().get("text", "")
        except Exception as e:
            raise TranscriptionError(str(e)) from e

    def close(self):
        self.client.close()


def get_transcriber() -> Transcriber:
    if TRANSCRIPTION_PROVIDER == "openai":
        return OpenAITranscriber()
    return GroqTranscriber()
