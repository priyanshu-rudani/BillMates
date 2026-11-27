"""
UI/dashboard/widgets.py
-----------------------
Reusable visual widgets for the dashboard overview:
- WelcomeBanner (hero gradient card + Invoice/Calculator/Plant illustration)
- KpiSummaryCard (pastel icon badge, top-right trend pill, auto-fit metric value)
- QuickActionsCard (4 soft-indigo action tiles)
- RecentActivitiesCard (activity feed with colored dots + View All link)
- GrowthPromoCard (rich purple gradient card showing sales % vs last month)
"""

import tkinter as tk
import tkinter.font as tkfont
from datetime import date
from typing import Any, Callable, Dict, List, Optional

from UI.dashboard.graphics import (
    RoundedCard,
    create_rounded_rect_image,
    render_banner_illustration,
    render_growth_chart_graphic,
    render_vector_icon,
)
from UI.dashboard.theme import THEME, get_font


class WelcomeBanner(tk.Canvas):
    """Hero welcome banner with horizontal lavender gradient and crisp illustration."""

    def __init__(
        self,
        master: tk.Misc,
        company_name: str,
        fy_label: str = "",
        height: int = 118,
        **kwargs,
    ):
        c = THEME["colors"]
        super().__init__(
            master,
            height=height,
            bg=c["app_bg"],
            highlightthickness=0,
            bd=0,
            **kwargs,
        )
        self._company_name = company_name
        self._fy_label = fy_label
        self._bg_photo = None
        self._illustration = render_banner_illustration(210, 102)
        self._last_size = (0, 0)
        self.bind("<Configure>", self._redraw)

    def set_context(self, company_name: str, fy_label: str) -> None:
        if company_name != self._company_name or fy_label != self._fy_label:
            self._company_name = company_name
            self._fy_label = fy_label
            self._last_size = (0, 0)
            self._redraw()

    def _redraw(self, _event=None) -> None:
        w = self.winfo_width()
        h = self.winfo_height()
        if w < 40 or h < 40 or (w, h) == self._last_size:
            return
        self._last_size = (w, h)
        c = THEME["colors"]

        self.delete("all")
        self._bg_photo = create_rounded_rect_image(
            w, h,
            radius=THEME["radii"]["banner"],
            fill=c["banner_start"],
            gradient_end=c["banner_end"],
            corner_wave_color="#A399F5",
            border_color="#DFE2F8",
            border_width=1,
            bg_color=c["app_bg"],
        )
        self.create_image(0, 0, image=self._bg_photo, anchor="nw")

        left_x = 26
        month_label = date.today().strftime("%B %Y")
        fy_suffix = f"  •  FY {self._fy_label}" if self._fy_label else ""

        self.create_text(
            left_x, int(h * 0.23),
            text="Welcome back,",
            fill=c["text_secondary"],
            font=get_font("banner_greet"),
            anchor="w",
        )
        self.create_text(
            left_x, int(h * 0.50),
            text=f"{self._company_name}!",
            fill=c["text_primary"],
            font=get_font("banner_title"),
            anchor="w",
        )
        self.create_text(
            left_x, int(h * 0.74),
            text=f"Here's your business overview for {month_label}{fy_suffix}.",
            fill=c["text_muted"],
            font=get_font("banner_sub"),
            anchor="w",
        )
        self.create_rectangle(
            left_x, int(h * 0.88),
            left_x + 32, int(h * 0.88) + 3,
            fill=c["purple_icon"],
            outline="",
        )

        self.create_image(w - 20, h // 2 + 2, image=self._illustration, anchor="e")


class KpiSummaryCard(RoundedCard):
    """Reusable KPI summary card with pastel circular badge, top-right trend pill, and auto-fit metric value."""

    def __init__(
        self,
        master: tk.Misc,
        title: str,
        value: str,
        icon_name: str,
        icon_fg: str,
        icon_bg: str,
        value_color: str,
        wave_color: str,
        trend_pct: Optional[float] = None,
        show_calendar: bool = False,
        height: int = 138,
    ):
        c = THEME["colors"]
        super().__init__(
            master,
            parent_bg=c["app_bg"],
            fill=c["card_bg"],
            border_color=c["card_border"],
            shadow_color=c["card_shadow"],
            corner_wave_color=wave_color,
            radius=THEME["radii"]["card"],
            pad_x=14,
            pad_y=11,
            height=height,
        )
        self._value_color = value_color
        self._show_calendar = show_calendar
        self._base_font_family, self._base_font_size = get_font("kpi_value")
        self._value_text = str(value)

        self.body.grid_columnconfigure(0, weight=1)
        self.body.grid_columnconfigure(1, weight=0)
        self.body.grid_rowconfigure(0, weight=0)
        self.body.grid_rowconfigure(1, weight=0)
        self.body.grid_rowconfigure(2, weight=1)

        # Row 0: Icon badge (left) + Trend pill or Calendar icon (right)
        self._icon = render_vector_icon(icon_name, size=30, color=icon_fg, bg_circle=icon_bg)
        tk.Label(self.body, image=self._icon, bg=c["card_bg"]).grid(
            row=0, column=0, sticky="w", pady=(0, 4)
        )

        self._right_container = tk.Frame(self.body, bg=c["card_bg"])
        self._right_container.grid(row=0, column=1, sticky="ne", pady=(3, 4))

        if show_calendar:
            self._cal_icon = render_vector_icon("calendar", size=17, color=c["text_muted"])
            tk.Label(self._right_container, image=self._cal_icon, bg=c["card_bg"]).pack()
        else:
            self._trend_canvas = tk.Canvas(
                self._right_container,
                width=64,
                height=22,
                bg=c["card_bg"],
                highlightthickness=0,
                bd=0,
            )
            self._trend_canvas.pack()
            self.set_trend(trend_pct)

        # Row 1: Metric title spanning full card width
        self.title_lbl = tk.Label(
            self.body,
            text=title,
            bg=c["card_bg"],
            fg=c["text_muted"],
            font=get_font("card_label"),
            anchor="w",
        )
        self.title_lbl.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(2, 2))

        # Row 2: Metric value spanning full card width with auto-fit font scaling
        self.value_lbl = tk.Label(
            self.body,
            text=self._value_text,
            bg=c["card_bg"],
            fg=value_color,
            font=(self._base_font_family, self._base_font_size),
            anchor="w",
            padx=0,
            pady=0,
        )
        self.value_lbl.grid(row=2, column=0, columnspan=2, sticky="nsew", pady=0)
        self.body.bind("<Configure>", lambda _e: self._fit_value_font(), add="+")
        self.after_idle(self._fit_value_font)

    def _fit_value_font(self) -> None:
        bw = self.body.winfo_width()
        if bw <= 20:
            bw = max(110, self.winfo_width() - 2 * self.pad_x)
        avail_w = max(60, bw - 8)
        text = self._value_text or "0"
        chosen_size = self._base_font_size
        for size in range(self._base_font_size, 7, -1):
            fnt = tkfont.Font(family=self._base_font_family, size=size)
            if fnt.measure(text) <= avail_w:
                chosen_size = size
                break
            chosen_size = size
        self.value_lbl.configure(font=(self._base_font_family, chosen_size))

    def update_metric(
        self,
        formatted_value: str,
        value_color: Optional[str] = None,
        trend_pct: Optional[float] = None,
    ) -> None:
        self._value_text = str(formatted_value)
        self.value_lbl.configure(
            text=self._value_text,
            fg=value_color or self._value_color,
        )
        self._fit_value_font()
        if not self._show_calendar:
            self.set_trend(trend_pct)

    def set_trend(self, trend_pct: Optional[float]) -> None:
        if self._show_calendar:
            return
        c = THEME["colors"]
        self._trend_canvas.delete("all")
        if trend_pct is None:
            pill_bg = c["tile_bg"]
            pill_fg = c["text_muted"]
            label = "This FY"
        elif trend_pct > 0:
            pill_bg = c["success_bg"]
            pill_fg = c["success"]
            label = f"↑ {min(999.9, abs(trend_pct)):.1f}%"
        elif trend_pct < 0:
            pill_bg = c["danger_bg"]
            pill_fg = c["danger"]
            label = f"↓ {min(999.9, abs(trend_pct)):.1f}%"
        else:
            pill_bg = c["tile_bg"]
            pill_fg = c["text_muted"]
            label = "0.0%"

        self._pill_img = create_rounded_rect_image(
            64, 22, radius=11, fill=pill_bg, bg_color=c["card_bg"]
        )
        self._trend_canvas.create_image(0, 0, image=self._pill_img, anchor="nw")
        self._trend_canvas.create_text(32, 11, text=label, fill=pill_fg, font=get_font("badge"))


