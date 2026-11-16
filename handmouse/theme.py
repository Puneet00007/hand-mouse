"""Design tokens. Colours are (light, dark) tuples so CustomTkinter switches themes for us.

Direction: quiet and typographic. Near-black / warm-white surfaces, hairline dividers,
one restrained accent (monochrome by default) used only for the primary action and state.
"""
import os

# name -> (main, hover, on_main)   main/hover/on_main may be (light, dark) tuples
ACCENTS = {
    "Mono":  (("#1A1A1C", "#F0F0F1"), ("#38383C", "#D6D6D8"), ("#FFFFFF", "#0C0C0D")),
    "Sage":  ("#6E9B7F", "#5E896F", "#FFFFFF"),
    "Amber": ("#C98A2B", "#B57A22", "#FFFFFF"),
    "Azure": ("#4F83CC", "#4372B3", "#FFFFFF"),
    "Coral": ("#D4684F", "#BD5A43", "#FFFFFF"),
}
DEFAULT_ACCENT = "Mono"

# hex used for the overlay drawn on the camera preview
OVERLAY = {"Mono": "#F0F0F1", "Sage": "#7FB394", "Amber": "#E0A13A", "Azure": "#6B9BE6", "Coral": "#E8806A"}


def overlay_hex(name: str) -> str:
    return OVERLAY.get(name, OVERLAY[DEFAULT_ACCENT])


BG        = ("#F7F7F5", "#0C0C0D")
SURFACE   = ("#FFFFFF", "#131315")     # raised areas (preview frame, segmented selection)
SUBTLE    = ("#ECECE9", "#1A1A1C")     # hover / selected nav / segmented track
HAIR      = ("#E2E2DE", "#232326")     # 1px dividers
TEXT      = ("#17171A", "#EDEDEE")
MUTED     = ("#75757B", "#86868C")
FAINT     = ("#A6A6AB", "#57575C")
TRACK     = ("#D9D9D5", "#2B2B2F")     # slider / switch off track
KNOB      = ("#FFFFFF", "#8A8A90")
PREVIEW   = "#080809"
GOOD      = "#3FA56B"
WARN      = "#D9A03A"
BAD       = "#D9534F"

FONT = os.environ.get("HANDMOUSE_FONT", "Segoe UI")   # falls back automatically on other systems
