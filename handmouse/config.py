"""User settings: typed defaults, validation, JSON persistence."""
from __future__ import annotations

import json
import os
import sys
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path

from .theme import ACCENTS, DEFAULT_ACCENT

GESTURE_KEYS = ("move", "click", "drag", "right_click", "scroll", "pause")


def default_gestures() -> dict:
    return {k: True for k in GESTURE_KEYS}


def config_path() -> Path:
    """%APPDATA%\\HandMouse\\config.json on Windows, ~/.config/handmouse elsewhere."""
    override = os.environ.get("HANDMOUSE_CONFIG")
    if override:
        return Path(override)
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home()))
        return base / "HandMouse" / "config.json"
    return Path.home() / ".config" / "handmouse" / "config.json"


# (min, max) limits used to sanitise values loaded from disk
LIMITS = {
    "camera_index": (0, 9),
    "smoothing": (1.0, 20.0),
    "margin_pct": (0.0, 40.0),
    "pinch_on": (0.10, 0.50),
    "pinch_off": (0.15, 0.70),
    "drag_hold": (0.10, 1.50),
    "scroll_speed": (5, 150),
    "right_click_cooldown": (0.2, 2.0),
    "fist_hold": (0.5, 5.0),
    "model_complexity": (0, 1),
}

PRESETS = {
    "Precise":  {"smoothing": 8.0, "margin_pct": 15.0},
    "Balanced": {"smoothing": 5.0, "margin_pct": 18.0},
    "Fast":     {"smoothing": 2.5, "margin_pct": 24.0},
}


@dataclass
class Config:
    # --- camera / tracking ---
    camera_index: int = 0
    hand: str = "Any"                 # Any | Left | Right
    model_complexity: int = 0         # 0 = fast, 1 = accurate
    # --- cursor ---
    smoothing: float = 5.0            # 1 = raw, higher = smoother (and laggier)
    margin_pct: float = 18.0          # dead border of the camera image, in %
    # --- clicks ---
    pinch_on: float = 0.28            # pinch distance / hand size -> "pinched"
    pinch_off: float = 0.38           # release threshold (hysteresis)
    drag_hold: float = 0.30           # seconds a pinch must be held to start a drag
    right_click_cooldown: float = 0.6
    # --- scroll / pause ---
    scroll_speed: float = 40
    scroll_invert: bool = False
    fist_hold: float = 1.5
    # --- gestures on/off ---
    gestures: dict = field(default_factory=default_gestures)
    # --- look & behaviour ---
    accent: str = DEFAULT_ACCENT
    appearance: str = "Dark"          # Dark | Light | System
    sound: bool = True
    show_skeleton: bool = True
    show_zone: bool = True
    show_preview: bool = True
    topmost: bool = False
    auto_start: bool = False

    # ------------------------------------------------------------------
    def sanitize(self) -> "Config":
        for name, (lo, hi) in LIMITS.items():
            v = getattr(self, name)
            try:
                v = type(getattr(Config(), name))(v)
            except (TypeError, ValueError):
                v = getattr(Config(), name)
            setattr(self, name, min(max(v, lo), hi))
        if self.hand not in ("Any", "Left", "Right"):
            self.hand = "Any"
        if self.accent not in ACCENTS:
            self.accent = DEFAULT_ACCENT
        if self.appearance not in ("Dark", "Light", "System"):
            self.appearance = "Dark"
        g = default_gestures()
        if isinstance(self.gestures, dict):
            g.update({k: bool(v) for k, v in self.gestures.items() if k in g})
        self.gestures = g
        # release threshold must stay above the press threshold
        self.pinch_off = max(self.pinch_off, self.pinch_on + 0.04)
        return self

    def apply_preset(self, name: str) -> None:
        for k, v in PRESETS[name].items():
            setattr(self, k, v)

    # ------------------------------------------------------------------
    @classmethod
    def load(cls, path: Path | None = None) -> "Config":
        path = path or config_path()
        cfg = cls()
        try:
            data = json.loads(Path(path).read_text(encoding="utf-8"))
            known = {f.name for f in fields(cls)}
            for k, v in data.items():
                if k in known:
                    setattr(cfg, k, v)
        except (OSError, ValueError):
            pass
        return cfg.sanitize()

    def save(self, path: Path | None = None) -> None:
        path = Path(path or config_path())
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(asdict(self), indent=2), encoding="utf-8")
        except OSError:
            pass
