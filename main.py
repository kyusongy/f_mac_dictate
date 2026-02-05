import threading
import rumps
from AppKit import NSObject
from recorder import Recorder
from transcriber import get_transcriber
from output import paste_text, play_success_sound
from indicator import Indicator
from hotkey import HotkeyListener


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

        audio = self.recorder.stop()

        if audio is None:
            self.title = "○"
            if self.indicator:
                self.indicator.hide()
            self.processing = False
            return

        def transcribe_and_paste():
            text = self.transcriber.transcribe(audio)
            run_on_main("finish", text)

        threading.Thread(target=transcribe_and_paste, daemon=True).start()

    def _finish(self, text: str):
        self.title = "○"
        if self.indicator:
            self.indicator.hide()
        text = text.strip() if text else ""
        if text:
            paste_text(text)
            if not text.startswith("[Transcription failed"):
                play_success_sound()
        self.processing = False

    @rumps.clicked("Quit")
    def quit_app(self, _):
        if self.hotkey_listener:
            self.hotkey_listener.stop()
        rumps.quit_application()


def main():
    app = DictateApp()
    app.indicator = Indicator()
    app.hotkey_listener = HotkeyListener(app._on_key_press, app._on_key_release)
    app.hotkey_listener.start()
    app.run()


if __name__ == "__main__":
    main()
