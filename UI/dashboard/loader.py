"""
UI/dashboard/loader.py
----------------------
Minimal, theme-matched splash loader displaying "BillMates Billing Software"
and a smooth animated progress bar, with built-in auto-close safety fallbacks.
"""

from __future__ import annotations

import math
import time
import tkinter as tk
from typing import Optional

from UI.dashboard.graphics import create_rounded_rect_image, render_vector_icon
from UI.dashboard.theme import THEME, get_font


class DashboardLoader(tk.Toplevel):
    """Centered splash loader with title and smooth animated progress bar."""

    WIDTH = 430
    HEIGHT = 172

    def __init__(self, master: tk.Misc, max_lifetime_ms: int = 15000):
        c = THEME["colors"]
        super().__init__(master)
        self.overrideredirect(True)
        self.configure(bg=c["sidebar_active_border"])
        try:
            self.attributes("-topmost", True)
        except tk.TclError:
            pass

        self._progress = 0.0
        self._pulse_phase = 0.0
        self._bar_fill_photo = None
        self._bar_track_photo = None
        self._watchdog_id: Optional[str] = None

        self._center_on_screen()
        self._build_ui()
        self.bind("<Escape>", lambda _e: self.close())
        self.protocol("WM_DELETE_WINDOW", self.close)

        if max_lifetime_ms > 0:
            self._watchdog_id = self.after(max_lifetime_ms, self.close)

        self.update_idletasks()
        self.deiconify()
        self.lift()
        self.update()

    def _center_on_screen(self) -> None:
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = max(0, (sw - self.WIDTH) // 2)
        y = max(0, (sh - self.HEIGHT) // 2 - 20)
        self.geometry(f"{self.WIDTH}x{self.HEIGHT}+{x}+{y}")

    def _build_ui(self) -> None:
        c = THEME["colors"]
        outer = tk.Frame(self, bg=c["sidebar_bg"], bd=0, highlightthickness=0)
        outer.pack(fill="both", expand=True, padx=1, pady=1)

        # Top theme accent stripe
        tk.Frame(outer, bg=c["primary"], height=4).pack(fill="x", side="top")

        body = tk.Frame(outer, bg=c["sidebar_bg"])
        body.pack(fill="both", expand=True, padx=32, pady=(26, 26))

        # Centered Title Row: Icon + "BillMates Billing Software"
        title_row = tk.Frame(body, bg=c["sidebar_bg"])
        title_row.pack(pady=(6, 26))

        self._brand_icon = render_vector_icon("brand_doc", size=26, color=c["white"])
        tk.Label(title_row, image=self._brand_icon, bg=c["sidebar_bg"]).pack(side="left", padx=(0, 10))
        tk.Label(
            title_row,
            text="BillMates Billing Software",
            bg=c["sidebar_bg"],
            fg=c["white"],
            font=get_font("brand", 2),
        ).pack(side="left")

        # Animated rounded progress bar
        self._bar_w = self.WIDTH - 66
        self._bar_h = 10
        self._bar_canvas = tk.Canvas(
            body,
            width=self._bar_w,
            height=self._bar_h,
            bg=c["sidebar_bg"],
            highlightthickness=0,
            bd=0,
        )
        self._bar_canvas.pack(fill="x")

        self._bar_track_photo = create_rounded_rect_image(
            self._bar_w, self._bar_h, radius=5, fill=c["sidebar_hover"], bg_color=c["sidebar_bg"]
        )
        self._bar_canvas.create_image(0, 0, image=self._bar_track_photo, anchor="nw")
        self._bar_fill_item = self._bar_canvas.create_image(0, 0, anchor="nw")

        self._draw_bar()

    def _draw_bar(self) -> None:
        if not self.winfo_exists():
            return
        c = THEME["colors"]
        pct = max(0.0, min(100.0, self._progress))
        fill_w = int((self._bar_w * pct) / 100.0)
        if fill_w >= 8:
            self._bar_fill_photo = create_rounded_rect_image(
                fill_w,
                self._bar_h,
                radius=5,
                fill=c["primary"],
                gradient_end=c["sidebar_active_border"],
                bg_color=c["sidebar_hover"],
            )
            self._bar_canvas.itemconfigure(self._bar_fill_item, image=self._bar_fill_photo)
        else:
            self._bar_canvas.itemconfigure(self._bar_fill_item, image="")

    def tick(self) -> None:
        """Advance progress animation smoothly and process pending Tk events."""
        if not self.winfo_exists():
            return
        self._pulse_phase = (self._pulse_phase + 0.25) % (2 * math.pi)
        self._draw_bar()
        self.update()

    def set_progress(self, target_pct: float, animate_ms: int = 90) -> None:
        """Smoothly animate progress bar to target_pct."""
        if not self.winfo_exists():
            return
        start_pct = self._progress
        steps = max(1, animate_ms // 16)
        for i in range(1, steps + 1):
            if not self.winfo_exists():
                return
            t = i / steps
            eased = 1 - math.pow(1 - t, 3)
            self._progress = start_pct + (target_pct - start_pct) * eased
            self.tick()
            if animate_ms > 0:
                time.sleep(0.015)

    def close(self) -> None:
        """Safely cancel watchdog and destroy loader window."""
        if self._watchdog_id is not None:
            try:
                self.after_cancel(self._watchdog_id)
            except Exception:
                pass
            self._watchdog_id = None
        if self.winfo_exists():
            try:
                self.attributes("-topmost", False)
            except tk.TclError:
                pass
            try:
                self.destroy()
            except Exception:
                pass
