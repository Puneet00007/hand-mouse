from types import SimpleNamespace as P

from handmouse.gestures import analyze


def hand(**over):
    """Synthetic upright right hand (image coords, y grows down). Pointing pose by default."""
    pts = {i: P(x=0.5, y=0.9) for i in range(21)}
    pts[0] = P(x=0.5, y=0.9)                      # wrist
    pts[9] = P(x=0.5, y=0.6)                      # middle MCP  -> hand size 0.3
    # index extended
    pts[6], pts[8] = P(x=0.45, y=0.45), P(x=0.45, y=0.2)
    # middle, ring, pinky folded (tip below pip)
    pts[10], pts[12] = P(x=0.5, y=0.5), P(x=0.5, y=0.62)
    pts[14], pts[16] = P(x=0.55, y=0.5), P(x=0.55, y=0.62)
    pts[18], pts[20] = P(x=0.6, y=0.55), P(x=0.6, y=0.66)
    pts[4] = P(x=0.6, y=0.7)                      # thumb tip, resting away
    for k, v in over.items():
        pts[int(k[1:])] = v
    return [pts[i] for i in range(21)]


def test_pointing_pose():
    g = analyze(hand())
    assert g["idx"] and not g["mid"] and not g["ring"] and not g["pinky"]
    assert not g["fist"]
    assert g["idx_reach"] > 2.0


def test_pinch_detected_when_thumb_touches_index():
    g = analyze(hand(t4=P(x=0.45, y=0.21)))
    assert g["pinch"] < 0.1


def test_fist():
    fist = hand(t8=P(x=0.45, y=0.62), t6=P(x=0.45, y=0.5), t4=P(x=0.55, y=0.7))
    g = analyze(fist)
    assert g["fist"]


def test_peace_sign_has_two_fingers_up():
    g = analyze(hand(t12=P(x=0.5, y=0.2), t10=P(x=0.5, y=0.45)))
    assert g["idx"] and g["mid"] and not g["ring"] and not g["pinky"]
