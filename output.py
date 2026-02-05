import time
from AppKit import NSPasteboard, NSStringPboardType, NSSound
from Quartz import (
    CGEventCreateKeyboardEvent,
    CGEventPost,
    kCGHIDEventTap,
    kCGEventFlagMaskCommand,
    CGEventSetFlags,
)


def paste_text(text: str):
    """Copy text to clipboard and simulate Cmd+V."""
    # Write to clipboard
    pb = NSPasteboard.generalPasteboard()
    pb.clearContents()
    pb.setString_forType_(text, NSStringPboardType)

    # Small delay for clipboard to settle
    time.sleep(0.05)

    # Simulate Cmd+V (key code 9 = 'v')
    key_down = CGEventCreateKeyboardEvent(None, 9, True)
    key_up = CGEventCreateKeyboardEvent(None, 9, False)
    CGEventSetFlags(key_down, kCGEventFlagMaskCommand)
    CGEventSetFlags(key_up, kCGEventFlagMaskCommand)
    CGEventPost(kCGHIDEventTap, key_down)
    CGEventPost(kCGHIDEventTap, key_up)


def play_success_sound():
    """Play system pop sound."""
    sound = NSSound.soundNamed_("Pop")
    if sound:
        sound.play()
