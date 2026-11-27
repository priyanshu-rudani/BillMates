"""
UI/dashboard/charts.py
----------------------
Matplotlib-powered chart panels embedded cleanly inside RoundedCard containers:
- RevenueExpensesChartCard (7D / 30D / 90D pill filters, dual area/line plot, hover tooltip)
- ExpenseDistributionCard (period dropdown pill, donut chart with center callout & 2-col legend)
"""

import os
import sys
import tempfile
import tkinter as tk
from typing import Callable, List, Optional, Tuple

if getattr(sys, "frozen", False) and "MPLCONFIGDIR" not in os.environ:
    _mpl_dir = os.path.join(tempfile.gettempdir(), "billmates_mplconfig")
    os.makedirs(_mpl_dir, exist_ok=True)
    os.environ["MPLCONFIGDIR"] = _mpl_dir

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.ticker import FuncFormatter

from UI.dashboard.graphics import RoundedCard, create_rounded_rect_image, render_vector_icon
from UI.dashboard.theme import THEME, get_font

matplotlib.rcParams["axes.unicode_minus"] = False


def _format_k(val: float, _pos: int) -> str:
    if val == 0:
        return "0"
    if abs(val) >= 1000:
        num = val / 1000.0
        return f"{int(num)}k" if abs(num - round(num)) < 0.05 else f"{num:.1f}k"
    return f"{int(val)}"


