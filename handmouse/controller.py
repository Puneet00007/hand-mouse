"""Gesture state machine: turns per-frame hand features into mouse actions.

Independent of the camera and of the UI, so it can be unit-tested with a fake mouse.
"""
from __future__ import annotations

from typing import Callable, Optional

from .config import Config

SCROLL_REF_PX = 480        # historic scale: movement measured as if the frame was 480px high
EDGE = 5                   # keep the cursor this many px away from the screen edge (fail-safe corners)


def _lerp(v, a0, a1, b0, b1):
    if a1 == a0:
        return b0
    t = min(max((v - a0) / (a1 - a0), 0.0), 1.0)
    return b0 + t * (b1 - b0)


class GestureController:
    def __init__(self, cfg: Config, mouse, on_event: Optional[Callable[[str], None]] = None):
        self.cfg = cfg
        self.mouse = mouse
        self.on_event = on_event or (lambda kind: None)
        self.paused = False
        self.mode = "no hand"
        self.pinching = False
        self.dragging = False
        self._pinch_start = 0.0
        self._last_right = 0.0
        self._fist_since: Optional[float] = None
        self._fist_latched = False
        self._prev_scroll_y: Optional[float] = None
        self.cur_x, self.cur_y = mouse.position()

    # ------------------------------------------------------------------
    def _emit(self, kind: str) -> None:
        try:
            self.on_event(kind)
        except Exception:
            pass

    def _release_all(self) -> None:
        if self.dragging:
            self.mouse.up()
            self._emit("drag_end")
        self.pinching = self.dragging = False

    def set_paused(self, value: bool) -> None:
        if value != self.paused:
            self.paused = value
            self._release_all()
            self._emit("pause" if value else "resume")

    def toggle_pause(self) -> None:
        self.set_paused(not self.paused)

    def hand_lost(self) -> str:
        """No hand in view: release buttons and hand the real mouse back to the user."""
        self._release_all()
        self._prev_scroll_y = None
        self._fist_since, self._fist_latched = None, False
        self.cur_x, self.cur_y = self.mouse.position()
        self.mode = "paused" if self.paused else "no hand"
        return self.mode

    def shutdown(self) -> None:
        self._release_all()

    # ------------------------------------------------------------------
    def update(self, g: dict, tip: tuple, now: float) -> str:
        """g = gestures.analyze() output, tip = index fingertip (x, y) in 0..1 image coords."""
        cfg, gs, m = self.cfg, self.cfg.gestures, self.mouse

        # ---- fist held = toggle pause (also while paused, so you can resume) ----
        if gs["pause"] and g["fist"] and not self.pinching and not self.dragging:
            if self._fist_since is None:
                self._fist_since = now
            if now - self._fist_since >= cfg.fist_hold and not self._fist_latched:
                self._fist_latched = True
                self.toggle_pause()
        else:
            self._fist_since, self._fist_latched = None, False

        if self.paused:
            self.mode = "paused"
            return self.mode
        if gs["pause"] and g["fist"] and not self.pinching and not self.dragging:
            self.mode = "fist..."
            return self.mode

        # ---------------------------- scroll ----------------------------
        if (gs["scroll"] and g["idx"] and g["mid"] and not g["ring"] and not g["pinky"]
                and g["rpinch"] > 0.5 and not self.pinching and not self.dragging):
            self.mode = "scroll"
            y = tip[1]
            if self._prev_scroll_y is not None:
                dy = (self._prev_scroll_y - y) * SCROLL_REF_PX
                if cfg.scroll_invert:
                    dy = -dy
                if abs(dy) > 1.5:
                    m.scroll(int(dy * cfg.scroll_speed / 5))
            self._prev_scroll_y = y
            return self.mode
        self._prev_scroll_y = None

        # ---------- left button: pinch (click) / long pinch (drag) ----------
        if gs["click"] or gs["drag"]:
            if not self.pinching and g["pinch"] < cfg.pinch_on:
                self.pinching, self._pinch_start = True, now
            elif self.pinching and g["pinch"] > cfg.pinch_off:
                self.pinching = False
                if self.dragging:
                    m.up()
                    self.dragging = False
                    self._emit("drag_end")
                elif gs["click"] and now - self._pinch_start < cfg.drag_hold:
                    m.click()
                    self._emit("click")
                    self.mode = "click"
            if (gs["drag"] and self.pinching and not self.dragging
                    and now - self._pinch_start >= cfg.drag_hold):
                m.down()
                self.dragging = True
                self._emit("drag_start")
        else:
            self.pinching = False

        # ---------------------------- right click ----------------------------
        # middle finger must be extended, otherwise a thumb resting on a curled
        # middle finger while pointing would right-click by accident
        if (gs["right_click"] and not self.pinching and g["rpinch"] < cfg.pinch_on
                and g["mid_reach"] > 1.5 and now - self._last_right > cfg.right_click_cooldown):
            m.right_click()
            self._last_right = now
            self._emit("right_click")
            self.mode = "right click"

        # ---------------------------- move / drag ----------------------------
        # the cursor stays frozen while a pinch starts, so the click lands exactly
        # where you were pointing; it follows the finger again once dragging
        if gs["move"] and ((not self.pinching) or self.dragging) and (g["idx"] or self.dragging):
            sw, sh = m.size()
            mg = cfg.margin_pct / 100.0
            tx = _lerp(tip[0], mg, 1 - mg, 0, sw)
            ty = _lerp(tip[1], mg, 1 - mg, 0, sh)
            s = max(cfg.smoothing, 1.0)
            self.cur_x += (tx - self.cur_x) / s
            self.cur_y += (ty - self.cur_y) / s
            m.move(min(max(self.cur_x, EDGE), sw - EDGE - 1),
                   min(max(self.cur_y, EDGE), sh - EDGE - 1))
            self.mode = "drag" if self.dragging else "move"
        elif self.mode in ("scroll", "paused", "fist..."):
            self.mode = "idle"
        return self.mode
