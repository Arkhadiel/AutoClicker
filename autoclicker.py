"""
Requirements:
    pip install pynput

Run:
    python autoclicker.py
"""

import threading
import time
import sys
import os
import tkinter as tk
from tkinter import ttk, messagebox

from pynput.mouse import Controller as MouseController, Button
from pynput import keyboard
from pynput.keyboard import Key


def resource_path(relative_path):
    """Get an absolute path to a bundled resource (works both when run as a
    plain script and when packaged as a PyInstaller executable)."""
    base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


BUTTON_MAP = {
    "Left": Button.left,
    "Right": Button.right,
    "Middle": Button.middle,
}

# Special key names a user can type into the "key to press" box, in addition
# to any single character (a, 1, ;, etc.)
SPECIAL_KEYS = {
    "space": Key.space, "enter": Key.enter, "return": Key.enter,
    "tab": Key.tab, "esc": Key.esc, "escape": Key.esc,
    "backspace": Key.backspace, "delete": Key.delete, "del": Key.delete,
    "shift": Key.shift, "ctrl": Key.ctrl, "control": Key.ctrl,
    "alt": Key.alt, "cmd": Key.cmd, "win": Key.cmd,
    "up": Key.up, "down": Key.down, "left": Key.left, "right": Key.right,
    "home": Key.home, "end": Key.end, "pageup": Key.page_up, "pagedown": Key.page_down,
    "capslock": Key.caps_lock, "insert": Key.insert,
    **{f"f{i}": getattr(Key, f"f{i}") for i in range(1, 13)},
}


def parse_key(text):
    """Turn user text (e.g. 'a', 'space', 'F5') into a pynput key object.
    Returns None if the text doesn't map to anything usable."""
    text = (text or "").strip()
    if not text:
        return None
    lowered = text.lower()
    if lowered in SPECIAL_KEYS:
        return SPECIAL_KEYS[lowered]
    if len(text) == 1:
        return text
    return None

# ---------------------------------------------------------------------------
# Dark, edgy, colorblind-safe palette.
# Avoids red/green as the sole differentiator anywhere - status is always
# also conveyed with an icon glyph and text label, not color alone.
# ---------------------------------------------------------------------------
BG = "#0b0b12"          # near-black background
PANEL = "#14141f"        # slightly lighter panel background
BORDER = "#2a2a3d"
TEXT = "#e6e6f0"
SUBTEXT = "#8d8da3"
ACCENT = "#8a5cff"       # violet accent
ACCENT_HOVER = "#a582ff"
STOPPED_COLOR = "#8d8da3"   # gray/blue - neutral, not red
RUNNING_COLOR = "#5cc8ff"   # cyan/blue - distinct from accent violet, colorblind-safe
FONT_FAMILY = "Consolas"


