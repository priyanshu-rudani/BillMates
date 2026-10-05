"""
services/autocomplete.py
-------------------------
Entry + dropdown suggestions. Replaces SearchBox for the item code / item name fields.

    AutoComplete(item_code, service.item_codes, on_select=on_item_code_select)

* `get_values` is a callable (fresh data each time the field gets focus / a search starts),
  so items added in the current session show up immediately.
* Case-insensitive; matches that START with the text are listed before "contains" matches.
* Keys: Up/Down move, Enter picks, Esc closes (the window's own Esc only fires when closed).
* Mouse: single click on a suggestion picks it.
"""
import tkinter as tk
from typing import Callable, Iterable, List, Optional

_IGNORED_KEYS = {
    "Up", "Down", "Return", "KP_Enter", "Escape", "Tab", "ISO_Left_Tab",
    "Left", "Right", "Home", "End", "Shift_L", "Shift_R", "Control_L", "Control_R",
    "Alt_L", "Alt_R", "Caps_Lock",
}


class AutoComplete:
    def __init__(self, entry: tk.Entry, get_values: Callable[[], Iterable],
                 on_select: Optional[Callable[[str], None]] = None,
                 max_rows: int = 5, max_matches: int = 100):
        self.entry = entry
        self.get_values = get_values
        self.on_select = on_select
        self.max_rows = max_rows
        self.max_matches = max_matches
        self._values: List[str] = []

        # The listbox must share the entry's parent so place() coordinates line up.
        self.listbox = tk.Listbox(entry.master, font=entry.cget("font"), height=max_rows,
                                  activestyle="none", exportselection=False)

        entry.bind("<FocusIn>", self._on_focus_in, add="+")
        entry.bind("<FocusOut>", self._on_focus_out, add="+")
        entry.bind("<KeyRelease>", self._on_key_release, add="+")
        entry.bind("<Down>", lambda e: self._move(+1), add="+")
        entry.bind("<Up>", lambda e: self._move(-1), add="+")
        entry.bind("<Return>", self._on_return, add="+")
        entry.bind("<KP_Enter>", self._on_return, add="+")
        entry.bind("<Escape>", self._on_escape, add="+")
        self.listbox.bind("<ButtonRelease-1>", self._on_click)

    # ---- data ---------------------------------------------------------------
    def refresh(self) -> None:
        try:
            raw = self.get_values()
        except Exception:
            raw = []
        seen, cleaned = set(), []
        for v in raw or []:
            if v is None:
                continue
            text = str(v).strip()
            if text and text.lower() not in seen:
                seen.add(text.lower())
                cleaned.append(text)
        self._values = cleaned

    def _matches(self, query: str) -> List[str]:
        q = query.lower()
        starts = [v for v in self._values if v.lower().startswith(q)]
        contains = [v for v in self._values if q in v.lower() and not v.lower().startswith(q)]
        return (starts + contains)[: self.max_matches]

    # ---- popup --------------------------------------------------------------
    def _show(self, items: List[str]) -> None:
        self.listbox.delete(0, tk.END)
        for it in items:
            self.listbox.insert(tk.END, it)
        self.listbox.config(height=min(len(items), self.max_rows))
        self.entry.update_idletasks()
        self.listbox.place(x=self.entry.winfo_x(),
                           y=self.entry.winfo_y() + self.entry.winfo_height(),
                           width=self.entry.winfo_width())
        self.listbox.lift()

    def hide(self) -> None:
        self.listbox.place_forget()

    @property
    def visible(self) -> bool:
        return bool(self.listbox.winfo_manager())

    # ---- events -------------------------------------------------------------
    def _on_focus_in(self, event=None):
        self.refresh()

    def _on_focus_out(self, event=None):
        # delay so a click on the listbox is processed before we hide it
        self.entry.after(150, self._hide_if_unfocused)

    def _hide_if_unfocused(self):
        try:
            focus = self.entry.focus_get()
        except KeyError:  # focus inside a popdown/combobox list
            focus = None
        if focus not in (self.entry, self.listbox):
            self.hide()

    def _on_key_release(self, event):
        if event.keysym in _IGNORED_KEYS:
            return
        text = self.entry.get().strip()
        if not text:
            self.hide()
            return
        if len(text) == 1 or not self._values:   # new search -> pick up fresh data
            self.refresh()
        items = self._matches(text)
        # hide when nothing matches, or the only match is exactly what is typed
        if not items or (len(items) == 1 and items[0].lower() == text.lower()):
            self.hide()
        else:
            self._show(items)

    def _move(self, step: int):
        if not self.visible or self.listbox.size() == 0:
            return None
        cur = self.listbox.curselection()
        idx = (cur[0] + step) if cur else (0 if step > 0 else self.listbox.size() - 1)
        idx = max(0, min(idx, self.listbox.size() - 1))
        self.listbox.selection_clear(0, tk.END)
        self.listbox.selection_set(idx)
        self.listbox.activate(idx)
        self.listbox.see(idx)
        return "break"

    def _on_return(self, event):
        if self.visible and self.listbox.curselection():
            self._accept(self.listbox.get(self.listbox.curselection()[0]))
            return "break"
        return None

    def _on_escape(self, event):
        if self.visible:
            self.hide()
            return "break"       # consume: don't trigger the window's Esc (close)
        return None

    def _on_click(self, event):
        idx = self.listbox.nearest(event.y)
        if idx >= 0 and self.listbox.size() > idx:
            self._accept(self.listbox.get(idx))

    def _accept(self, value: str) -> None:
        self.entry.delete(0, tk.END)
        self.entry.insert(0, value)
        self.entry.icursor(tk.END)
        self.hide()
        self.entry.focus_set()
        if self.on_select:
            self.on_select(value)