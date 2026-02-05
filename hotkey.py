from pynput import keyboard
from config import HOTKEY

# Map config strings to pynput keys
KEY_MAP = {
    "alt_r": keyboard.Key.alt_r,
    "alt_l": keyboard.Key.alt_l,
    "alt": keyboard.Key.alt,
    "ctrl_r": keyboard.Key.ctrl_r,
    "ctrl_l": keyboard.Key.ctrl_l,
    "ctrl": keyboard.Key.ctrl,
    "shift_r": keyboard.Key.shift_r,
    "shift_l": keyboard.Key.shift_l,
    "shift": keyboard.Key.shift,
    "cmd_r": keyboard.Key.cmd_r,
    "cmd_l": keyboard.Key.cmd_l,
    "cmd": keyboard.Key.cmd,
}


class HotkeyListener:
    def __init__(self, on_press, on_release):
        self.on_press_callback = on_press
        self.on_release_callback = on_release
        self.target_key = KEY_MAP.get(HOTKEY, keyboard.Key.alt_r)
        self.pressed = False
        self.listener = None

    def _on_press(self, key):
        if key == self.target_key and not self.pressed:
            self.pressed = True
            self.on_press_callback()

    def _on_release(self, key):
        if key == self.target_key and self.pressed:
            self.pressed = False
            self.on_release_callback()

    def start(self):
        self.listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release,
        )
        self.listener.start()

    def stop(self):
        if self.listener:
            self.listener.stop()
