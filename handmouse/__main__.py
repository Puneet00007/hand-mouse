"""python -m handmouse            -> opens the app
python -m handmouse --cli      -> headless: just run tracking with saved settings (Ctrl+C to quit)
"""
import argparse
import time

from . import APP_NAME, __version__


def main(argv=None):
    ap = argparse.ArgumentParser(prog="handmouse", description=f"{APP_NAME} - gesture mouse control")
    ap.add_argument("--cli", action="store_true", help="run without the window (uses saved settings)")
    ap.add_argument("--camera", type=int, help="camera index (overrides saved setting)")
    ap.add_argument("--reset", action="store_true", help="reset saved settings to defaults")
    ap.add_argument("--version", action="version", version=f"{APP_NAME} {__version__}")
    args = ap.parse_args(argv)

    from .config import Config
    if args.reset:
        Config().save()
        print("Settings reset.")
    if args.cli:
        from .engine import Engine
        cfg = Config.load()
        if args.camera is not None:
            cfg.camera_index = args.camera
        cfg.show_preview = False
        eng = Engine(cfg)
        eng.start()
        print(f"{APP_NAME} tracking... press Ctrl+C to stop.")
        try:
            while eng.running:
                if eng.error:
                    print("Error:", eng.error)
                    break
                time.sleep(0.2)
        except KeyboardInterrupt:
            pass
        eng.stop()
        return
    from .ui import run
    run()


if __name__ == "__main__":
    main()