class QuickActionsCard(RoundedCard):
    """Bottom-left card featuring 4 rounded square quick-action tiles."""

    def __init__(
        self,
        master: tk.Misc,
        actions: List[tuple],
        height: int = 162,
    ):
        c = THEME["colors"]
        super().__init__(
            master,
            parent_bg=c["app_bg"],
            fill=c["card_bg"],
            border_color=c["card_border"],
            shadow_color=c["card_shadow"],
            radius=THEME["radii"]["card"],
            pad_x=18,
            pad_y=14,
            height=height,
        )
        self._tile_icons: List[Any] = []

        hdr = tk.Frame(self.body, bg=c["card_bg"])
        hdr.pack(fill="x", pady=(0, 10))

        self._bolt_icon = render_vector_icon("bolt", size=16, color=c["purple_icon"])
        tk.Label(hdr, image=self._bolt_icon, bg=c["card_bg"]).pack(side="left", padx=(0, 6))
        tk.Label(
            hdr,
            text="Quick Actions",
            bg=c["card_bg"],
            fg=c["text_primary"],
            font=get_font("section_title"),
        ).pack(side="left")

        grid = tk.Frame(self.body, bg=c["card_bg"])
        grid.pack(fill="both", expand=True)
        for idx in range(len(actions)):
            grid.grid_columnconfigure(idx, weight=1, uniform="qa_tile")
        grid.grid_rowconfigure(0, weight=1)

        for idx, (label, icon_name, cmd) in enumerate(actions):
            tile = self._make_tile(grid, label, icon_name, cmd)
            tile.grid(
                row=0,
                column=idx,
                sticky="nsew",
                padx=(0 if idx == 0 else 5, 0 if idx == len(actions) - 1 else 5),
            )

    def _make_tile(self, parent: tk.Misc, label: str, icon_name: str, cmd: Callable[[], None]) -> tk.Canvas:
        c = THEME["colors"]
        tile = tk.Canvas(parent, bg=c["card_bg"], highlightthickness=0, bd=0, cursor="hand2")
        icon = render_vector_icon(icon_name, size=20, color=c["purple_icon"])
        self._tile_icons.append(icon)
        tile._hovered = False

        def _draw(_e=None):
            w = tile.winfo_width()
            h = tile.winfo_height()
            if w < 20 or h < 20:
                return
            tile.delete("all")
            bg_fill = c["tile_hover"] if tile._hovered else c["tile_bg"]
            tile._bg = create_rounded_rect_image(
                w, h, radius=THEME["radii"]["tile"], fill=bg_fill, bg_color=c["card_bg"]
            )
            tile.create_image(0, 0, image=tile._bg, anchor="nw")
            tile.create_image(w // 2, int(h * 0.32), image=icon, anchor="center")
            tile.create_text(
                w // 2, int(h * 0.70),
                text=label,
                fill=c["text_primary"],
                font=get_font("small_bold"),
                justify="center",
            )

        def _enter(_e=None):
            tile._hovered = True
            _draw()

        def _leave(_e=None):
            tile._hovered = False
            _draw()

        tile.bind("<Configure>", _draw)
        tile.bind("<Enter>", _enter)
        tile.bind("<Leave>", _leave)
        tile.bind("<Button-1>", lambda _e: cmd())
        return tile


class RecentActivitiesCard(RoundedCard):
    """Bottom-middle card displaying recent live billing events and a 'View All ->' link."""

    def __init__(
        self,
        master: tk.Misc,
        height: int = 162,
    ):
        c = THEME["colors"]
        super().__init__(
            master,
            parent_bg=c["app_bg"],
            fill=c["card_bg"],
            border_color=c["card_border"],
            shadow_color=c["card_shadow"],
            radius=THEME["radii"]["card"],
            pad_x=18,
            pad_y=14,
            height=height,
        )

        hdr = tk.Frame(self.body, bg=c["card_bg"])
        hdr.pack(fill="x", pady=(0, 8))

        self._clock_icon = render_vector_icon("clock", size=22, color=c["purple_icon"], bg_circle=c["purple_bg"])
        tk.Label(hdr, image=self._clock_icon, bg=c["card_bg"]).pack(side="left", padx=(0, 8))
        tk.Label(
            hdr,
            text="Recent Activities",
            bg=c["card_bg"],
            fg=c["text_primary"],
            font=get_font("section_title"),
        ).pack(side="left")

        self.list_frame = tk.Frame(self.body, bg=c["card_bg"])
        self.list_frame.pack(fill="both", expand=True)

    def set_activities(self, activities: List[Dict[str, Any]]) -> None:
        c = THEME["colors"]
        for child in self.list_frame.winfo_children():
            child.destroy()

        if not activities:
            tk.Label(
                self.list_frame,
                text="No recent billing activity recorded yet.\nUse Quick Actions to create an invoice or payment.",
                bg=c["card_bg"],
                fg=c["text_muted"],
                font=get_font("small"),
                justify="left",
            ).pack(anchor="w", pady=14)
            return

        for idx, act in enumerate(activities[:4]):
            row = tk.Frame(self.list_frame, bg=c["card_bg"])
            row.pack(fill="x", pady=(1 if idx == 0 else 3, 2))

            dot = tk.Canvas(row, width=10, height=10, bg=c["card_bg"], highlightthickness=0, bd=0)
            dot.pack(side="left", padx=(0, 8))
            dot.create_oval(1, 1, 9, 9, fill=act.get("color", c["success_bright"]), outline="")

            # Pack fixed-width timestamp BEFORE expanding title so timestamps are never clipped
            tk.Label(
                row,
                text=act.get("time", ""),
                bg=c["card_bg"],
                fg=c["text_light"],
                font=get_font("small"),
                anchor="e",
            ).pack(side="right", padx=(8, 0))

            raw_title = str(act.get("title", ""))
            short_title = raw_title if len(raw_title) <= 40 else raw_title[:37] + "..."
            tk.Label(
                row,
                text=short_title,
                bg=c["card_bg"],
                fg=c["text_primary"],
                font=get_font("small"),
                anchor="w",
            ).pack(side="left", fill="x", expand=True)


class GrowthPromoCard(tk.Canvas):
    """Bottom-right vibrant purple gradient card showing sales % change compared to last month."""

    def __init__(
        self,
        master: tk.Misc,
        height: int = 162,
        **kwargs,
    ):
        c = THEME["colors"]
        super().__init__(
            master,
            height=height,
            bg=c["app_bg"],
            highlightthickness=0,
            bd=0,
            **kwargs,
        )
        self._heading = "Business is Growing!"
        self._body_text = "Your sales increased by 0.0% compared to last month."
        self._bg_photo = None
        self._last_size = (0, 0)
        self._trophy_icon = render_vector_icon("trophy", size=24, color="#FBBF24")
        self._chart_graphic = render_growth_chart_graphic(90, 62)
        self.bind("<Configure>", self._redraw)

    def update_sales_growth(self, sales_pct: float) -> None:
        if sales_pct >= 0:
            self._heading = "Business is Growing!"
            self._body_text = f"Your sales increased by {sales_pct:.1f}% compared to last month."
        else:
            self._heading = "Monthly Sales Update"
            self._body_text = f"Your sales decreased by {abs(sales_pct):.1f}% compared to last month."
        self._last_size = (0, 0)
        self._redraw()

    def _redraw(self, _event=None) -> None:
        w = self.winfo_width()
        h = self.winfo_height()
        if w < 40 or h < 40 or (w, h) == self._last_size:
            return
        self._last_size = (w, h)
        c = THEME["colors"]

        self.delete("all")
        self._bg_photo = create_rounded_rect_image(
            w, h,
            radius=THEME["radii"]["card"],
            fill=c["growth_start"],
            gradient_end=c["growth_end"],
            corner_wave_color="#8B7DFF",
            bg_color=c["app_bg"],
        )
        self.create_image(0, 0, image=self._bg_photo, anchor="nw")

        self.create_oval(20, 26, 58, 64, fill="#6C63EA", outline="")
        self.create_image(39, 45, image=self._trophy_icon, anchor="center")

        self.create_text(
            72, 36,
            text=self._heading,
            fill=c["white"],
            font=get_font("section_title"),
            anchor="w",
        )
        text_w = max(120, w - 180)
        self.create_text(
            72, 68,
            text=self._body_text,
            fill="#E0E4FF",
            font=get_font("small"),
            width=text_w,
            anchor="nw",
        )

        self.create_image(w - 14, h - 14, image=self._chart_graphic, anchor="se")
