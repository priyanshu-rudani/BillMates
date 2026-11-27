"""
UI/dashboard/sidebar.py
-----------------------
Modern deep-indigo navigation sidebar with rounded pill active states,
submenu popups, and Logout button.
"""

import tkinter as tk
from typing import Any, Callable, Dict, List, Optional

from UI.dashboard.graphics import create_rounded_rect_image, render_vector_icon
from UI.dashboard.theme import THEME, get_font


class _SidebarNavButton(tk.Canvas):
    """Canvas-backed pill navigation button with anti-aliased rounded highlight."""

    def __init__(
        self,
        master: tk.Misc,
        text: str,
        icon_name: str,
        command: Callable[[tk.Widget], None],
        active: bool = False,
        height: int = 38,
    ):
        c = THEME["colors"]
        super().__init__(
            master,
            height=height,
            bg=c["sidebar_bg"],
            highlightthickness=0,
            bd=0,
            cursor="hand2",
        )
        self.text = text
        self.icon_name = icon_name
        self.command = command
        self._active = active
        self._hovered = False
        self._bg_photo = None
        self._icon = render_vector_icon(icon_name, size=17, color=c["white"])

        self.bind("<Configure>", self._redraw)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)

    def set_active(self, active: bool) -> None:
        if self._active != active:
            self._active = active
            self._redraw()

    def _on_enter(self, _event=None) -> None:
        self._hovered = True
        self._redraw()

    def _on_leave(self, _event=None) -> None:
        self._hovered = False
        self._redraw()

    def _on_click(self, _event=None) -> None:
        if self.command:
            self.command(self)

    def _redraw(self, _event=None) -> None:
        w = self.winfo_width()
        h = self.winfo_height()
        if w < 20 or h < 10:
            return

        c = THEME["colors"]
        self.delete("all")

        if self._active:
            self._bg_photo = create_rounded_rect_image(
                w, h, radius=10,
                fill=c["sidebar_active"],
                border_color=c["sidebar_active_border"],
                border_width=1,
                bg_color=c["sidebar_bg"],
            )
            self.create_image(0, 0, image=self._bg_photo, anchor="nw")
        elif self._hovered:
            self._bg_photo = create_rounded_rect_image(
                w, h, radius=10,
                fill=c["sidebar_hover"],
                bg_color=c["sidebar_bg"],
            )
            self.create_image(0, 0, image=self._bg_photo, anchor="nw")

        self.create_image(14, h // 2, image=self._icon, anchor="w")
        font = get_font("nav_active" if self._active else "nav")
        fg = c["white"] if self._active else c["sidebar_text"]
        self.create_text(42, h // 2, text=self.text, fill=fg, font=font, anchor="w")


class DashboardSidebar(tk.Frame):
    """Left navigation rail matching the Billing System dark-indigo sidebar."""

    def __init__(
        self,
        master: tk.Misc,
        menu_data: List[Dict[str, Any]],
        on_dashboard: Optional[Callable[[], None]] = None,
        **kwargs,
    ):
        c = THEME["colors"]
        width = THEME["spacing"]["sidebar_width"]
        super().__init__(master, width=width, bg=c["sidebar_bg"], **kwargs)
        self.pack_propagate(False)

        self.on_dashboard = on_dashboard
        self._nav_buttons: Dict[str, _SidebarNavButton] = {}
        self._active_key = "Dashboard"

        self._build_brand_header()
        self._build_navigation(menu_data)
        self._build_bottom_area(menu_data)

    def _build_brand_header(self) -> None:
        c = THEME["colors"]
        brand_frame = tk.Frame(self, bg=c["sidebar_bg"], height=60)
        brand_frame.pack(fill="x", padx=16, pady=(14, 10))
        brand_frame.pack_propagate(False)

        # self._brand_icon = render_vector_icon("brand_doc", size=23, color=c["white"])
        # tk.Label(brand_frame, image=self._brand_icon, bg=c["sidebar_bg"]).pack(side="left", padx=(2, 8))

        tk.Label(
            brand_frame,
            text="BillMates",
            bg=c["sidebar_bg"],
            fg=c["white"],
            font=get_font("brand"),
        ).pack(side="top")

    def _build_navigation(self, menu_data: List[Dict[str, Any]]) -> None:
        c = THEME["colors"]
        nav_frame = tk.Frame(self, bg=c["sidebar_bg"])
        nav_frame.pack(fill="x", padx=12, pady=(4, 8))

        dash_btn = _SidebarNavButton(
            nav_frame,
            text="Dashboard",
            icon_name="home",
            active=True,
            command=lambda _w: self._select_dashboard(),
        )
        dash_btn.pack(fill="x", pady=3)
        self._nav_buttons["Dashboard"] = dash_btn

        icon_map = {
            "Invoice": "invoice",
            "Clients": "clients",
            "Payments": "payments",
            "Expense": "expense",
            "Reports": "reports",
            "Cheques": "cheques",
            "Settings": "settings",
        }

        for item in menu_data:
            if item.get("pack_side") == "bottom":
                continue
            label = item.get("text", "")
            icon_name = icon_map.get(label, "invoice")
            commands = item.get("commands", [])
            single_cmd = item.get("single_command")

            if commands:
                dropdown = self._build_popup_menu(commands)
                action = lambda widget, m=dropdown, key=label: self._open_submenu(key, m, widget)
            else:
                action = lambda _w, cmd=single_cmd, key=label: self._trigger_single(key, cmd)

            btn = _SidebarNavButton(nav_frame, text=label, icon_name=icon_name, command=action)
            btn.pack(fill="x", pady=3)
            self._nav_buttons[label] = btn

    def _build_popup_menu(self, commands: List[Dict[str, Any]]) -> tk.Menu:
        c = THEME["colors"]
        menu = tk.Menu(
            self,
            tearoff=0,
            bg=c["white"],
            fg=c["text_primary"],
            activebackground=c["primary_light"],
            activeforeground=c["primary_dark"],
            font=get_font("body"),
            bd=0,
        )
        for cmd_data in commands:
            if cmd_data.get("type") == "separator":
                menu.add_separator()
            else:
                lbl = cmd_data.get("label")
                cmd = cmd_data.get("command")
                if lbl and cmd:
                    menu.add_command(label=f"  {lbl}  ", command=cmd)
        return menu

    def _select_dashboard(self) -> None:
        self.set_active("Dashboard")
        if self.on_dashboard:
            self.on_dashboard()

    def _open_submenu(self, key: str, menu: tk.Menu, widget: tk.Widget) -> None:
        self.set_active(key)
        x = widget.winfo_rootx() + widget.winfo_width() + 4
        y = widget.winfo_rooty()
        try:
            menu.tk_popup(x, y)
        finally:
            menu.grab_release()

    def _trigger_single(self, key: str, cmd: Optional[Callable[[], None]]) -> None:
        self.set_active(key)
        if cmd:
            cmd()

    def set_active(self, key: str) -> None:
        self._active_key = key
        for name, btn in self._nav_buttons.items():
            btn.set_active(name == key)

    def _build_bottom_area(self, menu_data: List[Dict[str, Any]]) -> None:
        c = THEME["colors"]
        bottom_wrap = tk.Frame(self, bg=c["sidebar_bg"])
        bottom_wrap.pack(side="bottom", fill="x", padx=12, pady=(4, 16))

        logout_cmd = None
        for item in menu_data:
            if item.get("pack_side") == "bottom":
                logout_cmd = item.get("single_command")
                break

        logout_btn = _SidebarNavButton(
            bottom_wrap,
            text="Logout",
            icon_name="logout",
            command=lambda _w: logout_cmd() if logout_cmd else None,
            height=38,
        )
        logout_btn.pack(fill="x")
