import json

from handmouse.config import Config


def test_roundtrip(tmp_path):
    p = tmp_path / "c.json"
    c = Config(); c.smoothing = 9.0; c.gestures["scroll"] = False; c.accent = "Amber"
    c.save(p)
    d = Config.load(p)
    assert d.smoothing == 9.0 and d.gestures["scroll"] is False and d.accent == "Amber"


def test_bad_values_are_sanitised(tmp_path):
    p = tmp_path / "c.json"
    p.write_text(json.dumps({"smoothing": 999, "hand": "Both", "pinch_on": "abc", "unknown": 1, "accent": "Hotpink",
                             "gestures": {"move": False, "nope": True}}))
    c = Config.load(p)
    assert c.smoothing == 20.0 and c.hand == "Any" and c.pinch_on == 0.28
    assert c.gestures["move"] is False and "nope" not in c.gestures
    assert c.accent == "Mono"


def test_missing_or_corrupt_file(tmp_path):
    assert Config.load(tmp_path / "none.json").smoothing == 5.0
    p = tmp_path / "bad.json"; p.write_text("{not json")
    assert Config.load(p).smoothing == 5.0


def test_pinch_release_above_press():
    c = Config(); c.pinch_on = 0.4; c.pinch_off = 0.2
    assert c.sanitize().pinch_off > c.pinch_on
