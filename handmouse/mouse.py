"""Mouse backend (PyAutoGUI). Kept tiny so tests can swap in a fake."""
from __future__ import annotations

import ctypes
import sys


def ensure_dpi_aware() -> None:
    """Make pixel coordinates match on scaled / high-DPI Windows screens."""
    if sys.platform != "win32":
        return
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


class PyAutoGuiMouse:
    """Thin wrapper around pyautogui. FailSafe stays ON: a corner slam stops the app."""

    def __init__(self):
        ensure_dpi_aware()
        import pyautogui
        pyautogui.PAUSE = 0
        pyautogui.FAILSAFE = True
        self._p = pyautogui
        self.FailSafeException = pyautogui.FailSafeException

    def size(self):
        return tuple(self._p.size())

    def position(self):
        return tuple(self._p.position())

    def move(self, x, y):
        self._p.moveTo(x, y)

    def click(self):
        self._p.click()

    def right_click(self):
        self._p.rightClick()

    def down(self):
        self._p.mouseDown()

    def up(self):
        self._p.mouseUp()

    def scroll(self, amount):
        self._p.scroll(amount)
