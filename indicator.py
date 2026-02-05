from AppKit import (
    NSWindow,
    NSWindowStyleMaskBorderless,
    NSColor,
    NSTextField,
    NSFont,
    NSScreen,
    NSFloatingWindowLevel,
    NSWindowCollectionBehaviorCanJoinAllSpaces,
    NSWindowCollectionBehaviorStationary,
    NSVisualEffectView,
    NSVisualEffectMaterialHUDWindow,
    NSVisualEffectBlendingModeBehindWindow,
    NSFontWeightMedium,
)
from Foundation import NSMakeRect

DOT_COLORS = {
    "red": NSColor.redColor,
    "orange": NSColor.orangeColor,
    "yellow": NSColor.yellowColor,
}


class Indicator:
    def __init__(self):
        self.window = None
        self.label = None
        self.dot = None
        self._setup()

    def _setup(self):
        width, height = 130, 32
        corner_radius = 16

        # Create window
        frame = NSMakeRect(0, 0, width, height)
        self.window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            frame,
            NSWindowStyleMaskBorderless,
            2,  # NSBackingStoreBuffered
            False,
        )
        self.window.setLevel_(NSFloatingWindowLevel)
        self.window.setCollectionBehavior_(
            NSWindowCollectionBehaviorCanJoinAllSpaces
            | NSWindowCollectionBehaviorStationary
        )
        self.window.setOpaque_(False)
        self.window.setBackgroundColor_(NSColor.clearColor())
        self.window.setHasShadow_(True)
        self.window.setIgnoresMouseEvents_(True)

        # Vibrancy blur effect
        blur = NSVisualEffectView.alloc().initWithFrame_(frame)
        blur.setMaterial_(NSVisualEffectMaterialHUDWindow)
        blur.setBlendingMode_(NSVisualEffectBlendingModeBehindWindow)
        blur.setState_(1)  # Active
        blur.setWantsLayer_(True)
        blur.layer().setCornerRadius_(corner_radius)
        blur.layer().setMasksToBounds_(True)

        # Dot indicator
        self.dot = NSTextField.alloc().initWithFrame_(NSMakeRect(14, 9, 14, 14))
        self.dot.setStringValue_("●")
        self.dot.setBezeled_(False)
        self.dot.setDrawsBackground_(False)
        self.dot.setEditable_(False)
        self.dot.setSelectable_(False)
        self.dot.setTextColor_(NSColor.redColor())
        self.dot.setFont_(NSFont.systemFontOfSize_(12))

        # Label
        self.label = NSTextField.alloc().initWithFrame_(NSMakeRect(30, 7, 90, 18))
        self.label.setStringValue_("Recording")
        self.label.setBezeled_(False)
        self.label.setDrawsBackground_(False)
        self.label.setEditable_(False)
        self.label.setSelectable_(False)
        self.label.setTextColor_(NSColor.whiteColor())
        self.label.setFont_(
            NSFont.systemFontOfSize_weight_(13, NSFontWeightMedium)
        )

        blur.addSubview_(self.dot)
        blur.addSubview_(self.label)
        self.window.contentView().addSubview_(blur)
        self._center()

    def _center(self):
        screen = NSScreen.mainScreen()
        if screen:
            sf = screen.frame()
            wf = self.window.frame()
            x = (sf.size.width - wf.size.width) / 2
            y = 100
            self.window.setFrameOrigin_((x, y))

    def show(self):
        self._center()
        self.window.orderFront_(None)

    def hide(self):
        self.window.orderOut_(None)

    def set_text(self, text: str, color: str | None = None):
        self.label.setStringValue_(text)
        if color and color in DOT_COLORS:
            self.dot.setTextColor_(DOT_COLORS[color]())
        elif "Recording" in text:
            self.dot.setTextColor_(NSColor.redColor())
        else:
            self.dot.setTextColor_(NSColor.orangeColor())
