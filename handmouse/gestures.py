"""Pure gesture analysis: 21 MediaPipe hand landmarks -> scale-independent features.

Nothing here imports MediaPipe/OpenCV, so it is trivial to unit-test.
"""
from __future__ import annotations

import math

# MediaPipe hand landmark ids
WRIST, THUMB_TIP = 0, 4
IDX_PIP, IDX_TIP = 6, 8
MID_MCP, MID_PIP, MID_TIP = 9, 10, 12
RING_PIP, RING_TIP = 14, 16
PINKY_PIP, PINKY_TIP = 18, 20


def _dist(a, b) -> float:
    return math.hypot(a.x - b.x, a.y - b.y)


def analyze(lm) -> dict:
    """Return gesture features for one hand.

    idx / mid / ring / pinky   finger extended (tip above its middle joint)
    pinch                      thumb-index distance  / hand size
    rpinch                     thumb-middle distance / hand size
    idx_reach / mid_reach      wrist-to-tip distance / hand size (extension)
    fist                       all four fingers folded
    """
    size = _dist(lm[WRIST], lm[MID_MCP]) or 1e-6
    up = lambda tip, pip: lm[tip].y < lm[pip].y   # image y grows downward
    f = {
        "idx": up(IDX_TIP, IDX_PIP),
        "mid": up(MID_TIP, MID_PIP),
        "ring": up(RING_TIP, RING_PIP),
        "pinky": up(PINKY_TIP, PINKY_PIP),
        "pinch": _dist(lm[THUMB_TIP], lm[IDX_TIP]) / size,
        "rpinch": _dist(lm[THUMB_TIP], lm[MID_TIP]) / size,
        "idx_reach": _dist(lm[IDX_TIP], lm[WRIST]) / size,
        "mid_reach": _dist(lm[MID_TIP], lm[WRIST]) / size,
    }
    f["fist"] = (not f["idx"] and not f["mid"] and not f["ring"] and not f["pinky"]
                 and f["idx_reach"] < 1.45 and f["pinch"] > 0.15)
    return f
