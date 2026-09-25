import sys
import threading
import time

import rumps
from PyObjCTools.AppHelper import callAfter

from cleanup import Cleaner
from config import HOTKEY, TRANSCRIPTION_PROVIDER
from hotkey import HotkeyListener
from indicator import Indicator
from output import paste_text, play_success_sound
from recorder import EmptyRecording, Recorder
from transcriber import TranscriptionError, get_transcriber

# Releasing sooner than this is a tap: recording continues until the next tap.
# Longer is push-to-talk: release stops.
TAP_SECONDS = 0.3


class DictateApp(rumps.App):
    def __init__(self):
        super().__init__("Dictate", "○", quit_button=None)
        hotkey_item = rumps.MenuItem(f"Hotkey: {HOTKEY}")
        hotkey_item.set_callback(None)
        # Enabled only while a failed recording is held for retry.
        self.retry_item = rumps.MenuItem("Retry last recording")
        self.retry_item.set_callback(None)
        self.menu = [
            hotkey_item,
            self.retry_item,
            None,
            rumps.MenuItem("Quit", callback=self._quit),
        ]
        self.recorder = Recorder()
        self.transcriber = get_transcriber()
        self.cleaner = Cleaner(
            self.transcriber.client if TRANSCRIPTION_PROVIDER == "groq" else None
        )
        self.indicator = Indicator(lambda: self.recorder.level)
        self.hotkey_listener = None
        self.processing = False
        self.failed_audio = None
        self.mode = "idle"  # idle | holding | latched
        self.pressed_at = 0.0

    # Hotkey callbacks fire on the listener thread; hop to main for UI work.
    def _on_key_press(self):
        callAfter(self._key_down)

    def _on_key_release(self):
        callAfter(self._key_up)

    def _on_chord(self):
        callAfter(self._chord)

    def _key_down(self):
        if self.mode == "latched":
            self.mode = "idle"
            self._stop_recording()
        elif self.mode == "idle" and not self.processing:
            self.mode = "holding"
            self.pressed_at = time.monotonic()
            self._start_recording()

    def _key_up(self):
        if self.mode != "holding":
            return
        if time.monotonic() - self.pressed_at < TAP_SECONDS:
            self.mode = "latched"
            self.indicator.recording(hands_free=True)
        else:
            self.mode = "idle"
            self._stop_recording()

    def _chord(self):
        if self.mode == "holding":
            self.mode = "idle"
            self.recorder.cancel()
            self.title = "○"
            self.indicator.hide()

    def _start_recording(self):
        self.title = "●"
        self.indicator.recording(hands_free=False)
        self.recorder.start()

    def _stop_recording(self):
        self.processing = True
        self.indicator.processing()
        threading.Thread(target=self._record_and_transcribe, daemon=True).start()

    def _retry(self, _):
        if self.processing or self.mode != "idle" or self.failed_audio is None:
            return
        self.processing = True
        self.indicator.processing()
        threading.Thread(
            target=self._transcribe, args=(self.failed_audio,), daemon=True
        ).start()

    def _record_and_transcribe(self):
        try:
            audio = self.recorder.stop()
        except EmptyRecording as e:
            callAfter(self._skip, str(e))
            return
        self._transcribe(audio)

    def _transcribe(self, audio: bytes):
        try:
            text = self.transcriber.transcribe(
                audio, on_retry=lambda: callAfter(self.indicator.processing, "Retrying")
            )
        except TranscriptionError as e:
            callAfter(self._fail, audio, str(e))
            return
        callAfter(self._finish, self.cleaner.fix(text), audio)

    def _finish(self, text: str, audio: bytes):
        # A newer successful clip must not discard a still-unsent failed one.
        if audio is self.failed_audio:
            self.failed_audio = None
            self.retry_item.set_callback(None)
        self.title = "○"
        text = text.strip() if text else ""
        if text:
            paste_text(text)
            play_success_sound()
            self.indicator.done()
        else:
            self.indicator.hide()
        self.processing = False

    def _skip(self, reason: str):
        self.title = "○"
        self.processing = False
        self.indicator.notice(reason)

    def _fail(self, audio: bytes, message: str):
        print(f"Transcription failed: {message}", file=sys.stderr)
        self.failed_audio = audio
        self.retry_item.set_callback(self._retry)
        self.title = "○"
        self.processing = False
        # Full error goes to stderr; the pill offers a one-click retry.
        self.indicator.failed(on_retry=lambda: self._retry(None))

    def _quit(self, _):
        if self.hotkey_listener:
            self.hotkey_listener.stop()
        self.cleaner.close()
        self.transcriber.close()
        rumps.quit_application()


def main():
    app = DictateApp()
    app.hotkey_listener = HotkeyListener(
        app._on_key_press, app._on_key_release, app._on_chord
    )
    app.hotkey_listener.start()
    app.run()


if __name__ == "__main__":
    main()
