import math
from collections.abc import Callable

import objc
from AppKit import NSBezierPath, NSColor, NSView
from Foundation import NSMakeRect

BARS = 16
BAR_W = 3.0
GAP = 2.0
WIDTH = BARS * BAR_W + (BARS - 1) * GAP
HEIGHT = 28.0
MIN_H = 4.0
MAX_H = 26.0
# History scrolls one bar every other frame, so about a second of speech is on screen.
SHIFT_EVERY = 2


class WaveformView(NSView):
    """Scrolling mic-level bars ("live") or a travelling wave ("wave") while busy."""

    def initWithLevel_(self, level: Callable[[], float]):
        self = self.initWithFrame_(NSMakeRect(0, 0, WIDTH, HEIGHT))  # noqa: PLW0642 (ObjC init idiom)
        if self is None:
            return None
        self.level = level
        self.mode = "live"
        self.reset()
        return self

    @objc.python_method
    def reset(self) -> None:
        self.history = [0.0] * BARS
        self.heights = [MIN_H] * BARS
        self.ticks = 0

    @objc.python_method
    def step(self, fps: int) -> None:
        self.ticks += 1
        if self.mode == "live":
            if self.ticks % SHIFT_EVERY == 0:
                self.history = self.history[1:] + [self.level()]
            targets = [MIN_H + v * (MAX_H - MIN_H) for v in self.history]
        else:
            t = self.ticks / fps
            targets = [
                MIN_H + 7 * (0.5 + 0.5 * math.sin(t * 9 - i * 0.6)) for i in range(BARS)
            ]
        # Easing toward targets makes ~15 Hz level updates read as smooth motion.
        self.heights = [h + (g - h) * 0.45 for h, g in zip(self.heights, targets)]
        self.setNeedsDisplay_(True)

    def drawRect_(self, _rect) -> None:
        for i, h in enumerate(self.heights):
            alpha = 0.45 + 0.55 * min(1.0, (h - MIN_H) / (MAX_H - MIN_H))
            NSColor.colorWithWhite_alpha_(1.0, alpha).setFill()
            rect = NSMakeRect(i * (BAR_W + GAP), (HEIGHT - h) / 2, BAR_W, h)
            NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(
                rect, BAR_W / 2, BAR_W / 2
            ).fill()
