import sys
import threading

import rumps
from PyObjCTools.AppHelper import callAfter, callLater

from config import HOTKEY
from hotkey import HotkeyListener
from indicator import Indicator
from output import paste_text, play_success_sound
from recorder import EmptyRecording, Recorder
from transcriber import TranscriptionError, get_transcriber


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
        self.indicator = None
        self.hotkey_listener = None
        self.processing = False
        self.failed_audio = None

    # Hotkey callbacks fire on the listener thread; hop to main for UI work.
    def _on_key_press(self):
        callAfter(self._start_recording)

    def _on_key_release(self):
        callAfter(self._stop_recording)

    def _start_recording(self):
        if self.processing:
            return
        self.title = "●"
        if self.indicator:
            self.indicator.set_text("Recording")
            self.indicator.show()
        self.recorder.start()

    def _stop_recording(self):
        # Release can arrive for a press that was ignored mid-processing;
        # without this guard the previous clip's frames get re-transcribed.
        if self.processing or not self.recorder.recording:
            return
        self.processing = True
        if self.indicator:
            self.indicator.set_text("Processing")
        threading.Thread(target=self._record_and_transcribe, daemon=True).start()

    def _retry(self, _):
        if self.processing or self.failed_audio is None:
            return
        self.processing = True
        if self.indicator:
            self.indicator.set_text("Retrying")
            self.indicator.show()
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
            text = self.transcriber.transcribe(audio)
        except TranscriptionError as e:
            callAfter(self._fail, audio, str(e))
            return
        callAfter(self._finish, text, audio)

    def _finish(self, text: str, audio: bytes):
        # A newer successful clip must not discard a still-unsent failed one.
        if audio is self.failed_audio:
            self.failed_audio = None
            self.retry_item.set_callback(None)
        self.title = "○"
        if self.indicator:
            self.indicator.hide()
        text = text.strip() if text else ""
        if text:
            paste_text(text)
            play_success_sound()
        self.processing = False

    def _skip(self, reason: str):
        self.title = "○"
        self.processing = False
        if self.indicator:
            self.indicator.set_text(reason, color="yellow")
            callLater(1.5, self._hide_indicator)

    def _fail(self, audio: bytes, message: str):
        print(f"Transcription failed: {message}", file=sys.stderr)
        self.failed_audio = audio
        self.retry_item.set_callback(self._retry)
        self.title = "○"
        self.processing = False
        if self.indicator:
            # Full error goes to stderr; the pill only fits a word or two.
            self.indicator.set_text("Failed", color="yellow")
            self.indicator.show()
            callLater(2.0, self._hide_indicator)

    def _hide_indicator(self):
        if self.indicator:
            self.indicator.hide()

    def _quit(self, _):
        if self.hotkey_listener:
            self.hotkey_listener.stop()
        self.transcriber.close()
        rumps.quit_application()


def main():
    app = DictateApp()
    app.indicator = Indicator()
    app.hotkey_listener = HotkeyListener(app._on_key_press, app._on_key_release)
    app.hotkey_listener.start()
    app.run()


if __name__ == "__main__":
    main()
