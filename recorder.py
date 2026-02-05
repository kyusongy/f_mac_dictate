import io
import wave
import numpy as np
import sounddevice as sd
from config import SAMPLE_RATE, MIN_DURATION


class Recorder:
    def __init__(self):
        self.frames = []
        self.stream = None
        self.recording = False

    def _callback(self, indata, frames, time, status):
        if self.recording:
            self.frames.append(indata.copy())

    def start(self):
        self.frames = []
        self.recording = True
        self.stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=1,
            dtype=np.int16,
            callback=self._callback,
        )
        self.stream.start()

    def stop(self) -> bytes | None:
        """Stop recording and return WAV bytes, or None if too short."""
        self.recording = False
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None

        if not self.frames:
            return None

        audio = np.concatenate(self.frames, axis=0)
        duration = len(audio) / SAMPLE_RATE

        if duration < MIN_DURATION:
            return None

        # Convert to WAV bytes
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(audio.tobytes())

        return buf.getvalue()
