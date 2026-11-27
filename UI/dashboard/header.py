"""
UI/dashboard/header.py
----------------------
Top navigation header bar with pill search bar (live entity search),
notification bell popover, and user/company profile pill.
"""

import tkinter as tk
from typing import Callable, List, Optional

from UI.dashboard.graphics import create_rounded_rect_image, render_vector_icon
from UI.dashboard.theme import THEME, get_font


def _company_initials(name: str) -> str:
    parts = [p for p in name.strip().split() if p]
    if not parts:
        return "BM"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[1][0]).upper()


class TopHeaderBar(tk.Frame):
    """White top header bar with search, notifications, and company profile menu."""

    def __init__(
        self,
        master: tk.Misc,
        company_name: str,
        on_search: Callable[[str], List[dict]],
        on_search_select: Callable[[dict], None],
        on_edit_company: Callable[[], None],
        on_backup: Callable[[], None],
        on_refresh: Callable[[], None],
        get_notifications: Callable[[], List[str]],
        **kwargs,
    ):
        c = THEME["colors"]
        super().__init__(master, bg=c["header_bg"], height=THEME["spacing"]["header_height"], **kwargs)
        self.pack_propagate(False)

        self.on_search = on_search
        self.on_search_select = on_search_select
        self.on_edit_company = on_edit_company
        self.on_backup = on_backup
        self.on_refresh = on_refresh
        self.get_notifications = get_notifications

        self._company_name = company_name
        self._search_popup: Optional[tk.Toplevel] = None
        self._notif_popup: Optional[tk.Toplevel] = None
        self._placeholder = "Search clients, invoices, actions..."
        self._has_placeholder = True

        row = tk.Frame(self, bg=c["header_bg"])
        row.pack(fill="both", expand=True, padx=24)

        tk.Frame(self, bg=c["header_border"], height=1).pack(side="bottom", fill="x")

        self._build_search_pill(row)
        self._build_right_controls(row)

    def _build_search_pill(self, parent: tk.Frame) -> None:
        c = THEME["colors"]
        self._search_canvas = tk.Canvas(
            parent,
            width=350,
            height=38,
            bg=c["header_bg"],
            highlightthickness=0,
            bd=0,
        )
        self._search_canvas.pack(side="left", pady=12)
        self._search_canvas.pack_propagate(False)

        def _draw_bg(_event=None):
            w = self._search_canvas.winfo_width()
            h = self._search_canvas.winfo_height()
            if w < 40:
                return
            self._search_canvas.delete("bg")
            self._search_bg = create_rounded_rect_image(
                w, h, radius=19,
                fill=c["search_bg"],
                border_color=c["search_border"],
                border_width=1,
                bg_color=c["header_bg"],
            )
            self._search_canvas.create_image(0, 0, image=self._search_bg, anchor="nw", tags="bg")
            self._search_canvas.tag_lower("bg")

        self._search_canvas.bind("<Configure>", _draw_bg)

        self._search_icon = render_vector_icon("search", size=15, color=c["text_muted"])
        self._search_canvas.create_image(18, 19, image=self._search_icon, anchor="center")

        self.search_entry = tk.Entry(
            self._search_canvas,
            bg=c["search_bg"],
            fg=c["text_light"],
            insertbackground=c["text_primary"],
            relief="flat",
            bd=0,
            font=get_font("body"),
        )
        self.search_entry.insert(0, self._placeholder)
        self._search_canvas.create_window(36, 19, anchor="w", width=298, height=24, window=self.search_entry)

        self.search_entry.bind("<FocusIn>", self._on_search_focus_in)
        self.search_entry.bind("<FocusOut>", self._on_search_focus_out)
        self.search_entry.bind("<KeyRelease>", self._on_search_key)
        self.search_entry.bind("<Return>", self._on_search_enter)
        self.search_entry.bind("<Escape>", lambda _e: self._close_search_popup())

    def _on_search_focus_in(self, _event=None) -> None:
        if self._has_placeholder:
            self.search_entry.delete(0, tk.END)
            self.search_entry.configure(fg=THEME["colors"]["text_primary"])
            self._has_placeholder = False

    def _on_search_focus_out(self, _event=None) -> None:
        if not self.search_entry.get().strip():
            self._has_placeholder = True
            self.search_entry.delete(0, tk.END)
            self.search_entry.insert(0, self._placeholder)
            self.search_entry.configure(fg=THEME["colors"]["text_light"])
        self.after(220, self._maybe_close_search_popup)

    def _maybe_close_search_popup(self) -> None:
        if self._search_popup and self._search_popup.winfo_exists():
            try:
                focused = self.focus_get()
                if focused is not None and focused.winfo_toplevel() == self._search_popup:
                    return
            except Exception:
                pass
            self._close_search_popup()

    def _on_search_key(self, event=None) -> None:
        if event and event.keysym == "Escape":
            self._close_search_popup()
            return
        if self._has_placeholder:
            return
        query = self.search_entry.get().strip()
        if not query:
            self._close_search_popup()
            return
        results = self.on_search(query)
        self._show_search_popup(results)

    def _on_search_enter(self, _event=None) -> None:
        if self._has_placeholder:
            return
        query = self.search_entry.get().strip()
        if not query:
            return
        results = self.on_search(query)
        if results:
            self._close_search_popup()
            self.on_search_select(results[0])

    def _show_search_popup(self, results: List[dict]) -> None:
        self._close_search_popup()
        c = THEME["colors"]
        popup = tk.Toplevel(self)
        popup.overrideredirect(True)
        popup.configure(bg=c["card_border"])
        self._search_popup = popup

        x = self._search_canvas.winfo_rootx()
        y = self._search_canvas.winfo_rooty() + self._search_canvas.winfo_height() + 4
        w = max(350, self._search_canvas.winfo_width())

        inner = tk.Frame(popup, bg=c["white"], padx=8, pady=6)
        inner.pack(fill="both", expand=True, padx=1, pady=1)

        if not results:
            tk.Label(
                inner,
                text="No matching clients, invoices, or commands.",
                bg=c["white"],
                fg=c["text_muted"],
                font=get_font("small"),
                pady=6,
            ).pack(anchor="w", padx=6)
        else:
            for item in results:
                row = tk.Frame(inner, bg=c["white"], cursor="hand2")
                row.pack(fill="x", pady=2)
                badge = tk.Label(
                    row,
                    text=item["kind"],
                    bg=c["primary_light"],
                    fg=c["primary_dark"],
                    font=get_font("small_bold"),
                    padx=6,
                    pady=2,
                )
                badge.pack(side="left", padx=(4, 8), pady=3)
                lbl = tk.Label(
                    row,
                    text=item["label"],
                    bg=c["white"],
                    fg=c["text_primary"],
                    font=get_font("body"),
                    anchor="w",
                )
                lbl.pack(side="left", fill="x", expand=True)

                def _pick(_e=None, payload=item):
                    self._close_search_popup()
                    self.on_search_select(payload)

                for wdg in (row, badge, lbl):
                    wdg.bind("<Button-1>", _pick)

        popup.update_idletasks()
        popup.geometry(f"{w}x{popup.winfo_reqheight()}+{x}+{y}")

    def _close_search_popup(self) -> None:
        if self._search_popup and self._search_popup.winfo_exists():
            self._search_popup.destroy()
        self._search_popup = None

    def _build_right_controls(self, parent: tk.Frame) -> None:
        c = THEME["colors"]
        right = tk.Frame(parent, bg=c["header_bg"])
        right.pack(side="right", pady=10)

        self._bell_icon = render_vector_icon("bell", size=20, color=c["text_primary"])
        self._bell_canvas = tk.Canvas(right, width=36, height=36, bg=c["header_bg"], highlightthickness=0, bd=0, cursor="hand2")
        self._bell_canvas.pack(side="left", padx=(0, 14))
        self._bell_canvas.create_image(18, 19, image=self._bell_icon)
        self._bell_dot = self._bell_canvas.create_oval(22, 6, 29, 13, fill=c["danger"], outline=c["white"], width=1)
        self._bell_canvas.bind("<Button-1>", lambda _e: self._toggle_notifications())

        profile_frame = tk.Frame(right, bg=c["header_bg"], cursor="hand2")
        profile_frame.pack(side="left")

        self._avatar_canvas = tk.Canvas(profile_frame, width=34, height=34, bg=c["header_bg"], highlightthickness=0, bd=0, cursor="hand2")
        self._avatar_canvas.pack(side="left", padx=(0, 8))
        self._avatar_canvas.create_oval(1, 1, 33, 33, fill=c["primary"], outline="")
        self._avatar_text = self._avatar_canvas.create_text(
            17, 17,
            text=_company_initials(self._company_name),
            fill=c["white"],
            font=get_font("small_bold"),
        )

        self._profile_label = tk.Label(
            profile_frame,
            text=f"{self._company_name}  ⌄",
            bg=c["header_bg"],
            fg=c["text_primary"],
            font=get_font("body_bold"),
            cursor="hand2",
        )
        self._profile_label.pack(side="left")

        profile_menu = tk.Menu(
            self,
            tearoff=0,
            bg=c["white"],
            fg=c["text_primary"],
            activebackground=c["primary_light"],
            activeforeground=c["primary_dark"],
            font=get_font("body"),
        )
        profile_menu.add_command(label="  Edit Company Profile  ", command=self.on_edit_company)
        profile_menu.add_command(label="  Backup Database  ", command=self.on_backup)
        profile_menu.add_separator()
        profile_menu.add_command(label="  Refresh Dashboard  ", command=self.on_refresh)

        def _open_profile_menu(_e=None):
            x = profile_frame.winfo_rootx()
            y = profile_frame.winfo_rooty() + profile_frame.winfo_height() + 6
            try:
                profile_menu.tk_popup(x, y)
            finally:
                profile_menu.grab_release()

        for wdg in (profile_frame, self._avatar_canvas, self._profile_label):
            wdg.bind("<Button-1>", _open_profile_menu)

    def _toggle_notifications(self) -> None:
        if self._notif_popup and self._notif_popup.winfo_exists():
            self._notif_popup.destroy()
            self._notif_popup = None
            return

        c = THEME["colors"]
        popup = tk.Toplevel(self)
        popup.overrideredirect(True)
        popup.configure(bg=c["card_border"])
        self._notif_popup = popup

        inner = tk.Frame(popup, bg=c["white"], padx=14, pady=12)
        inner.pack(fill="both", expand=True, padx=1, pady=1)

        hdr = tk.Frame(inner, bg=c["white"])
        hdr.pack(fill="x", pady=(0, 8))
        tk.Label(
            hdr,
            text="Notifications",
            bg=c["white"],
            fg=c["text_primary"],
            font=get_font("section_title", -1),
        ).pack(side="left")
        close_lbl = tk.Label(hdr, text="✕", bg=c["white"], fg=c["text_muted"], font=get_font("small_bold"), cursor="hand2")
        close_lbl.pack(side="right")
        close_lbl.bind("<Button-1>", lambda _e: self._close_notifications())

        for note in self.get_notifications():
            row = tk.Frame(inner, bg=c["tile_bg"], padx=10, pady=7)
            row.pack(fill="x", pady=3)
            tk.Label(
                row,
                text=f"•  {note}",
                bg=c["tile_bg"],
                fg=c["text_secondary"],
                font=get_font("small"),
                wraplength=270,
                justify="left",
            ).pack(anchor="w")

        def _on_focus_out(_e=None):
            self.after(120, self._check_close_notifications)

        popup.bind("<FocusOut>", _on_focus_out)
        popup.bind("<Escape>", lambda _e: self._close_notifications())
        popup.update_idletasks()
        pw = max(300, popup.winfo_reqwidth())
        ph = popup.winfo_reqheight()
        x = self._bell_canvas.winfo_rootx() - pw + self._bell_canvas.winfo_width()
        y = self._bell_canvas.winfo_rooty() + self._bell_canvas.winfo_height() + 6
        popup.geometry(f"{pw}x{ph}+{x}+{y}")
        popup.focus_set()

    def _check_close_notifications(self) -> None:
        if not self._notif_popup or not self._notif_popup.winfo_exists():
            return
        try:
            focused = self.focus_get()
            if focused is not None and focused.winfo_toplevel() == self._notif_popup:
                return
        except Exception:
            pass
        self._close_notifications()

    def _close_notifications(self) -> None:
        if self._notif_popup and self._notif_popup.winfo_exists():
            self._notif_popup.destroy()
        self._notif_popup = None

    def set_company_name(self, name: str) -> None:
        self._company_name = name
        self._profile_label.configure(text=f"{name}  ⌄")
        self._avatar_canvas.itemconfigure(self._avatar_text, text=_company_initials(name))
