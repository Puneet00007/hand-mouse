"""Camera + MediaPipe tracking loop running in a background thread."""
from __future__ import annotations

import sys
import threading
import time
from typing import Optional

import cv2

from .config import Config
from .controller import GestureController
from .gestures import IDX_TIP, THUMB_TIP, analyze
from .theme import overlay_hex

CAM_W, CAM_H = 640, 480


def list_cameras(max_index: int = 5) -> list[int]:
    """Probe camera indices (takes a second or two)."""
    found = []
    for i in range(max_index):
        cap = cv2.VideoCapture(i, cv2.CAP_DSHOW) if sys.platform == "win32" else cv2.VideoCapture(i)
        if cap.isOpened():
            found.append(i)
        cap.release()
    return found


def _beep(freq: int, ms: int) -> None:
    if sys.platform != "win32":
        return
    try:
        import winsound
        threading.Thread(target=winsound.Beep, args=(freq, ms), daemon=True).start()
    except Exception:
        pass


def _hex_to_bgr(h: str):
    h = h.lstrip("#")
    return int(h[4:6], 16), int(h[2:4], 16), int(h[0:2], 16)


class Engine:
    """start() / stop() / toggle_pause();  poll get_frame() and stats from the UI thread."""

    def __init__(self, cfg: Config, mouse=None):
        self.cfg = cfg
        self._mouse = mouse
        self._thread: Optional[threading.Thread] = None
        self._stop = threading.Event()
        self._lock = threading.Lock()
        self._frame = None
        self._frame_id = 0
        self.controller: Optional[GestureController] = None
        self.stats = {"fps": 0.0, "mode": "stopped", "hand": False, "clicks": 0,
                      "right_clicks": 0, "drags": 0, "paused": False}
        self.error: Optional[str] = None
        self.running = False

    # ------------------------------------------------------------------
    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self.error = None
        self._stop.clear()
        self.running = True
        self._thread = threading.Thread(target=self._run, daemon=True, name="handmouse-engine")
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=3)
        self.running = False
        with self._lock:
            self._frame = None
        self.stats.update(mode="stopped", hand=False, fps=0.0, paused=False)

    def toggle_pause(self) -> None:
        if self.controller:
            self.controller.toggle_pause()

    def get_frame(self):
        """Return (frame_id, RGB ndarray) of the newest preview frame, or (id, None)."""
        with self._lock:
            return self._frame_id, self._frame

    # ------------------------------------------------------------------
    def _on_event(self, kind: str) -> None:
        s = self.stats
        if kind == "click":
            s["clicks"] += 1
        elif kind == "right_click":
            s["right_clicks"] += 1
        elif kind == "drag_start":
            s["drags"] += 1
        if not self.cfg.sound:
            return
        if kind in ("click", "right_click", "drag_start"):
            _beep(1200, 25)
        elif kind == "pause":
            _beep(400, 150)
        elif kind == "resume":
            _beep(800, 150)

    def _pick_hand(self, res):
        """Choose the hand matching the Left/Right preference (frames are mirrored)."""
        if not res.multi_hand_landmarks:
            return None
        pref = self.cfg.hand
        if pref == "Any" or not res.multi_handedness:
            return res.multi_hand_landmarks[0]
        for lms, hd in zip(res.multi_hand_landmarks, res.multi_handedness):
            if hd.classification[0].label == pref:
                return lms
        return None

    def _run(self) -> None:
        import mediapipe as mp  # heavy import: only when tracking starts
        cfg = self.cfg
        try:
            if self._mouse is None:
                from .mouse import PyAutoGuiMouse
                self._mouse = PyAutoGuiMouse()
            mouse = self._mouse
            cap = (cv2.VideoCapture(cfg.camera_index, cv2.CAP_DSHOW)
                   if sys.platform == "win32" else cv2.VideoCapture(cfg.camera_index))
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAM_W)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAM_H)
            if not cap.isOpened():
                self.error = (f"Could not open camera {cfg.camera_index}. Close other apps that "
                              "use the webcam or pick another camera in Settings.")
                return
            hands = mp.solutions.hands.Hands(
                max_num_hands=2 if cfg.hand != "Any" else 1,
                model_complexity=cfg.model_complexity,
                min_detection_confidence=0.7, min_tracking_confidence=0.6)
        except Exception as exc:                    # noqa: BLE001
            self.error = f"Startup failed: {exc}"
            self.running = False
            return

        draw = mp.solutions.drawing_utils
        connections = mp.solutions.hands.HAND_CONNECTIONS
        ctrl = self.controller = GestureController(cfg, mouse, self._on_event)
        fps, prev = 0.0, time.time()
        try:
            while not self._stop.is_set():
                ok, frame = cap.read()
                if not ok:
                    self.error = "The camera stopped delivering frames."
                    break
                frame = cv2.flip(frame, 1)
                h, w = frame.shape[:2]
                res = hands.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                now = time.time()
                hand = self._pick_hand(res)
                g = None
                if hand is not None:
                    lm = hand.landmark
                    g = analyze(lm)
                    ctrl.update(g, (lm[IDX_TIP].x, lm[IDX_TIP].y), now)
                else:
                    ctrl.hand_lost()

                fps = 0.9 * fps + 0.1 * (1 / max(now - prev, 1e-6))
                prev = now
                st = self.stats
                st.update(fps=fps, mode=ctrl.mode, hand=hand is not None, paused=ctrl.paused)

                if cfg.show_preview:
                    accent = _hex_to_bgr(overlay_hex(cfg.accent))
                    if cfg.show_zone:
                        m = int(cfg.margin_pct / 100 * w), int(cfg.margin_pct / 100 * h)
                        cv2.rectangle(frame, (m[0], m[1]), (w - m[0], h - m[1]), accent, 2)
                    if hand is not None and cfg.show_skeleton:
                        spec = draw.DrawingSpec(color=accent, thickness=2, circle_radius=2)
                        draw.draw_landmarks(frame, hand, connections, spec,
                                            draw.DrawingSpec(color=(255, 255, 255), thickness=2))
                        lm = hand.landmark
                        p1 = (int(lm[THUMB_TIP].x * w), int(lm[THUMB_TIP].y * h))
                        p2 = (int(lm[IDX_TIP].x * w), int(lm[IDX_TIP].y * h))
                        col = (80, 220, 90) if ctrl.pinching else (200, 200, 200)
                        cv2.line(frame, p1, p2, col, 3)
                    if ctrl.paused:
                        cv2.putText(frame, "PAUSED", (w // 2 - 70, 40),
                                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, (60, 60, 255), 3)
                    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    with self._lock:
                        self._frame, self._frame_id = rgb, self._frame_id + 1
                else:
                    with self._lock:
                        self._frame = None
                    time.sleep(0.001)
        except Exception as exc:                    # noqa: BLE001
            fs = getattr(mouse, "FailSafeException", None)
            if fs and isinstance(exc, fs):
                self.error = "Fail-safe triggered: the mouse was moved into a screen corner."
            else:
                self.error = f"Tracking error: {exc}"
        finally:
            try:
                ctrl.shutdown()
            except Exception:                       # noqa: BLE001
                pass
            cap.release()
            hands.close()
            self.running = False
            self.stats.update(mode="stopped", hand=False, fps=0.0)
