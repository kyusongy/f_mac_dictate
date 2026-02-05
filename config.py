import os
import sys
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
TRANSCRIPTION_PROVIDER = os.getenv("TRANSCRIPTION_PROVIDER", "groq")
HOTKEY = os.getenv("HOTKEY", "alt_r")
WHISPER_PROMPT = os.getenv("WHISPER_PROMPT", "")
_DEFAULT_MODELS = {"groq": "whisper-large-v3-turbo", "openai": "whisper-1"}
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "")

try:
    MIN_DURATION = float(os.getenv("MIN_DURATION", "0.5"))
except ValueError:
    print("Warning: invalid MIN_DURATION, using 0.5", file=sys.stderr)
    MIN_DURATION = 0.5

try:
    SAMPLE_RATE = int(os.getenv("SAMPLE_RATE", "16000"))
except ValueError:
    print("Warning: invalid SAMPLE_RATE, using 16000", file=sys.stderr)
    SAMPLE_RATE = 16000

if TRANSCRIPTION_PROVIDER not in ("groq", "openai"):
    print(f"Warning: unknown TRANSCRIPTION_PROVIDER '{TRANSCRIPTION_PROVIDER}', using groq", file=sys.stderr)
    TRANSCRIPTION_PROVIDER = "groq"

VALID_HOTKEYS = {
    "alt_r", "alt_l", "alt", "ctrl_r", "ctrl_l", "ctrl",
    "shift_r", "shift_l", "shift", "cmd_r", "cmd_l", "cmd",
}
if HOTKEY not in VALID_HOTKEYS:
    print(f"Warning: unknown HOTKEY '{HOTKEY}', using alt_r", file=sys.stderr)
    HOTKEY = "alt_r"

if not WHISPER_MODEL:
    WHISPER_MODEL = _DEFAULT_MODELS[TRANSCRIPTION_PROVIDER]

if TRANSCRIPTION_PROVIDER == "groq" and not GROQ_API_KEY:
    print("Warning: GROQ_API_KEY is empty", file=sys.stderr)
elif TRANSCRIPTION_PROVIDER == "openai" and not OPENAI_API_KEY:
    print("Warning: OPENAI_API_KEY is empty", file=sys.stderr)
