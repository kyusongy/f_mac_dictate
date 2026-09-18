import io
import time
import wave

import numpy as np
import sounddevice as sd

from config import MIN_DURATION, SAMPLE_RATE

# Key release usually lands before the last syllable finishes.
TAIL_SECONDS = 0.25
# ~-40 dBFS. Below this it's room noise, and Whisper hallucinates
# ("Thank you.", or echoes the prompt) when fed near-silence.
SILENCE_PEAK = 300


class EmptyRecording(Exception):
    pass


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

    def stop(self) -> bytes:
        """Stop recording and return WAV bytes. Raises EmptyRecording if nothing usable."""
        time.sleep(TAIL_SECONDS)
        self.recording = False
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None

        if not self.frames:
            raise EmptyRecording("Too short")

        audio = np.concatenate(self.frames, axis=0)
        if len(audio) / SAMPLE_RATE < MIN_DURATION + TAIL_SECONDS:
            raise EmptyRecording("Too short")
        if np.abs(audio.astype(np.int32)).max() < SILENCE_PEAK:
            raise EmptyRecording("No speech")

        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(audio.tobytes())

        return buf.getvalue()
