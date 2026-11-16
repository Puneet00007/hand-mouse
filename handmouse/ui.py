"""HandMouse interface - a quiet, typographic desktop UI (CustomTkinter).

Design rules: hairline dividers instead of boxes, one accent used sparingly,
no decorative glyphs, generous spacing, short plain-language copy.
"""
from __future__ import annotations

import sys
import threading
import tkinter as tk
from pathlib import Path

import customtkinter as ctk
from PIL import Image, ImageTk

from . import APP_NAME, __version__
from .config import PRESETS, Config, config_path
from .engine import Engine, list_cameras
from .theme import ACCENTS, BAD, BG, FAINT, FONT, GOOD, HAIR, KNOB, MUTED, PREVIEW, SUBTLE, SURFACE, TEXT, TRACK, WARN

ASSETS = Path(__file__).parent / "assets"

GESTURES = [  # key, title, how, what it does
    ("move", "Move", "Index finger up", "The cursor follows your fingertip inside the active zone."),
    ("click", "Left click", "Quick pinch, thumb and index", "Two quick pinches make a double-click."),
    ("drag", "Drag and drop", "Hold the pinch, then move", "Release the pinch to drop."),
    ("right_click", "Right click", "Pinch thumb and middle finger", "Keep the middle finger extended."),
    ("scroll", "Scroll", "Index and middle finger up", "Move your hand up or down."),
    ("pause", "Pause", "Closed fist, held", "Hold a fist to pause, and again to resume."),
]

NAV = ("Dashboard", "Gestures", "Settings", "About")


