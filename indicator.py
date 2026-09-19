import time
from collections.abc import Callable

from AppKit import (
    NSAnimationContext,
    NSAppearance,
    NSAppearanceNameDarkAqua,
    NSAttributedString,
    NSBackingStoreBuffered,
    NSButton,
    NSColor,
    NSEvent,
    NSFont,
    NSFontAttributeName,
    NSFontWeightBold,
    NSFontWeightMedium,
    NSFontWeightRegular,
    NSForegroundColorAttributeName,
    NSImage,
    NSImageSymbolConfiguration,
    NSImageView,
    NSLayoutAttributeCenterY,
    NSLayoutConstraint,
    NSPanel,
    NSRunLoop,
    NSRunLoopCommonModes,
    NSScreen,
    NSStackView,
    NSStatusWindowLevel,
    NSTextAlignmentRight,
    NSTextField,
    NSTimer,
    NSUserInterfaceLayoutOrientationHorizontal,
    NSView,
    NSViewHeightSizable,
    NSViewWidthSizable,
    NSVisualEffectBlendingModeBehindWindow,
    NSVisualEffectMaterialHUDWindow,
    NSVisualEffectStateActive,
    NSVisualEffectView,
    NSWindowCollectionBehaviorCanJoinAllSpaces,
    NSWindowCollectionBehaviorFullScreenAuxiliary,
    NSWindowCollectionBehaviorStationary,
    NSWindowStyleMaskBorderless,
    NSWindowStyleMaskNonactivatingPanel,
)
from Foundation import NSMakeRect, NSMouseInRect, NSObject
from PyObjCTools.AppHelper import callLater
from Quartz import (
    CABasicAnimation,
    CAMediaTimingFunction,
    kCAMediaTimingFunctionEaseInEaseOut,
)

from waveform import HEIGHT as WAVE_H
from waveform import WIDTH as WAVE_W
from waveform import WaveformView

PILL_H = 40
PAD = 14
BOTTOM = 100
FPS = 30
CLOCK_W = 34
SPRING = CAMediaTimingFunction.functionWithControlPoints____(0.2, 0.9, 0.25, 1.0)


def _rgb(r: int, g: int, b: int) -> NSColor:
    return NSColor.colorWithSRGBRed_green_blue_alpha_(r / 255, g / 255, b / 255, 1.0)


RED = _rgb(255, 69, 58)
GREEN = _rgb(48, 209, 88)
AMBER = _rgb(255, 179, 64)


def _active_screen() -> NSScreen:
    # mainScreen() is the screen of *our* key window, and a menu bar app has
    # none, so it always resolves to the primary display. The cursor tracks
    # where the user is actually working.
    mouse = NSEvent.mouseLocation()
    for screen in NSScreen.screens():
        if NSMouseInRect(mouse, screen.frame(), False):
            return screen
    return NSScreen.mainScreen()


def _animate(
    changes: Callable[[], None],
    duration: float = 0.3,
    done: Callable[[], None] | None = None,
) -> None:
    def group(ctx) -> None:
        ctx.setDuration_(duration)
        ctx.setTimingFunction_(SPRING)
        changes()

    NSAnimationContext.runAnimationGroup_completionHandler_(group, done)


def _label(size: float, weight: float, alpha: float, mono: bool = False) -> NSTextField:
    make = (
        NSFont.monospacedDigitSystemFontOfSize_weight_
        if mono
        else NSFont.systemFontOfSize_weight_
    )
    label = NSTextField.labelWithString_("")
    label.setFont_(make(size, weight))
    label.setTextColor_(NSColor.colorWithWhite_alpha_(1.0, alpha))
    return label


def _symbol(name: str) -> NSImage:
    config = NSImageSymbolConfiguration.configurationWithPointSize_weight_(
        15, NSFontWeightBold
    )
    image = NSImage.imageWithSystemSymbolName_accessibilityDescription_(name, None)
    return image.imageWithSymbolConfiguration_(config)


class _Action(NSObject):
    """Target/action trampoline into a Python callable."""

    def initWithCallback_(self, callback: Callable[[], None]):
        self = self.init()  # noqa: PLW0642 (ObjC init idiom)
        if self is None:
            return None
        self.callback = callback
        return self

    def fire_(self, _sender) -> None:
        self.callback()


class _Button(NSButton):
    # The panel never becomes key (your text field keeps focus), so without
    # this the first click would be swallowed instead of pressing the button.
    def acceptsFirstMouse_(self, _event) -> bool:
        return True


