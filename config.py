import os
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
TRANSCRIPTION_PROVIDER = os.getenv("TRANSCRIPTION_PROVIDER", "groq")
HOTKEY = os.getenv("HOTKEY", "alt_r")
MIN_DURATION = float(os.getenv("MIN_DURATION", "0.5"))
SAMPLE_RATE = int(os.getenv("SAMPLE_RATE", "16000"))