class _SegmentedPill(tk.Canvas):
    """Compact segmented pill selector (e.g. 7D | 30D | 90D)."""

    def __init__(
        self,
        master: tk.Misc,
        options: List[Tuple[str, int]],
        selected_value: int,
        on_change: Callable[[int], None],
    ):
        c = THEME["colors"]
        self.options = options
        self.selected_value = selected_value
        self.on_change = on_change
        self._btn_w = 44
        self._h = 28
        total_w = self._btn_w * len(options) + 6

        super().__init__(
            master,
            width=total_w,
            height=self._h,
            bg=c["card_bg"],
            highlightthickness=0,
            bd=0,
            cursor="hand2",
        )
        self._photos: List[object] = []
        self.bind("<Button-1>", self._on_click)
        self._draw()

    def _on_click(self, event: tk.Event) -> None:
        idx = max(0, min(len(self.options) - 1, (event.x - 3) // self._btn_w))
        val = self.options[idx][1]
        if val != self.selected_value:
            self.selected_value = val
            self._draw()
            self.on_change(val)

    def _draw(self) -> None:
        c = THEME["colors"]
        self.delete("all")
        self._photos.clear()
        w = int(self["width"])
        h = self._h

        track = create_rounded_rect_image(w, h, radius=14, fill=c["tile_bg"], bg_color=c["card_bg"])
        self._photos.append(track)
        self.create_image(0, 0, image=track, anchor="nw")

        for idx, (label, val) in enumerate(self.options):
            x0 = 3 + idx * self._btn_w
            is_active = val == self.selected_value
            if is_active:
                pill = create_rounded_rect_image(
                    self._btn_w, h - 4, radius=12, fill=c["primary"], bg_color=c["tile_bg"]
                )
                self._photos.append(pill)
                self.create_image(x0, 2, image=pill, anchor="nw")
                fg = c["white"]
                fnt = get_font("small_bold")
            else:
                fg = c["text_secondary"]
                fnt = get_font("small")
            self.create_text(x0 + self._btn_w // 2, h // 2, text=label, fill=fg, font=fnt)


class RevenueExpensesChartCard(RoundedCard):
    """Left chart card: Revenue & Expenses Overview with 7D / 30D / 90D selector."""

    def __init__(
        self,
        master: tk.Misc,
        fetch_series: Callable[[int], Tuple[List[str], List[float], List[float]]],
        on_open_reports: Optional[Callable[[], None]] = None,
        height: int = 330,
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
        self.fetch_series = fetch_series
        self.on_open_reports = on_open_reports
        self._days = 7
        self._labels: List[str] = []
        self._revenue: List[float] = []
        self._expenses: List[float] = []

        self.body.grid_rowconfigure(2, weight=1)
        self.body.grid_columnconfigure(0, weight=1)

        self._build_header()
        self._build_legend()
        self._build_plot()

    def _build_header(self) -> None:
        c = THEME["colors"]
        hdr = tk.Frame(self.body, bg=c["card_bg"])
        hdr.grid(row=0, column=0, sticky="ew")

        self._icon = render_vector_icon("reports", size=24, color=c["white"], bg_circle=c["purple_icon"])
        tk.Label(hdr, image=self._icon, bg=c["card_bg"]).pack(side="left", padx=(0, 8))
        tk.Label(
            hdr,
            text="Revenue & Expenses Overview",
            bg=c["card_bg"],
            fg=c["text_primary"],
            font=get_font("section_title"),
        ).pack(side="left")

        right = tk.Frame(hdr, bg=c["card_bg"])
        right.pack(side="right")

        self._seg = _SegmentedPill(
            right,
            options=[("7D", 7), ("30D", 30), ("90D", 90)],
            selected_value=self._days,
            on_change=self._on_range_change,
        )
        self._seg.pack(side="left", padx=(0, 8))

        self._cal_icon = render_vector_icon("calendar", size=16, color=c["text_secondary"])
        cal_btn = tk.Canvas(right, width=28, height=28, bg=c["card_bg"], highlightthickness=0, bd=0, cursor="hand2")
        cal_btn.pack(side="left")
        cal_bg = create_rounded_rect_image(
            28, 28, radius=8, fill=c["tile_bg"], border_color=c["card_border"], border_width=1, bg_color=c["card_bg"]
        )
        cal_btn._bg = cal_bg
        cal_btn.create_image(0, 0, image=cal_bg, anchor="nw")
        cal_btn.create_image(14, 14, image=self._cal_icon, anchor="center")
        if self.on_open_reports:
            cal_btn.bind("<Button-1>", lambda _e: self.on_open_reports())

    def _build_legend(self) -> None:
        c = THEME["colors"]
        leg = tk.Frame(self.body, bg=c["card_bg"])
        leg.grid(row=1, column=0, pady=(6, 0))

        for label, color in [("Revenue", c["chart_revenue"]), ("Expenses", c["chart_expense"])]:
            dot = tk.Canvas(leg, width=10, height=10, bg=c["card_bg"], highlightthickness=0, bd=0)
            dot.pack(side="left", padx=(10, 4))
            dot.create_oval(1, 1, 9, 9, fill=color, outline="")
            tk.Label(
                leg,
                text=label,
                bg=c["card_bg"],
                fg=c["text_secondary"],
                font=get_font("small"),
            ).pack(side="left", padx=(0, 8))

    def _build_plot(self) -> None:
        c = THEME["colors"]
        self.fig = Figure(figsize=(5.2, 2.65), facecolor=c["card_bg"], dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.fig.subplots_adjust(left=0.10, right=0.96, top=0.92, bottom=0.18)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.body)
        widget = self.canvas.get_tk_widget()
        widget.configure(bg=c["card_bg"], highlightthickness=0, bd=0)
        widget.grid(row=2, column=0, sticky="nsew", pady=(2, 0))

        self._annot = None
        self.canvas.mpl_connect("motion_notify_event", self._on_hover)

    def _on_range_change(self, days: int) -> None:
        self._days = days
        self.refresh()

    def refresh(self, preloaded: Optional[Tuple[List[str], List[float], List[float]]] = None) -> None:
        if preloaded is not None:
            self._labels, self._revenue, self._expenses = preloaded
        else:
            self._labels, self._revenue, self._expenses = self.fetch_series(self._days)
        self._render()

    def _render(self) -> None:
        c = THEME["colors"]
        ax = self.ax
        ax.clear()
        ax.set_facecolor(c["card_bg"])

        if not self._labels:
            ax.text(
                0.5, 0.5,
                "No trend data available",
                ha="center", va="center",
                color=c["text_muted"], fontsize=10,
                transform=ax.transAxes,
            )
            ax.set_xticks([])
            ax.set_yticks([])
            for sp in ax.spines.values():
                sp.set_visible(False)
            self.canvas.draw_idle()
            return

        x = list(range(len(self._labels)))
        rev = self._revenue
        exp = self._expenses
        peak = max(max(rev, default=0.0), max(exp, default=0.0))

        ax.fill_between(x, rev, 0, color=c["chart_revenue_fill"], alpha=0.12)
        ax.fill_between(x, exp, 0, color=c["chart_expense_fill"], alpha=0.10)

        ax.plot(
            x, rev,
            marker="o", markersize=5.5, linewidth=2.0,
            color=c["chart_revenue"], label="Revenue", zorder=4,
        )
        ax.plot(
            x, exp,
            marker="s", markersize=5.0, linewidth=1.8, linestyle="--",
            color=c["chart_expense"], label="Expenses", zorder=4,
        )

        ax.set_xticks(x)
        ax.set_xticklabels(self._labels, fontsize=8.5, color=c["chart_axis"])

        upper = peak * 1.15 if peak > 0 else 1000
        ax.set_ylim(bottom=0, top=upper)
        ax.yaxis.set_major_formatter(FuncFormatter(_format_k))
        ax.tick_params(axis="y", colors=c["chart_axis"], labelsize=8.5, length=0)
        ax.tick_params(axis="x", colors=c["chart_axis"], labelsize=8.5, length=0, pad=6)

        ax.grid(True, axis="both", color=c["chart_grid"], linestyle="-", linewidth=0.8, zorder=0)
        for side in ("top", "right", "left"):
            ax.spines[side].set_visible(False)
        ax.spines["bottom"].set_color("#E2E8F0")
        ax.spines["bottom"].set_linewidth(0.8)

        if peak == 0:
            ax.text(
                0.5, 0.55,
                f"No revenue or expense payments in the last {self._days} days",
                ha="center", va="center",
                color=c["text_light"], fontsize=9.5,
                transform=ax.transAxes,
            )

        self._annot = ax.annotate(
            "",
            xy=(0, 0),
            xytext=(10, 12),
            textcoords="offset points",
            bbox=dict(boxstyle="round,pad=0.4", fc="#1E293B", ec="none", alpha=0.92),
            color="#FFFFFF",
            fontsize=8,
            zorder=10,
        )
        self._annot.set_visible(False)
        self.canvas.draw_idle()

    def _on_hover(self, event) -> None:
        if self._annot is None or event.inaxes != self.ax or not self._labels:
            if self._annot is not None and self._annot.get_visible():
                self._annot.set_visible(False)
                self.canvas.draw_idle()
            return
        idx = int(round(event.xdata)) if event.xdata is not None else -1
        if 0 <= idx < len(self._labels):
            r_val = self._revenue[idx]
            e_val = self._expenses[idx]
            self._annot.xy = (idx, max(r_val, e_val))
            # Flip tooltip left near the right edge so it never gets clipped
            offset_x = -95 if idx >= max(1, len(self._labels) - 2) else 10
            self._annot.set_position((offset_x, 12))
            self._annot.set_text(f"{self._labels[idx]}\nRev: {r_val:,.0f}  |  Exp: {e_val:,.0f}")
            self._annot.set_visible(True)
            self.canvas.draw_idle()


class ExpenseDistributionCard(RoundedCard):
    """Right chart card: Expense Distribution Donut Chart with period dropdown and 2-col legend."""

    PERIODS = ["This Month", "This Quarter", "Financial Year", "All Time"]

    def __init__(
        self,
        master: tk.Misc,
        fetch_distribution: Callable[[str], Tuple[List[str], List[float]]],
        height: int = 330,
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
        self.fetch_distribution = fetch_distribution
        self._period = "This Month"
        self._labels: List[str] = []
        self._values: List[float] = []

        self.body.grid_rowconfigure(1, weight=1)
        self.body.grid_rowconfigure(2, weight=0)
        self.body.grid_columnconfigure(0, weight=1)

        self._build_header()
        self._build_donut()
        self._legend_frame = tk.Frame(self.body, bg=c["card_bg"])
        self._legend_frame.grid(row=2, column=0, sticky="ew", pady=(4, 2))

    def _build_header(self) -> None:
        c = THEME["colors"]
        hdr = tk.Frame(self.body, bg=c["card_bg"])
        hdr.grid(row=0, column=0, sticky="ew")

        self._icon = render_vector_icon("pie", size=24, color=c["white"], bg_circle=c["purple_icon"])
        tk.Label(hdr, image=self._icon, bg=c["card_bg"]).pack(side="left", padx=(0, 8))
        tk.Label(
            hdr,
            text="Expense Distribution",
            bg=c["card_bg"],
            fg=c["text_primary"],
            font=get_font("section_title"),
        ).pack(side="left")

        self._drop_canvas = tk.Canvas(hdr, width=114, height=28, bg=c["card_bg"], highlightthickness=0, bd=0, cursor="hand2")
        self._drop_canvas.pack(side="right")
        self._draw_dropdown_pill()

        menu = tk.Menu(
            self,
            tearoff=0,
            bg=c["white"],
            fg=c["text_primary"],
            activebackground=c["primary_light"],
            activeforeground=c["primary_dark"],
            font=get_font("small"),
        )
        for p in self.PERIODS:
            menu.add_command(label=f"  {p}  ", command=lambda val=p: self._set_period(val))

        def _open_menu(_e=None):
            x = self._drop_canvas.winfo_rootx()
            y = self._drop_canvas.winfo_rooty() + self._drop_canvas.winfo_height() + 4
            try:
                menu.tk_popup(x, y)
            finally:
                menu.grab_release()

        self._drop_canvas.bind("<Button-1>", _open_menu)

    def _draw_dropdown_pill(self) -> None:
        c = THEME["colors"]
        self._drop_canvas.delete("all")
        self._drop_bg = create_rounded_rect_image(
            114, 28, radius=14,
            fill=c["tile_bg"],
            border_color=c["card_border"],
            border_width=1,
            bg_color=c["card_bg"],
        )
        self._drop_canvas.create_image(0, 0, image=self._drop_bg, anchor="nw")
        self._drop_canvas.create_text(52, 14, text=self._period, fill=c["text_primary"], font=get_font("small_bold"))
        self._drop_canvas.create_text(101, 13, text="⌄", fill=c["text_muted"], font=get_font("small_bold"))

    def _set_period(self, period: str) -> None:
        self._period = period
        self._draw_dropdown_pill()
        self.refresh()

    def _build_donut(self) -> None:
        c = THEME["colors"]
        self.fig = Figure(figsize=(3.5, 2.45), facecolor=c["card_bg"], dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.fig.subplots_adjust(left=0.04, right=0.96, top=0.96, bottom=0.04)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.body)
        widget = self.canvas.get_tk_widget()
        widget.configure(bg=c["card_bg"], highlightthickness=0, bd=0)
        widget.grid(row=1, column=0, sticky="nsew")

    def refresh(self, preloaded: Optional[Tuple[List[str], List[float]]] = None) -> None:
        if preloaded is not None:
            self._labels, self._values = preloaded
        else:
            self._labels, self._values = self.fetch_distribution(self._period)
        self._render()
        self._render_legend()

    def _render(self) -> None:
        c = THEME["colors"]
        ax = self.ax
        ax.clear()
        ax.set_facecolor(c["card_bg"])

        if not self._values or sum(self._values) <= 0:
            ax.pie(
                [1],
                colors=["#EEF1F8"],
                radius=0.92,
                wedgeprops=dict(width=0.38, edgecolor="white", linewidth=2),
            )
            ax.text(0, 0.06, "0%", ha="center", va="center", fontsize=14, fontweight="bold", color=c["text_primary"])
            ax.text(0, -0.14, "No Expenses", ha="center", va="center", fontsize=8.5, color=c["text_muted"])
            ax.set(aspect="equal")
            self.canvas.draw_idle()
            return

        palette = c["donut_palette"]
        colors = [palette[i % len(palette)] for i in range(len(self._values))]
        total = sum(self._values)
        top_idx = max(range(len(self._values)), key=lambda i: self._values[i])
        top_pct = (self._values[top_idx] / total) * 100.0
        top_lbl = self._labels[top_idx]

        def _autopct(pct: float) -> str:
            return f"{pct:.1f}%" if pct >= 4.2 else ""

        _wedges, _texts, autotexts = ax.pie(
            self._values,
            colors=colors,
            radius=0.96,
            startangle=145,
            counterclock=True,
            autopct=_autopct,
            pctdistance=0.77,
            wedgeprops=dict(width=0.40, edgecolor="white", linewidth=2.2),
            textprops=dict(color="white", fontsize=8, fontweight="bold"),
        )
        for at in autotexts:
            at.set_color("white")

        ax.text(0, 0.07, f"{top_pct:.1f}%", ha="center", va="center", fontsize=14, fontweight="bold", color=c["text_primary"])
        ax.text(0, -0.13, top_lbl[:18], ha="center", va="center", fontsize=8, color=c["text_muted"])
        ax.set(aspect="equal")
        self.canvas.draw_idle()

    def _render_legend(self) -> None:
        c = THEME["colors"]
        for child in self._legend_frame.winfo_children():
            child.destroy()

        if not self._labels:
            tk.Label(
                self._legend_frame,
                text="No expense categories recorded for this period.",
                bg=c["card_bg"],
                fg=c["text_muted"],
                font=get_font("small"),
            ).pack(pady=6)
            return

        palette = c["donut_palette"]
        self._legend_frame.grid_columnconfigure(0, weight=1)
        self._legend_frame.grid_columnconfigure(1, weight=1)

        for idx, lbl in enumerate(self._labels):
            col = idx % 2
            row = idx // 2
            item = tk.Frame(self._legend_frame, bg=c["card_bg"])
            item.grid(row=row, column=col, sticky="w", padx=10, pady=2)

            dot = tk.Canvas(item, width=10, height=10, bg=c["card_bg"], highlightthickness=0, bd=0)
            dot.pack(side="left", padx=(0, 6))
            dot.create_oval(1, 1, 9, 9, fill=palette[idx % len(palette)], outline="")

            tk.Label(
                item,
                text=lbl,
                bg=c["card_bg"],
                fg=c["text_secondary"],
                font=get_font("small"),
            ).pack(side="left")