class Indicator:
    """Floating pill: live waveform while recording, then processing/done/failed."""

    def __init__(self, level: Callable[[], float]):
        self.state = "hidden"
        self.visible = False
        self.gen = 0
        self.started = 0.0
        self.screen = None
        self.timer = None
        self.on_retry = None
        self.ticker = _Action.alloc().initWithCallback_(self._tick)
        self.clicker = _Action.alloc().initWithCallback_(self._retry_clicked)
        self._build(level)

    # --- public states ---

    def recording(self, hands_free: bool) -> None:
        if self.state != "recording":
            self.started = time.monotonic()
            self.wave.reset()
        self._apply("recording", dot=hands_free, wave="live", clock=True)
        if hands_free:
            self._pulse()

    def processing(self, text: str = "") -> None:
        self._apply("processing", wave="wave", text=text)

    def done(self) -> None:
        self._apply("done", icon=("checkmark", GREEN), width=PILL_H)
        self._hide_later(0.7)

    def failed(self, on_retry: Callable[[], None]) -> None:
        self.on_retry = on_retry
        self._apply(
            "failed",
            icon=("exclamationmark.circle.fill", AMBER),
            text="Couldn't transcribe",
            retry=True,
        )
        self._hide_later(10)

    def notice(self, text: str) -> None:
        self._apply("notice", text=text)
        self._hide_later(1.2)

    def hide(self) -> None:
        self.gen += 1
        self.state = "hidden"
        self._stop_timer()
        self.panel.setIgnoresMouseEvents_(True)
        if not self.visible:
            return
        self.visible = False

        def fade() -> None:
            self.panel.animator().setAlphaValue_(0.0)

        def gone() -> None:
            if not self.visible:
                self.panel.orderOut_(None)

        _animate(fade, 0.2, gone)

    # --- construction ---

    def _build(self, level: Callable[[], float]) -> None:
        panel = NSPanel.alloc().initWithContentRect_styleMask_backing_defer_(
            NSMakeRect(0, 0, 120, PILL_H),
            NSWindowStyleMaskBorderless | NSWindowStyleMaskNonactivatingPanel,
            NSBackingStoreBuffered,
            False,
        )
        panel.setLevel_(NSStatusWindowLevel)
        panel.setCollectionBehavior_(
            NSWindowCollectionBehaviorCanJoinAllSpaces
            | NSWindowCollectionBehaviorStationary
            | NSWindowCollectionBehaviorFullScreenAuxiliary
        )
        panel.setOpaque_(False)
        panel.setBackgroundColor_(NSColor.clearColor())
        panel.setHasShadow_(True)
        panel.setIgnoresMouseEvents_(True)
        # Panels hide when their app deactivates, and a menu bar app is never active.
        panel.setHidesOnDeactivate_(False)
        panel.setAppearance_(NSAppearance.appearanceNamed_(NSAppearanceNameDarkAqua))

        blur = NSVisualEffectView.alloc().initWithFrame_(panel.frame())
        blur.setMaterial_(NSVisualEffectMaterialHUDWindow)
        blur.setBlendingMode_(NSVisualEffectBlendingModeBehindWindow)
        blur.setState_(NSVisualEffectStateActive)
        blur.setWantsLayer_(True)
        layer = blur.layer()
        layer.setCornerRadius_(PILL_H / 2)
        layer.setMasksToBounds_(True)
        layer.setBorderWidth_(0.5)
        layer.setBorderColor_(NSColor.colorWithWhite_alpha_(1.0, 0.14).CGColor())
        panel.setContentView_(blur)

        # HUD material alone reads mid-grey over light windows; darken it so
        # the pill stays legible on any background.
        tint = NSView.alloc().initWithFrame_(blur.bounds())
        tint.setAutoresizingMask_(NSViewWidthSizable | NSViewHeightSizable)
        tint.setWantsLayer_(True)
        tint.layer().setBackgroundColor_(
            NSColor.colorWithWhite_alpha_(0.08, 0.6).CGColor()
        )
        blur.addSubview_(tint)

        self.dot = NSView.alloc().init()
        self.dot.setWantsLayer_(True)
        self.dot.layer().setBackgroundColor_(RED.CGColor())
        self.dot.layer().setCornerRadius_(4)
        self.wave = WaveformView.alloc().initWithLevel_(level)
        self.icon = NSImageView.alloc().init()
        self.text = _label(13, NSFontWeightMedium, 1.0)
        self.clock = _label(12, NSFontWeightRegular, 0.6, mono=True)
        self.clock.setAlignment_(NSTextAlignmentRight)
        self.retry = self._retry_button()

        stack = NSStackView.stackViewWithViews_(
            [self.dot, self.wave, self.icon, self.text, self.clock, self.retry]
        )
        stack.setOrientation_(NSUserInterfaceLayoutOrientationHorizontal)
        stack.setAlignment_(NSLayoutAttributeCenterY)
        stack.setSpacing_(10)
        stack.setTranslatesAutoresizingMaskIntoConstraints_(False)
        blur.addSubview_(stack)
        NSLayoutConstraint.activateConstraints_(
            [
                stack.centerXAnchor().constraintEqualToAnchor_(blur.centerXAnchor()),
                stack.centerYAnchor().constraintEqualToAnchor_(blur.centerYAnchor()),
                self.dot.widthAnchor().constraintEqualToConstant_(8),
                self.dot.heightAnchor().constraintEqualToConstant_(8),
                self.wave.widthAnchor().constraintEqualToConstant_(WAVE_W),
                self.wave.heightAnchor().constraintEqualToConstant_(WAVE_H),
                self.icon.widthAnchor().constraintEqualToConstant_(18),
                self.icon.heightAnchor().constraintEqualToConstant_(18),
                self.clock.widthAnchor().constraintEqualToConstant_(CLOCK_W),
                self.retry.widthAnchor().constraintEqualToConstant_(56),
                self.retry.heightAnchor().constraintEqualToConstant_(24),
            ]
        )
        self.panel = panel
        self.stack = stack

    def _retry_button(self) -> NSButton:
        button = _Button.alloc().init()
        button.setTarget_(self.clicker)
        button.setAction_("fire:")
        button.setBordered_(False)
        button.setWantsLayer_(True)
        button.layer().setBackgroundColor_(
            NSColor.colorWithWhite_alpha_(1.0, 0.18).CGColor()
        )
        button.layer().setCornerRadius_(6)
        attrs = {
            NSForegroundColorAttributeName: NSColor.whiteColor(),
            NSFontAttributeName: NSFont.systemFontOfSize_weight_(
                12, NSFontWeightMedium
            ),
        }
        button.setAttributedTitle_(
            NSAttributedString.alloc().initWithString_attributes_("Retry", attrs)
        )
        return button

    # --- internals ---

    def _apply(
        self,
        state: str,
        *,
        dot: bool = False,
        wave: str | None = None,
        icon: tuple[str, NSColor] | None = None,
        text: str = "",
        clock: bool = False,
        retry: bool = False,
        width: float | None = None,
    ) -> None:
        self.gen += 1
        self.state = state
        self.dot.setHidden_(not dot)
        self.wave.setHidden_(wave is None)
        if wave:
            self.wave.mode = wave
            self._start_timer()
        else:
            self._stop_timer()
        self.icon.setHidden_(icon is None)
        if icon:
            name, color = icon
            self.icon.setImage_(_symbol(name))
            self.icon.setContentTintColor_(color)
        self.text.setHidden_(not text)
        self.text.setStringValue_(text)
        self.clock.setHidden_(not clock)
        if clock:
            self._update_clock()
        self.retry.setHidden_(not retry)
        # Only clickable while it has a button; otherwise clicks fall through.
        self.panel.setIgnoresMouseEvents_(not retry)
        # Hidden views detach from the stack on layout; measure after that.
        self.stack.layoutSubtreeIfNeeded()
        self._place(width or self.stack.fittingSize().width + 2 * PAD)

    def _place(self, width: float) -> None:
        if not self.visible:
            self.screen = _active_screen()
        sf = self.screen.frame()
        x = sf.origin.x + (sf.size.width - width) / 2
        target = NSMakeRect(x, sf.origin.y + BOTTOM, width, PILL_H)
        if self.visible:
            _animate(lambda: self.panel.animator().setFrame_display_(target, True))
            return

        self.visible = True
        self.panel.setFrame_display_(
            NSMakeRect(x, sf.origin.y + BOTTOM - 8, width, PILL_H), False
        )
        self.panel.setAlphaValue_(0.0)
        self.panel.orderFrontRegardless()

        def rise() -> None:
            self.panel.animator().setFrame_display_(target, True)
            self.panel.animator().setAlphaValue_(1.0)

        _animate(rise, 0.25)

    def _pulse(self) -> None:
        pulse = CABasicAnimation.animationWithKeyPath_("opacity")
        pulse.setFromValue_(1.0)
        pulse.setToValue_(0.35)
        pulse.setDuration_(0.7)
        pulse.setAutoreverses_(True)
        pulse.setRepeatCount_(float("inf"))
        pulse.setTimingFunction_(
            CAMediaTimingFunction.functionWithName_(kCAMediaTimingFunctionEaseInEaseOut)
        )
        self.dot.layer().addAnimation_forKey_(pulse, "pulse")

    def _start_timer(self) -> None:
        if self.timer is None:
            self.timer = (
                NSTimer.timerWithTimeInterval_target_selector_userInfo_repeats_(
                    1 / FPS, self.ticker, "fire:", None, True
                )
            )
            # Common modes keep it animating while a menu is open.
            NSRunLoop.mainRunLoop().addTimer_forMode_(self.timer, NSRunLoopCommonModes)

    def _stop_timer(self) -> None:
        if self.timer is not None:
            self.timer.invalidate()
            self.timer = None

    def _tick(self) -> None:
        self.wave.step(FPS)
        if not self.clock.isHidden():
            self._update_clock()

    def _update_clock(self) -> None:
        secs = int(time.monotonic() - self.started)
        self.clock.setStringValue_(f"{secs // 60}:{secs % 60:02d}")

    def _hide_later(self, delay: float) -> None:
        callLater(delay, self._hide_if, self.gen)

    def _hide_if(self, gen: int) -> None:
        # A newer state has taken over the pill since this hide was scheduled.
        if gen == self.gen:
            self.hide()

    def _retry_clicked(self) -> None:
        if self.on_retry:
            self.on_retry()
