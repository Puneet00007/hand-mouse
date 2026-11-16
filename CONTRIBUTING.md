# Contributing

Thanks for helping make HandMouse better!

## Dev setup
```bash
python -m venv venv && venv\Scripts\activate      # Windows   (source venv/bin/activate elsewhere)
pip install -r requirements.txt -r requirements-dev.txt
python -m pytest        # unit tests (no camera needed)
ruff check .            # lint
python -m handmouse     # run the app
```
Use Python 3.9 - 3.12 (MediaPipe does not support newer versions yet).

## Project layout
| Module | Responsibility |
|---|---|
| `handmouse/gestures.py` | landmarks -> features (pure functions) |
| `handmouse/controller.py` | gesture state machine -> mouse actions (takes any mouse object) |
| `handmouse/engine.py` | camera + MediaPipe thread, preview frames, stats |
| `handmouse/mouse.py` | PyAutoGUI backend + DPI fix |
| `handmouse/config.py` | typed settings, validation, JSON persistence |
| `handmouse/ui.py`, `theme.py` | CustomTkinter interface |

## Adding a gesture
1. Add the feature to `gestures.analyze()` and a test in `tests/test_gestures.py`.
2. Handle it in `GestureController.update()` and add a test with the fake mouse in `tests/test_controller.py`.
3. Add a switch key in `config.GESTURE_KEYS` and a card in `ui.GESTURE_INFO`.

Please keep PRs focused, run `ruff` and `pytest`, and update the README/CHANGELOG when behaviour changes.
