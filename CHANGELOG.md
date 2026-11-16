# Changelog

## 2.1.0
- Interface redesign: quiet, typographic layout with hairline dividers instead of boxed cards, no decorative glyphs.
- Monochrome by default; accents are now Mono, Sage, Amber, Azure and Coral (an old saved accent falls back to Mono).
- New app icon: graphite tile with a cursor and tracking ring.
- Preview keeps a 4:3 shape; settings are laid out as plain rows.
- Fix: gesture rows and switches now reflect saved state on first draw.

## 2.0.0
- New desktop app with a dark/light UI: dashboard with live camera preview, gesture toggles, full settings page.
- Accent colours, profiles (Precise / Balanced / Fast), left/right hand preference, camera picker.
- Settings are saved automatically (`%APPDATA%\HandMouse\config.json`).
- Gesture logic split into testable modules (`gestures`, `controller`, `engine`) with unit tests and CI.
- Fist-hold pause, double-click via two quick pinches, drag & drop, scrolling, right click.
- Windows launchers: `setup.bat` (with desktop shortcut), `run.bat`, `run_debug.bat`, `build_exe.bat`.

## 1.0.0
- Initial command-line prototype.