class AutoClicker:
    def __init__(self):
        self.mouse = MouseController()
        self.running = False
        self.thread = None
        self.click_count = 0
        self.fixed_pos = None  # (x, y) or None -> use current cursor position

        # settings, populated by GUI
        self.cps = 10.0
        self.button = Button.left
        self.click_limit = 0  # 0 = unlimited

    def start(self):
        if self.running:
            return
        self.running = True
        self.click_count = 0
        self.thread = threading.Thread(target=self._click_loop, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False

    def _click_loop(self):
        interval = 1.0 / max(self.cps, 0.1)
        next_time = time.perf_counter()
        while self.running:
            if self.fixed_pos is not None:
                self.mouse.position = self.fixed_pos
            self.mouse.click(self.button)
            self.click_count += 1

            if self.click_limit and self.click_count >= self.click_limit:
                self.running = False
                break

            next_time += interval
            sleep_time = next_time - time.perf_counter()
            if sleep_time > 0:
                time.sleep(sleep_time)
            else:
                next_time = time.perf_counter()


class KeyPresser:
    def __init__(self):
        self.keyboard_ctrl = keyboard.Controller()
        self.running = False
        self.thread = None
        self.press_count = 0

        # settings, populated by GUI
        self.pps = 10.0  # presses per second
        self.key = "a"
        self.press_limit = 0  # 0 = unlimited
        self.continuous = False  # True = hold key down instead of rapid press/release

    def start(self):
        if self.running:
            return
        self.running = True
        self.press_count = 0
        if self.continuous:
            # Just hold the key down until stop() releases it - no loop/thread needed.
            try:
                self.keyboard_ctrl.press(self.key)
            except Exception:
                self.running = False
                return
            self.press_count = 1
        else:
            self.thread = threading.Thread(target=self._press_loop, daemon=True)
            self.thread.start()

    def stop(self):
        was_running = self.running
        self.running = False
        if self.continuous and was_running:
            try:
                self.keyboard_ctrl.release(self.key)
            except Exception:
                pass

    def _press_loop(self):
        interval = 1.0 / max(self.pps, 0.1)
        next_time = time.perf_counter()
        while self.running:
            try:
                self.keyboard_ctrl.press(self.key)
                self.keyboard_ctrl.release(self.key)
            except Exception:
                self.running = False
                break
            self.press_count += 1

            if self.press_limit and self.press_count >= self.press_limit:
                self.running = False
                break

            next_time += interval
            sleep_time = next_time - time.perf_counter()
            if sleep_time > 0:
                time.sleep(sleep_time)
            else:
                next_time = time.perf_counter()


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("AUTOCLICKER // v2")
        self.root.configure(bg=BG)
        try:
            self.root.iconbitmap(resource_path("icon.ico"))
        except Exception:
            pass
        self.root.resizable(True, True)
        self.root.minsize(760, 420)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.clicker = AutoClicker()
        self.presser = KeyPresser()

        self._build_style()

        outer = tk.Frame(root, bg=BG, padx=18, pady=16)
        outer.grid(row=0, column=0, sticky="nsew")
        outer.columnconfigure(0, weight=1)
        outer.columnconfigure(1, weight=1)
        outer.rowconfigure(1, weight=1)

        # ---- Header ----
        header = tk.Frame(outer, bg=BG)
        header.grid(row=0, column=0, columnspan=2, sticky="we", pady=(0, 14))
        tk.Label(header, text="AUTOCLICKER", bg=BG, fg=TEXT,
                 font=(FONT_FAMILY, 18, "bold")).pack(side="left")
        tk.Label(header, text=" // v2", bg=BG, fg=ACCENT,
                 font=(FONT_FAMILY, 18, "bold")).pack(side="left")

        card = tk.Frame(outer, bg=PANEL, highlightbackground=BORDER,
                         highlightthickness=1, padx=18, pady=16)
        card.grid(row=1, column=0, sticky="nsew", padx=(0, 9))
        card.columnconfigure(1, weight=1)

        pad = {"padx": 8, "pady": 7}

        # CPS
        self._label(card, "CLICKS / SECOND").grid(row=0, column=0, sticky="w", **pad)
        self.cps_var = tk.StringVar(value="10")
        self._entry(card, self.cps_var, width=10).grid(row=0, column=1, sticky="we", **pad)
        self._sublabel(card, "max 500").grid(row=0, column=2, sticky="w")

        # Mouse button
        self._label(card, "MOUSE BUTTON").grid(row=1, column=0, sticky="w", **pad)
        self.button_var = tk.StringVar(value="Left")
        button_combo = ttk.Combobox(
            card, textvariable=self.button_var, values=["Left", "Right", "Middle"],
            state="readonly", width=8, style="Dark.TCombobox"
        )
        button_combo.grid(row=1, column=1, sticky="w", **pad)

        # Click position mode
        self._label(card, "CLICK POSITION").grid(row=2, column=0, sticky="w", **pad)
        self.pos_mode = tk.StringVar(value="current")
        pos_frame = tk.Frame(card, bg=PANEL)
        pos_frame.grid(row=2, column=1, columnspan=2, sticky="w")
        self._radio(pos_frame, "Current cursor", self.pos_mode, "current").grid(row=0, column=0, sticky="w")
        self._radio(pos_frame, "Fixed position", self.pos_mode, "fixed").grid(row=1, column=0, sticky="w")

        fixed_frame = tk.Frame(card, bg=PANEL)
        fixed_frame.grid(row=3, column=1, columnspan=2, sticky="w", padx=8)
        self.pos_label = self._sublabel(fixed_frame, "◇ not set")
        self.pos_label.grid(row=0, column=0, padx=(0, 10))
        self._button(fixed_frame, "Set to cursor", self.set_fixed_position, small=True).grid(row=0, column=1)

        # Click limit
        self._label(card, "CLICK LIMIT (0 = ∞)").grid(row=4, column=0, sticky="w", **pad)
        self.limit_var = tk.StringVar(value="0")
        self._entry(card, self.limit_var, width=10).grid(row=4, column=1, sticky="we", **pad)

        # Divider
        tk.Frame(card, bg=BORDER, height=1).grid(row=5, column=0, columnspan=3, sticky="we", pady=(12, 12))

        # Status row - icon + text + color, never color alone (colorblind-safe)
        status_frame = tk.Frame(card, bg=PANEL)
        status_frame.grid(row=6, column=0, columnspan=3, sticky="w")
        self.status_icon = tk.Label(status_frame, text="■", bg=PANEL, fg=STOPPED_COLOR,
                                     font=(FONT_FAMILY, 13, "bold"))
        self.status_icon.pack(side="left", padx=(0, 8))
        self.status_var = tk.StringVar(value="STOPPED")
        self.status_label = tk.Label(status_frame, textvariable=self.status_var, bg=PANEL, fg=STOPPED_COLOR,
                                      font=(FONT_FAMILY, 12, "bold"))
        self.status_label.pack(side="left")

        self.count_var = tk.StringVar(value="clicks: 0")
        self._sublabel(card, "", textvariable=self.count_var).grid(row=7, column=0, columnspan=3, sticky="w", pady=(4, 0))

        # Start/stop button
        self.toggle_btn = self._button(card, "▶  START  (F6)", self.toggle, wide=True)
        self.toggle_btn.grid(row=8, column=0, columnspan=3, pady=(16, 0), sticky="we")

        self._sublabel(card, "F6 start/stop   ·   F9 emergency stop").grid(
            row=9, column=0, columnspan=3, pady=(10, 0)
        )

        # ---- Key presser card (sits beside the mouse clicker card) ----
        key_card = tk.Frame(outer, bg=PANEL, highlightbackground=BORDER,
                             highlightthickness=1, padx=18, pady=16)
        key_card.grid(row=1, column=1, sticky="nsew", padx=(9, 0))
        key_card.columnconfigure(1, weight=1)

        key_header = tk.Frame(key_card, bg=PANEL)
        key_header.grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 10))
        tk.Label(key_header, text="KEY PRESSER", bg=PANEL, fg=TEXT,
                 font=(FONT_FAMILY, 12, "bold")).pack(side="left")

        self._label(key_card, "KEY TO PRESS").grid(row=1, column=0, sticky="w", **pad)
        self.key_var = tk.StringVar(value="space")
        self._entry(key_card, self.key_var, width=10).grid(row=1, column=1, sticky="we", **pad)
        self._sublabel(key_card, "e.g. a, 5, space, enter, f1, up").grid(row=1, column=2, sticky="w")

        self._label(key_card, "PRESS MODE").grid(row=2, column=0, sticky="w", **pad)
        self.press_mode = tk.StringVar(value="repeated")
        mode_frame = tk.Frame(key_card, bg=PANEL)
        mode_frame.grid(row=2, column=1, columnspan=2, sticky="w")
        self._radio(mode_frame, "Repeated (press/release at rate)", self.press_mode,
                    "repeated").grid(row=0, column=0, sticky="w")
        self._radio(mode_frame, "Continuous (hold key down)", self.press_mode,
                    "continuous").grid(row=1, column=0, sticky="w")
        self.press_mode.trace_add("write", self._on_press_mode_change)

        self._label(key_card, "PRESSES / SECOND").grid(row=3, column=0, sticky="w", **pad)
        self.pps_var = tk.StringVar(value="10")
        self.pps_entry = self._entry(key_card, self.pps_var, width=10)
        self.pps_entry.grid(row=3, column=1, sticky="we", **pad)
        self._sublabel(key_card, "max 500 (repeated mode only)").grid(row=3, column=2, sticky="w")

        self._label(key_card, "PRESS LIMIT (0 = ∞)").grid(row=4, column=0, sticky="w", **pad)
        self.press_limit_var = tk.StringVar(value="0")
        self.press_limit_entry = self._entry(key_card, self.press_limit_var, width=10)
        self.press_limit_entry.grid(row=4, column=1, sticky="we", **pad)
        self._sublabel(key_card, "(repeated mode only)").grid(row=4, column=2, sticky="w")

        tk.Frame(key_card, bg=BORDER, height=1).grid(row=5, column=0, columnspan=3, sticky="we", pady=(12, 12))

        key_status_frame = tk.Frame(key_card, bg=PANEL)
        key_status_frame.grid(row=6, column=0, columnspan=3, sticky="w")
        self.key_status_icon = tk.Label(key_status_frame, text="■", bg=PANEL, fg=STOPPED_COLOR,
                                         font=(FONT_FAMILY, 13, "bold"))
        self.key_status_icon.pack(side="left", padx=(0, 8))
        self.key_status_var = tk.StringVar(value="STOPPED")
        self.key_status_label = tk.Label(key_status_frame, textvariable=self.key_status_var, bg=PANEL,
                                          fg=STOPPED_COLOR, font=(FONT_FAMILY, 12, "bold"))
        self.key_status_label.pack(side="left")

        self.key_count_var = tk.StringVar(value="presses: 0")
        self._sublabel(key_card, "", textvariable=self.key_count_var).grid(
            row=7, column=0, columnspan=3, sticky="w", pady=(4, 0)
        )

        self.key_toggle_btn = self._button(key_card, "▶  START  (F7)", self.toggle_presser, wide=True)
        self.key_toggle_btn.grid(row=8, column=0, columnspan=3, pady=(16, 0), sticky="we")

        self._sublabel(key_card, "F7 start/stop   ·   F9 emergency stop (stops both)").grid(
            row=9, column=0, columnspan=3, pady=(10, 0)
        )

        # Global hotkeys
        self.hotkey_listener = keyboard.GlobalHotKeys({
            "<F6>": self.toggle,
            "<F7>": self.toggle_presser,
            "<F9>": self.emergency_stop,
        })
        self.hotkey_listener.start()

        self._update_loop()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    # ---- themed widget helpers -------------------------------------------------

    def _build_style(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Dark.TCombobox",
                         fieldbackground=BG, background=PANEL, foreground=TEXT,
                         arrowcolor=TEXT, bordercolor=BORDER, lightcolor=BORDER, darkcolor=BORDER)
        style.map("Dark.TCombobox", fieldbackground=[("readonly", BG)],
                   foreground=[("readonly", TEXT)])

    def _label(self, parent, text):
        return tk.Label(parent, text=text, bg=PANEL, fg=TEXT, font=(FONT_FAMILY, 9, "bold"))

    def _sublabel(self, parent, text, textvariable=None):
        kwargs = {"bg": PANEL, "fg": SUBTEXT, "font": (FONT_FAMILY, 9)}
        if textvariable is not None:
            return tk.Label(parent, textvariable=textvariable, **kwargs)
        return tk.Label(parent, text=text, **kwargs)

    def _entry(self, parent, var, width=10):
        e = tk.Entry(parent, textvariable=var, width=width, bg=BG, fg=TEXT,
                      insertbackground=TEXT, relief="flat", highlightthickness=1,
                      highlightbackground=BORDER, highlightcolor=ACCENT,
                      font=(FONT_FAMILY, 10))
        return e

    def _radio(self, parent, text, var, value):
        return tk.Radiobutton(parent, text=text, variable=var, value=value,
                               bg=PANEL, fg=TEXT, selectcolor=BG,
                               activebackground=PANEL, activeforeground=ACCENT,
                               highlightthickness=0, font=(FONT_FAMILY, 9))

    def _button(self, parent, text, command, wide=False, small=False):
        btn = tk.Button(parent, text=text, command=command, bg=ACCENT, fg="#0b0b12",
                         activebackground=ACCENT_HOVER, activeforeground="#0b0b12",
                         relief="flat", cursor="hand2",
                         font=(FONT_FAMILY, 9 if small else 11, "bold"),
                         padx=10 if small else 6, pady=3 if small else 8)
        return btn

    # ---- logic -------------------------------------------------------------

    def set_fixed_position(self):
        x, y = self.clicker.mouse.position
        self.clicker.fixed_pos = (x, y)
        self.pos_label.config(text=f"◆ ({x}, {y})")

    def _read_settings(self):
        try:
            cps = float(self.cps_var.get())
        except ValueError:
            cps = 10.0
        cps = max(0.1, min(cps, 500.0))
        self.clicker.cps = cps

        self.clicker.button = BUTTON_MAP.get(self.button_var.get(), Button.left)

        if self.pos_mode.get() == "fixed":
            if self.clicker.fixed_pos is None:
                messagebox.showwarning(
                    "No fixed position set",
                    "Choose 'Set to cursor' first, or switch to 'Current cursor'."
                )
                return False
        else:
            self.clicker.fixed_pos = None

        try:
            limit = int(self.limit_var.get())
        except ValueError:
            limit = 0
        self.clicker.click_limit = max(0, limit)

        return True

    def toggle(self):
        if self.clicker.running:
            self.clicker.stop()
        else:
            if not self._read_settings():
                return
            self.clicker.start()

    def _read_presser_settings(self):
        key = parse_key(self.key_var.get())
        if key is None:
            messagebox.showwarning(
                "Invalid key",
                "Type a single character (e.g. 'a', '5') or a recognized key name "
                "(e.g. space, enter, tab, esc, shift, ctrl, alt, up/down/left/right, f1-f12)."
            )
            return False
        self.presser.key = key
        self.presser.continuous = (self.press_mode.get() == "continuous")

        try:
            pps = float(self.pps_var.get())
        except ValueError:
            pps = 10.0
        self.presser.pps = max(0.1, min(pps, 500.0))

        try:
            limit = int(self.press_limit_var.get())
        except ValueError:
            limit = 0
        self.presser.press_limit = max(0, limit)

        return True

    def _on_press_mode_change(self, *_args):
        # PPS and press-limit only apply in repeated mode; disable them
        # visually when continuous (hold) mode is selected.
        continuous = self.press_mode.get() == "continuous"
        state = "disabled" if continuous else "normal"
        self.pps_entry.config(state=state)
        self.press_limit_entry.config(state=state)

    def toggle_presser(self):
        if self.presser.running:
            self.presser.stop()
        else:
            if not self._read_presser_settings():
                return
            self.presser.start()

    def emergency_stop(self):
        self.clicker.stop()
        self.presser.stop()

    def _update_loop(self):
        if self.clicker.running:
            self.status_var.set(f"RUNNING @ {self.clicker.cps:.1f} CPS")
            self.status_icon.config(text="●", fg=RUNNING_COLOR)
            self.status_label.config(fg=RUNNING_COLOR)
            self.toggle_btn.config(text="■  STOP  (F6)", bg=RUNNING_COLOR)
        else:
            self.status_var.set("STOPPED")
            self.status_icon.config(text="■", fg=STOPPED_COLOR)
            self.status_label.config(fg=STOPPED_COLOR)
            self.toggle_btn.config(text="▶  START  (F6)", bg=ACCENT)
        self.count_var.set(f"clicks: {self.clicker.click_count}")

        if self.presser.running:
            if self.presser.continuous:
                self.key_status_var.set("HOLDING KEY DOWN")
            else:
                self.key_status_var.set(f"RUNNING @ {self.presser.pps:.1f} PPS")
            self.key_status_icon.config(text="●", fg=RUNNING_COLOR)
            self.key_status_label.config(fg=RUNNING_COLOR)
            self.key_toggle_btn.config(text="■  STOP  (F7)", bg=RUNNING_COLOR)
        else:
            self.key_status_var.set("STOPPED")
            self.key_status_icon.config(text="■", fg=STOPPED_COLOR)
            self.key_status_label.config(fg=STOPPED_COLOR)
            self.key_toggle_btn.config(text="▶  START  (F7)", bg=ACCENT)
        self.key_count_var.set(f"presses: {self.presser.press_count}")

        self.root.after(100, self._update_loop)

    def on_close(self):
        self.clicker.stop()
        self.presser.stop()
        self.hotkey_listener.stop()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
