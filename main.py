import threading
import rumps
from AppKit import NSObject
from recorder import Recorder, RecordingTooShort
from transcriber import get_transcriber, TranscriptionError
from output import paste_text, play_success_sound
from indicator import Indicator
from hotkey import HotkeyListener
from config import HOTKEY


class Delegate(NSObject):
    """Bridge to run callbacks on main thread."""

    app = None
    pending_action = None
    pending_text = None

    def performAction_(self, _):
        if self.pending_action == "start":
            self.app._start_recording()
        elif self.pending_action == "stop":
            self.app._stop_recording()
        elif self.pending_action == "finish":
            self.app._finish(self.pending_text)
        elif self.pending_action == "error":
            self.app._show_error(self.pending_text)
        elif self.pending_action == "hide":
            self.app._hide_indicator()


delegate = Delegate.alloc().init()


def run_on_main(action, text=None):
    delegate.pending_action = action
    delegate.pending_text = text
    delegate.performSelectorOnMainThread_withObject_waitUntilDone_(
        "performAction:", None, False
    )


class DictateApp(rumps.App):
    def __init__(self):
        super().__init__("Dictate", "○", quit_button=None)
        hotkey_item = rumps.MenuItem(f"Hotkey: {HOTKEY}")
        hotkey_item.set_callback(None)
        self.menu = [hotkey_item, None, rumps.MenuItem("Quit", callback=self._quit)]
        self.recorder = Recorder()
        self.transcriber = get_transcriber()
        self.indicator = None
        self.hotkey_listener = None
        self.processing = False
        delegate.app = self

    def _on_key_press(self):
        if self.processing:
            return
        run_on_main("start")

    def _on_key_release(self):
        if self.processing:
            return
        run_on_main("stop")

    def _start_recording(self):
        self.title = "●"
        if self.indicator:
            self.indicator.set_text("Recording")
            self.indicator.show()
        self.recorder.start()

    def _stop_recording(self):
        self.processing = True
        if self.indicator:
            self.indicator.set_text("Processing")

        try:
            audio = self.recorder.stop()
        except RecordingTooShort:
            self.title = "○"
            self.processing = False
            if self.indicator:
                self.indicator.set_text("Too short", color="yellow")
                threading.Timer(1.5, lambda: run_on_main("hide")).start()
            return

        def transcribe_and_paste():
            try:
                text = self.transcriber.transcribe(audio)
                run_on_main("finish", text)
            except TranscriptionError as e:
                run_on_main("error", str(e))

        threading.Thread(target=transcribe_and_paste, daemon=True).start()

    def _finish(self, text: str):
        self.title = "○"
        if self.indicator:
            self.indicator.hide()
        text = text.strip() if text else ""
        if text:
            paste_text(text)
            play_success_sound()
        self.processing = False

    def _show_error(self, message: str):
        self.title = "○"
        self.processing = False
        if self.indicator:
            self.indicator.set_text(message, color="yellow")
            self.indicator.show()
            threading.Timer(2.0, lambda: run_on_main("hide")).start()

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
