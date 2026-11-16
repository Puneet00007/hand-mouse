from handmouse.config import Config
from handmouse.controller import GestureController


class FakeMouse:
    def __init__(self):
        self.log = []
        self.pos = (500, 500)

    def size(self): return (1920, 1080)
    def position(self): return self.pos
    def move(self, x, y): self.pos = (x, y); self.log.append("move")
    def click(self): self.log.append("click")
    def right_click(self): self.log.append("right")
    def down(self): self.log.append("down")
    def up(self): self.log.append("up")
    def scroll(self, a): self.log.append(("scroll", a))


def feats(**o):
    g = dict(idx=True, mid=False, ring=False, pinky=False, pinch=1.0, rpinch=1.0,
             idx_reach=2.2, mid_reach=1.0, fist=False)
    g.update(o)
    return g


def make():
    cfg, m, ev = Config(), FakeMouse(), []
    return cfg, m, GestureController(cfg, m, ev.append), ev


def test_pointing_moves_cursor():
    cfg, m, c, _ = make()
    c.update(feats(), (0.5, 0.5), 0.0)
    assert "move" in m.log


def test_quick_pinch_clicks_once():
    cfg, m, c, ev = make()
    c.update(feats(pinch=0.1), (0.5, 0.5), 0.00)
    c.update(feats(pinch=0.1), (0.5, 0.5), 0.10)
    c.update(feats(pinch=0.9), (0.5, 0.5), 0.15)
    assert m.log.count("click") == 1 and "down" not in m.log
    assert ev == ["click"]


def test_long_pinch_drags_and_drops():
    cfg, m, c, _ = make()
    t = 0.0
    for _ in range(5):
        c.update(feats(pinch=0.1), (0.5, 0.5), t); t += 0.1
    assert "down" in m.log and "click" not in m.log
    c.update(feats(pinch=0.9), (0.5, 0.5), t)
    assert "up" in m.log and not c.dragging


def test_cursor_frozen_at_pinch_start():
    cfg, m, c, _ = make()
    c.update(feats(), (0.5, 0.5), 0.0)
    moves = m.log.count("move")
    c.update(feats(pinch=0.1), (0.7, 0.7), 0.05)
    assert m.log.count("move") == moves


def test_right_click_needs_extended_middle():
    cfg, m, c, _ = make()
    c.update(feats(rpinch=0.1, mid_reach=1.0), (0.5, 0.5), 0.0)   # resting thumb: ignore
    assert "right" not in m.log
    c.update(feats(rpinch=0.1, mid_reach=1.9), (0.5, 0.5), 1.0)
    assert "right" in m.log


def test_fist_toggles_pause():
    cfg, m, c, ev = make()
    c.update(feats(idx=False, fist=True), (0.5, 0.5), 0.0)
    assert not c.paused
    c.update(feats(idx=False, fist=True), (0.5, 0.5), cfg.fist_hold + 0.1)
    assert c.paused and "pause" in ev
    n = len(m.log)
    c.update(feats(), (0.6, 0.6), 5.0)           # paused: no mouse action
    assert len(m.log) == n


def test_disabled_gesture_is_ignored():
    cfg, m, c, _ = make()
    cfg.gestures["click"] = False
    c.update(feats(pinch=0.1), (0.5, 0.5), 0.0)
    c.update(feats(pinch=0.9), (0.5, 0.5), 0.1)
    assert "click" not in m.log


def test_scroll():
    cfg, m, c, _ = make()
    g = feats(mid=True, rpinch=0.9, mid_reach=2.0)
    c.update(g, (0.5, 0.60), 0.0)
    c.update(g, (0.5, 0.50), 0.1)
    assert any(isinstance(x, tuple) and x[1] > 0 for x in m.log)


def test_hand_lost_releases_drag():
    cfg, m, c, _ = make()
    t = 0.0
    for _ in range(5):
        c.update(feats(pinch=0.1), (0.5, 0.5), t); t += 0.1
    c.hand_lost()
    assert m.log[-1] == "up" and not c.dragging


def test_cursor_stays_off_screen_corners():
    cfg, m, c, _ = make()
    for _ in range(60):
        c.update(feats(), (0.0, 0.0), 0.0)
    assert m.pos[0] >= 5 and m.pos[1] >= 5