class App(ctk.CTk):
    def __init__(self):
        self.cfg = Config.load()
        ctk.set_appearance_mode(self.cfg.appearance)
        super().__init__(fg_color=BG)
        self.title(APP_NAME)
        self.geometry("1160x740")
        self.minsize(1040, 680)
        self.engine = Engine(self.cfg)
        self._page = "Dashboard"
        self._error: str | None = None
        self._save_job = None
        self._last_frame_id = -1
        self._photo = None
        self.wd: dict = {}
        self._tick_n = 0
        self._set_icon()
        self._set_topmost(self.cfg.topmost)
        self._build()
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.bind("<Control-space>", lambda e: self.toggle_tracking())
        self.bind("<Control-p>", lambda e: self.engine.toggle_pause())
        self.after(15, self._tick)
        if self.cfg.auto_start:
            self.after(600, self.toggle_tracking)

    # ------------------------------------------------------------------ tokens
    @property
    def acc(self):
        return ACCENTS.get(self.cfg.accent, ACCENTS["Mono"])        # (main, hover, on_main)

    def f(self, size=13, bold=False):
        return ctk.CTkFont(family=FONT, size=size, weight="bold" if bold else "normal")

    def lbl(self, parent, text, size=13, bold=False, color=TEXT, **kw):
        return ctk.CTkLabel(parent, text=text, font=self.f(size, bold), text_color=color, **kw)

    @staticmethod
    def resolve(color):
        """Pick the light/dark half of a (light, dark) colour tuple for plain tk widgets."""
        if isinstance(color, str):
            return color
        return color[1] if ctk.get_appearance_mode() == "Dark" else color[0]

    def hair(self, parent, **pack):
        h = tk.Frame(parent, height=1, bd=0, highlightthickness=0, bg=self.resolve(HAIR))
        h.pack(fill="x", **pack)
        return h

    def dot(self, parent, color):
        return ctk.CTkFrame(parent, width=8, height=8, corner_radius=4, fg_color=color)

    def _set_icon(self):
        try:
            if sys.platform == "win32":
                self.after(250, lambda: self.iconbitmap(str(ASSETS / "icon.ico")))
            else:
                self._icon = ImageTk.PhotoImage(Image.open(ASSETS / "icon.png"))
                self.iconphoto(True, self._icon)
        except Exception:
            pass

    def _set_topmost(self, value: bool):
        try:
            self.attributes("-topmost", bool(value))
        except tk.TclError:
            pass

    def save_soon(self):
        if self._save_job:
            self.after_cancel(self._save_job)
        self._save_job = self.after(400, self.cfg.save)

    def _restart_if_running(self):
        if self.engine.running:
            self.engine.stop()
            self.engine.start()

    # ------------------------------------------------------------------ reusable controls
    def primary_btn(self, parent, text, command, height=44):
        main, hover, on = self.acc
        return ctk.CTkButton(parent, text=text, command=command, height=height, corner_radius=10,
                             font=self.f(14, True), fg_color=main, hover_color=hover, text_color=on)

    def ghost_btn(self, parent, text, command, height=36, color=TEXT, width=140):
        return ctk.CTkButton(parent, text=text, command=command, height=height, width=width, corner_radius=10,
                             font=self.f(13, True), fg_color="transparent", hover_color=SUBTLE,
                             text_color=color, border_width=1, border_color=HAIR)

    def segmented(self, parent, values, current, command, width=None):
        seg = ctk.CTkSegmentedButton(
            parent, values=values, command=command, height=30, corner_radius=8, border_width=3,
            font=self.f(12, True), fg_color=SUBTLE, selected_color=SURFACE, selected_hover_color=SURFACE,
            unselected_color=SUBTLE, unselected_hover_color=SUBTLE, text_color=TEXT,
            **({"width": width} if width else {}))
        if current is not None:
            seg.set(current)
        return seg

    def switch(self, parent, value, command):
        var = tk.BooleanVar(value=value)
        sw = ctk.CTkSwitch(parent, text="", variable=var, width=42, switch_width=38, switch_height=20,
                           progress_color=self.acc[0], fg_color=TRACK, button_color=KNOB,
                           button_hover_color=KNOB, command=lambda: command(var.get()))
        return sw

    def row(self, parent, title, hint=None, last=False, pad=15):
        """Settings-style row: title + hint on the left, control frame on the right, hairline below."""
        outer = ctk.CTkFrame(parent, fg_color="transparent")
        outer.pack(fill="x")
        inner = ctk.CTkFrame(outer, fg_color="transparent")
        inner.pack(fill="x", pady=pad)
        inner.grid_columnconfigure(0, weight=1)
        self.lbl(inner, title, 14, True).grid(row=0, column=0, sticky="w")
        if hint:
            self.lbl(inner, hint, 12, color=MUTED, justify="left", wraplength=430).grid(row=1, column=0, sticky="w")
        ctl = ctk.CTkFrame(inner, fg_color="transparent")
        ctl.grid(row=0, column=1, rowspan=2, sticky="e", padx=(20, 0))
        if not last:
            self.hair(outer)
        return ctl

    def heading(self, parent, text, first=False):
        self.lbl(parent, text.upper(), 11, True, FAINT).pack(anchor="w", pady=(0 if first else 30, 2))
        self.hair(parent)

    # ------------------------------------------------------------------ shell
    def _build(self):
        for w in self.winfo_children():
            w.destroy()
        self.grid_columnconfigure(2, weight=1)
        self.grid_rowconfigure(0, weight=1)

        sb = ctk.CTkFrame(self, width=208, fg_color="transparent", corner_radius=0)
        sb.grid(row=0, column=0, sticky="nsew")
        sb.grid_propagate(False)
        sb.grid_rowconfigure(20, weight=1)
        sb.grid_columnconfigure(0, weight=1)
        brand = ctk.CTkFrame(sb, fg_color="transparent")
        brand.grid(row=0, column=0, sticky="w", padx=24, pady=(30, 34))
        logo = ctk.CTkImage(Image.open(ASSETS / "icon.png"), size=(30, 30))
        ctk.CTkLabel(brand, image=logo, text="").pack(side="left")
        self.lbl(brand, APP_NAME, 16, True).pack(side="left", padx=(10, 0))

        self._nav = {}
        for i, name in enumerate(NAV):
            b = ctk.CTkButton(sb, text=name, anchor="w", height=36, corner_radius=8, font=self.f(13, True),
                              fg_color="transparent", text_color=MUTED, hover_color=SUBTLE,
                              command=lambda n=name: self.show_page(n))
            b.grid(row=1 + i, column=0, padx=14, pady=1, sticky="ew")
            self._nav[name] = b

        foot = ctk.CTkFrame(sb, fg_color="transparent")
        foot.grid(row=21, column=0, sticky="ew", padx=24, pady=(0, 24))
        st = ctk.CTkFrame(foot, fg_color="transparent")
        st.pack(anchor="w")
        self.side_dot = self.dot(st, MUTED)
        self.side_dot.pack(side="left", pady=(2, 0))
        self.side_status = self.lbl(st, "Stopped", 12, True, MUTED)
        self.side_status.pack(side="left", padx=(8, 0))
        self.lbl(foot, f"Version {__version__}", 11, color=FAINT).pack(anchor="w", pady=(4, 0))

        tk.Frame(self, width=1, bd=0, highlightthickness=0, bg=self.resolve(HAIR)).grid(
            row=0, column=1, sticky="ns")

        self.content = ctk.CTkFrame(self, fg_color="transparent")
        self.content.grid(row=0, column=2, sticky="nsew", padx=40, pady=(32, 28))
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(1, weight=1)
        self.show_page(self._page)

    def show_page(self, name: str):
        self._page, self.wd, self._last_frame_id = name, {}, -1
        for n, b in self._nav.items():
            b.configure(fg_color=SUBTLE if n == name else "transparent", text_color=TEXT if n == name else MUTED)
        for w in self.content.winfo_children():
            w.destroy()
        head = ctk.CTkFrame(self.content, fg_color="transparent")
        head.grid(row=0, column=0, sticky="ew", pady=(0, 24))
        head.grid_columnconfigure(0, weight=1)
        self.lbl(head, name, 26, True).grid(row=0, column=0, sticky="w")
        if name == "Dashboard":
            chip = ctk.CTkFrame(head, fg_color="transparent")
            chip.grid(row=0, column=1, sticky="e")
            self.wd["chip_dot"] = self.dot(chip, MUTED)
            self.wd["chip_dot"].pack(side="left", pady=(2, 0))
            self.wd["chip"] = self.lbl(chip, "Stopped", 13, True, MUTED)
            self.wd["chip"].pack(side="left", padx=(8, 0))
        body = ctk.CTkFrame(self.content, fg_color="transparent")
        body.grid(row=1, column=0, sticky="nsew")
        getattr(self, f"_page_{name.lower()}")(body)
        self._refresh_controls()

    # ------------------------------------------------------------------ dashboard
    def _page_dashboard(self, p):
        p.grid_columnconfigure(0, weight=1)
        p.grid_rowconfigure(0, weight=1)
        w = self.wd

        left = ctk.CTkFrame(p, fg_color="transparent")
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 36))
        holder = ctk.CTkFrame(left, fg_color=PREVIEW, corner_radius=14, border_width=1, border_color=HAIR,
                              height=420)
        holder.pack(fill="x", anchor="n")
        holder.pack_propagate(False)
        holder.grid_propagate(False)
        w["holder"] = holder
        self.lbl(left, "Keep your hand inside the outlined box. Move your index finger to steer.", 12,
                 color=FAINT).pack(anchor="w", pady=(14, 0))

        def fit(event):
            h = int(min(event.width * 0.75, max(event.height - 40, 200)))
            if abs(h - int(holder.cget("height"))) > 1:
                holder.configure(height=h)
        left.bind("<Configure>", fit)
        w["preview"] = tk.Label(holder._canvas, bg=PREVIEW, fg="#7C7C82", font=(FONT, 12), bd=0, justify="center")
        w["preview"].place(relx=0.5, rely=0.5, anchor="center")

        right = ctk.CTkFrame(p, fg_color="transparent", width=260)
        right.grid(row=0, column=1, sticky="ns")
        right.grid_propagate(False)
        right.grid_columnconfigure(0, weight=1)

        w["start"] = self.primary_btn(right, "Start tracking", self.toggle_tracking)
        w["start"].grid(row=0, column=0, sticky="ew")
        w["pause"] = self.ghost_btn(right, "Pause", self.engine.toggle_pause, height=38, width=0)
        w["pause"].grid(row=1, column=0, sticky="ew", pady=(10, 0))

        stats = ctk.CTkFrame(right, fg_color="transparent")
        stats.grid(row=2, column=0, sticky="ew", pady=(34, 0))
        self.lbl(stats, "LIVE", 11, True, FAINT).pack(anchor="w", pady=(0, 2))
        self.hair(stats)
        for key, name in (("fps", "Frame rate"), ("mode", "Gesture"), ("hand", "Hand"), ("clicks", "Clicks")):
            r = ctk.CTkFrame(stats, fg_color="transparent")
            r.pack(fill="x")
            inner = ctk.CTkFrame(r, fg_color="transparent")
            inner.pack(fill="x", pady=11)
            self.lbl(inner, name, 13, color=MUTED).pack(side="left")
            w[key] = self.lbl(inner, "-", 13, True)
            w[key].pack(side="right")
            self.hair(r)

        prof = ctk.CTkFrame(right, fg_color="transparent")
        prof.grid(row=3, column=0, sticky="ew", pady=(34, 0))
        self.lbl(prof, "PROFILE", 11, True, FAINT).pack(anchor="w", pady=(0, 10))
        cur = next((n for n, v in PRESETS.items() if abs(v["smoothing"] - self.cfg.smoothing) < 1e-6
                    and abs(v["margin_pct"] - self.cfg.margin_pct) < 1e-6), None)
        seg = self.segmented(prof, list(PRESETS), cur, self._preset)
        seg.pack(fill="x")
        self.lbl(prof, "Precise is steadier. Fast is more responsive.", 12, color=MUTED, justify="left",
                 wraplength=250).pack(anchor="w", pady=(8, 0))

        w["msg"] = self.lbl(right, "", 12, color=MUTED, justify="left", wraplength=250)
        w["msg"].grid(row=4, column=0, sticky="sw", pady=(26, 0))
        right.grid_rowconfigure(4, weight=1)
        self._set_preview_text()

    def _preset(self, name):
        self.cfg.apply_preset(name)
        self.save_soon()

    def _set_preview_text(self):
        lab = self.wd.get("preview")
        if lab is None or not lab.winfo_exists():
            return
        self._photo = None
        if self.engine.running and not self.cfg.show_preview:
            text = "Preview is off\nTracking continues in the background"
        elif self.engine.running:
            text = "Starting camera..."
        else:
            text = "Camera is off\nStart tracking to begin"
        lab.configure(image="", text=text)

    # ------------------------------------------------------------------ gestures
    def _page_gestures(self, p):
        col = ctk.CTkFrame(p, fg_color="transparent")
        col.pack(fill="both", expand=True)
        self.lbl(col, "Turn off anything you don't need. Changes apply immediately.", 13, color=MUTED).pack(
            anchor="w", pady=(0, 18))
        self.hair(col)
        for key, title, how, desc in GESTURES:
            ctl = self.row(col, title, None, pad=16)
            inner = ctl.master
            self.lbl(inner, f"{how}.  {desc}", 12, color=MUTED, justify="left", wraplength=560).grid(
                row=1, column=0, sticky="w")
            sw = self.switch(ctl, self.cfg.gestures.get(key, True), lambda v, k=key: self._set_gesture(k, v))
            if self.cfg.gestures.get(key, True):
                sw.select()
            sw.pack()
        self.lbl(col, "With your hand out of view, HandMouse never touches the mouse.", 12, color=FAINT).pack(
            anchor="w", pady=(20, 0))

    def _set_gesture(self, key, value):
        self.cfg.gestures[key] = bool(value)
        self.save_soon()

    # ------------------------------------------------------------------ settings
    def _slider(self, parent, title, hint, attr, lo, hi, steps, fmt, setter=None, last=False):
        ctl = self.row(parent, title, hint, last=last)
        val = self.lbl(ctl, fmt(getattr(self.cfg, attr)), 13, True, TEXT, width=64, anchor="e")
        val.pack(side="left", padx=(0, 14))

        def on(v):
            v = round(v, 3)
            (setter or (lambda x: setattr(self.cfg, attr, x)))(v)
            val.configure(text=fmt(v))
            self.save_soon()
        s = ctk.CTkSlider(ctl, from_=lo, to=hi, number_of_steps=steps, command=on, width=220, height=16,
                          progress_color=self.acc[0], button_color=self.acc[0], button_hover_color=self.acc[1],
                          fg_color=TRACK, button_length=0)
        s.set(getattr(self.cfg, attr))
        s.pack(side="left")

    def _toggle_row(self, parent, title, hint, attr, after=None, last=False):
        ctl = self.row(parent, title, hint, last=last)

        def on(v):
            setattr(self.cfg, attr, v)
            self.save_soon()
            if after:
                after()
        sw = self.switch(ctl, getattr(self.cfg, attr), on)
        if getattr(self.cfg, attr):
            sw.select()
        sw.pack()

    def _page_settings(self, p):
        p.grid_columnconfigure(0, weight=1)
        p.grid_rowconfigure(0, weight=1)
        sc = ctk.CTkScrollableFrame(p, fg_color="transparent", scrollbar_button_color=SUBTLE,
                                    scrollbar_button_hover_color=HAIR)
        sc.grid(row=0, column=0, sticky="nsew")
        cfg = self.cfg

        self.heading(sc, "Camera", first=True)
        ctl = self.row(sc, "Camera", "Scan to find connected webcams.")
        self.cam_menu = ctk.CTkOptionMenu(ctl, values=[f"Camera {cfg.camera_index}"], width=150, height=32,
                                          corner_radius=8, fg_color=SUBTLE, button_color=SUBTLE,
                                          button_hover_color=HAIR, text_color=TEXT, font=self.f(12, True),
                                          dropdown_fg_color=SURFACE, dropdown_text_color=TEXT,
                                          dropdown_hover_color=SUBTLE, command=self._set_camera)
        self.cam_menu.pack(side="left", padx=(0, 8))
        self.ghost_btn(ctl, "Scan", self._scan_cameras, height=32, width=64).pack(side="left")
        ctl = self.row(sc, "Preferred hand", "Ignore the other hand.")
        self.segmented(ctl, ["Any", "Left", "Right"], cfg.hand, self._set_hand).pack()
        ctl = self.row(sc, "Tracking quality", "Accurate is steadier but uses more CPU.", last=True)
        self.segmented(ctl, ["Fast", "Accurate"], "Accurate" if cfg.model_complexity else "Fast",
                       self._set_quality).pack()

        self.heading(sc, "Cursor")
        self._slider(sc, "Smoothing", "Higher is steadier, with a little more lag.", "smoothing",
                     1, 15, 28, lambda v: f"{v:.1f}")
        self._slider(sc, "Active zone padding", "How much of the camera image is ignored around the edges.",
                     "margin_pct", 5, 35, 30, lambda v: f"{v:.0f}%", last=True)

        self.heading(sc, "Clicks and scrolling")

        def set_pinch(v):
            cfg.pinch_on = v
            cfg.pinch_off = v + 0.10
        self._slider(sc, "Pinch sensitivity", "Higher registers a pinch from further apart.", "pinch_on",
                     0.15, 0.45, 30, lambda v: f"{v:.2f}", setter=set_pinch)
        self._slider(sc, "Drag hold time", "How long a pinch is held before it becomes a drag.", "drag_hold",
                     0.15, 0.8, 26, lambda v: f"{v:.2f} s")
        self._slider(sc, "Scroll speed", None, "scroll_speed", 10, 100, 18, lambda v: f"{v:.0f}")
        self._toggle_row(sc, "Reverse scroll direction", "Moving your hand up scrolls down.", "scroll_invert")
        self._slider(sc, "Pause hold time", "How long to hold a fist to pause or resume.", "fist_hold",
                     0.5, 3.0, 25, lambda v: f"{v:.1f} s", last=True)

        self.heading(sc, "Appearance")
        ctl = self.row(sc, "Theme")
        self.segmented(ctl, ["Dark", "Light", "System"], cfg.appearance, self._set_theme).pack()
        ctl = self.row(sc, "Accent", "Used for the main button, sliders and the camera overlay.")
        for name, (main, hover, _on) in ACCENTS.items():
            sel = name == cfg.accent
            ctk.CTkButton(ctl, text="", width=22, height=22, corner_radius=11, fg_color=main, hover_color=hover,
                          border_width=2 if sel else 0, border_color=TEXT,
                          command=lambda n=name: self._set_accent(n)).pack(side="left", padx=4)
        self._toggle_row(sc, "Draw hand skeleton", "Show finger joints on the preview.", "show_skeleton")
        self._toggle_row(sc, "Draw active zone", "Show the box you move your finger in.", "show_zone", last=True)

        self.heading(sc, "Behaviour")
        self._toggle_row(sc, "Show camera preview", "Turn off to save CPU.", "show_preview",
                         after=self._set_preview_text)
        self._toggle_row(sc, "Sound feedback", "A short tone on click, and when pausing (Windows).", "sound")
        self._toggle_row(sc, "Keep window on top", None, "topmost",
                         after=lambda: self._set_topmost(cfg.topmost))
        self._toggle_row(sc, "Start tracking when the app opens", None, "auto_start", last=True)

        self.hair(sc, pady=(30, 0))
        ctl = self.row(sc, "Reset settings", "Restore every setting to its default.", last=True)
        self.ghost_btn(ctl, "Reset", self._reset, color=BAD, width=90).pack()

    def _scan_cameras(self):
        threading.Thread(target=lambda: self.after(0, lambda c=list_cameras(): self._cams_found(c)),
                         daemon=True).start()

    def _cams_found(self, cams):
        if not self.cam_menu.winfo_exists():
            return
        vals = [f"Camera {i}" for i in cams] or ["No camera found"]
        self.cam_menu.configure(values=vals)
        self.cam_menu.set(f"Camera {self.cfg.camera_index}" if f"Camera {self.cfg.camera_index}" in vals
                          else vals[0])

    def _set_camera(self, v):
        if v.startswith("Camera "):
            self.cfg.camera_index = int(v.split()[1])
            self.save_soon()
            self._restart_if_running()

    def _set_hand(self, v):
        self.cfg.hand = v
        self.save_soon()
        self._restart_if_running()

    def _set_quality(self, v):
        self.cfg.model_complexity = 1 if v == "Accurate" else 0
        self.save_soon()
        self._restart_if_running()

    def _set_accent(self, name):
        self.cfg.accent = name
        self.save_soon()
        self._build()

    def _set_theme(self, v):
        self.cfg.appearance = v
        ctk.set_appearance_mode(v)
        self.save_soon()
        self.after(50, self._build)          # plain-tk hairlines need re-colouring

    def _reset(self):
        fresh = Config()
        for k, v in fresh.__dict__.items():
            setattr(self.cfg, k, v)
        self.cfg.gestures = dict(fresh.gestures)
        self.cfg.save()
        ctk.set_appearance_mode(self.cfg.appearance)
        self._set_topmost(self.cfg.topmost)
        self._build()

    # ------------------------------------------------------------------ about
    def _page_about(self, p):
        col = ctk.CTkFrame(p, fg_color="transparent")
        col.pack(fill="both", expand=True)
        top = ctk.CTkFrame(col, fg_color="transparent")
        top.pack(anchor="w", pady=(0, 30))
        logo = ctk.CTkImage(Image.open(ASSETS / "icon.png"), size=(64, 64))
        ctk.CTkLabel(top, image=logo, text="").pack(side="left")
        txt = ctk.CTkFrame(top, fg_color="transparent")
        txt.pack(side="left", padx=18)
        self.lbl(txt, APP_NAME, 18, True).pack(anchor="w")
        self.lbl(txt, f"Version {__version__}  ·  MIT licence", 12, color=MUTED).pack(anchor="w")
        self.lbl(txt, "Hand tracking by MediaPipe. Runs entirely on this computer.", 12, color=MUTED).pack(anchor="w")

        self.heading(col, "Shortcuts", first=True)
        for k, d in (("Ctrl + Space", "Start or stop tracking"), ("Ctrl + P", "Pause or resume"),
                     ("Fist, held", "Pause or resume from anywhere"),
                     ("Mouse into a screen corner", "Emergency stop")):
            ctl = self.row(col, d, pad=12)
            self.lbl(ctl, k, 12, True, MUTED).pack()
        self.heading(col, "Files")
        ctl = self.row(col, "Settings file", pad=12, last=True)
        self.lbl(ctl, str(config_path()), 11, color=MUTED).pack()

    # ------------------------------------------------------------------ run loop
    def toggle_tracking(self):
        self._error = None
        if self.engine.running:
            self.engine.stop()
        else:
            self.engine.start()
        self._refresh_controls()
        self._set_preview_text()

    def _alive(self, key):
        w = self.wd.get(key)
        return w if (w is not None and w.winfo_exists()) else None

    def _status(self):
        e = self.engine
        if self._error:
            return "Error", BAD
        if not e.running:
            return "Stopped", MUTED
        if e.stats["paused"]:
            return "Paused", WARN
        return "Tracking", GOOD

    def _refresh_controls(self):
        text, color = self._status()
        self.side_dot.configure(fg_color=color)
        self.side_status.configure(text=text, text_color=TEXT if text != "Stopped" else MUTED)
        if self._alive("chip"):
            self.wd["chip"].configure(text=text, text_color=TEXT if text != "Stopped" else MUTED)
            self.wd["chip_dot"].configure(fg_color=color)
        st = self._alive("start")
        if st:
            running = self.engine.running
            main, hover, on = self.acc
            st.configure(text="Stop tracking" if running else "Start tracking",
                         fg_color=SUBTLE if running else main, hover_color=HAIR if running else hover,
                         text_color=TEXT if running else on)
        pa = self._alive("pause")
        if pa:
            pa.configure(text="Resume" if self.engine.stats["paused"] else "Pause",
                         state="normal" if self.engine.running else "disabled")
        msg = self._alive("msg")
        if msg:
            msg.configure(text=self._error or "Hold a fist to pause. Ctrl+Space starts and stops.",
                          text_color=BAD if self._error else FAINT)

    def _tick(self):
        try:
            e = self.engine
            if e.error:
                self._error, e.error = e.error, None
                self._refresh_controls()
                self._set_preview_text()
            self._tick_n += 1

            lab = self._alive("preview")
            if lab and e.running and self.cfg.show_preview:
                fid, frame = e.get_frame()
                if frame is not None and fid != self._last_frame_id:
                    self._last_frame_id = fid
                    hold = self.wd["holder"]
                    fit = min(max(hold.winfo_width() - 4, 160) / frame.shape[1],
                              max(hold.winfo_height() - 4, 120) / frame.shape[0])
                    size = (int(frame.shape[1] * fit), int(frame.shape[0] * fit))
                    self._photo = ImageTk.PhotoImage(Image.fromarray(frame).resize(size, Image.BILINEAR))
                    lab.configure(image=self._photo, text="")

            if self._tick_n % 6 == 0:
                s = e.stats
                if self._alive("fps"):
                    w = self.wd
                    w["fps"].configure(text=f"{s['fps']:.0f}" if e.running else "-")
                    w["mode"].configure(text=s["mode"].capitalize() if e.running else "-")
                    w["hand"].configure(text="Detected" if s["hand"] else ("None" if e.running else "-"))
                    w["clicks"].configure(text=str(s["clicks"] + s["right_clicks"]))
                self._refresh_controls()
        finally:
            self.after(15, self._tick)

    def _on_close(self):
        try:
            self.engine.stop()
            self.cfg.save()
        finally:
            self.destroy()


def run():
    App().mainloop()
