import time
from collections.abc import Callable

import httpx

from config import (
    GROQ_API_KEY,
    OPENAI_API_KEY,
    TRANSCRIPTION_PROVIDER,
    WHISPER_LANGUAGE,
    WHISPER_MODEL,
    WHISPER_PROMPT,
)

PROVIDERS = {
    "groq": ("https://api.groq.com/openai/v1", GROQ_API_KEY),
    "openai": ("https://api.openai.com/v1", OPENAI_API_KEY),
}
ATTEMPTS = 3
RETRY_STATUS = {429, 500, 502, 503, 504}


class TranscriptionError(Exception):
    pass


class Transcriber:
    def __init__(self, base_url: str, api_key: str):
        self.client = httpx.Client(
            base_url=base_url,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=30,
        )

    def transcribe(
        self, audio_bytes: bytes, on_retry: Callable[[], None] = lambda: None
    ) -> str:
        for attempt in range(1, ATTEMPTS + 1):
            try:
                return self._post(audio_bytes)
            except Exception as e:
                if attempt == ATTEMPTS or not _transient(e):
                    raise TranscriptionError(_describe(e)) from e
                on_retry()
                time.sleep(attempt)

    def _post(self, audio_bytes: bytes) -> str:
        data = {"model": WHISPER_MODEL}
        if WHISPER_PROMPT:
            data["prompt"] = WHISPER_PROMPT
        # Auto-detect guesses per clip and often misfires on short ones.
        if WHISPER_LANGUAGE:
            data["language"] = WHISPER_LANGUAGE
        resp = self.client.post(
            "/audio/transcriptions",
            files={"file": ("audio.wav", audio_bytes, "audio/wav")},
            data=data,
        )
        resp.raise_for_status()
        return resp.json().get("text", "")

    def close(self):
        self.client.close()


def _transient(e: Exception) -> bool:
    if isinstance(e, httpx.HTTPStatusError):
        return e.response.status_code in RETRY_STATUS
    return isinstance(e, httpx.TransportError)


def _describe(e: Exception) -> str:
    # Provider error bodies say what's actually wrong (bad key, file too large).
    if isinstance(e, httpx.HTTPStatusError):
        return f"{e.response.status_code}: {e.response.text[:300]}"
    return str(e)


def get_transcriber() -> Transcriber:
    return Transcriber(*PROVIDERS[TRANSCRIPTION_PROVIDER])
