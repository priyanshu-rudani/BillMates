"""
UI/payment_form.py
------------------
Reusable Payment Window component for:
- Client (Customer) Payment In
- Supplier (Purchase) Payment Out
- Salary Payment
- Company Expense Payment
"""
from __future__ import annotations

import sys
from pathlib import Path

if getattr(sys, 'frozen', False):
    root_path = Path(sys.executable).parent
else:
    root_path = Path(__file__).parent.parent
sys.path.append(str(root_path))

import tkinter as tk
from tkinter import ttk, Canvas, Entry, Text, Button, messagebox
from tkcalendar import DateEntry

from utilities.path_utils import generate_path, center_window, fetch_client_names, Top_Close
from utilities.window_registry import single_instance, track
from services.payment_service import PaymentService, PaymentConfig, PaymentInput, PaymentError


EXPENSE_TYPES = [
    "Rent",
    "Utilities",
    "Maintenance",
    "Transposition",
    "Marketing",
    "Loan Interest",
    "Taxes",
    "Other Expances",
]

PAYMENT_MODES = ["Cash", "UPI", "Net Banking", "Check", "Card"]

BUTTON_LABELS = {
    "client": "Add Payment",
    "expense": "Add Expense",
    "salary": "Pay Salary",
    "supplier": "Pay Supplier",
}


def open_payment_window(config: PaymentConfig, parent=None):
    """Factory function that renders a reusable payment form window based on config."""
    service = PaymentService(config)

    window = tk.Toplevel(parent)
    window.focus()
    window.transient(parent)
    window.grab_set()
    window.iconbitmap(generate_path("UI", "assets", "BillMates.ico"))
    window.title(config.window_title)
    center_window(window, 380, 380)
    window.configure(bg="#FBF6FF")

    canvas = Canvas(
        window,
        bg="#FBF6FF",
        height=380,
        width=380,
        bd=0,
        highlightthickness=0,
        relief="ridge"
    )
    canvas.place(x=0, y=0)

    # Header decorative banner
    canvas.create_rectangle(0.0, 0.0, 380.0, 90.0, fill="#E7EBFF", outline="")

    # Field Labels
    canvas.create_text(
        55.0,
        27.0,
        anchor="nw",
        text=config.target_label,
        fill="#000000",
        font=("VarelaRound Regular", 13 * -1)
    )
    canvas.create_text(
        55.0,
        97.0,
        anchor="nw",
        text="Date",
        fill="#000000",
        font=("VarelaRound Regular", 13 * -1)
    )
    canvas.create_text(
        55.0,
        145.0,
        anchor="nw",
        text="Payment Type ",
        fill="#000000",
        font=("VarelaRound Regular", 13 * -1)
    )
    canvas.create_text(
        55.0,
        195.0,
        anchor="nw",
        text="Amount",
        fill="#000000",
        font=("VarelaRound Regular", 13 * -1)
    )
    canvas.create_text(
        55.0,
        240.0,
        anchor="nw",
        text="Remark",
        fill="#000000",
        font=("VarelaRound Regular", 13 * -1)
    )

    # Target Dropdown (Party name or Expense type)
    if config.name == "expense":
        target_dropdown = ttk.Combobox(window, values=EXPENSE_TYPES, state="readonly")
        target_dropdown.current(0)
    else:
        party_names = fetch_client_names(config.client_type)
        target_dropdown = ttk.Combobox(
            window,
            values=party_names,
            state="readonly",
            font=("VarelaRound Regular", 14 * -1)
        )
    target_dropdown.place(x=55.0, y=43.0, width=270.0, height=25.0)

    # Date Entry
    date_entry = DateEntry(
        window,
        width=12,
        background="#000000",
        foreground="white",
        borderwidth=2,
        date_pattern='dd/mm/yyyy'
    )
    date_entry.place(x=55.0, y=112.0, width=270.0, height=25.0)

    # Payment Mode Dropdown
    payment_mode_dropdown = ttk.Combobox(window, values=PAYMENT_MODES, state="readonly")
    payment_mode_dropdown.current(0)
    payment_mode_dropdown.place(x=55.0, y=160.0, width=270.0, height=25.0)

    # Amount Entry with numeric validation
    float_validation = window.register(lambda value: value == "" or (
        value.replace(".", "", 1).isdigit() and
        (("." in value and len(value.split(".")[0]) <= 10 and len(value.split(".")[1]) <= 3) or
         ("." not in value and len(value) <= 10))
    ))
    amount_entry = Entry(
        window,
        bd=1,
        bg="#FFFFFF",
        fg="#000716",
        font=("VarelaRound Regular", 14 * -1),
        validate="key",
        validatecommand=(float_validation, "%P"),
        highlightthickness=0
    )
    amount_entry.place(x=55.0, y=210.0, width=270.0, height=25.0)

    # Remarks Text Area
    remark_text = Text(
        window,
        bd=1,
        bg="#FFFFFF",
        fg="#000716",
        font=("VarelaRound Regular", 12 * -1),
        highlightthickness=0
    )
    remark_text.place(x=55.0, y=255.0, width=270.0, height=45.0)

    # Submit Handler
    def on_submit():
        payment_input = PaymentInput(
            target_name=target_dropdown.get().strip(),
            date=date_entry.get().strip(),
            total_amount=amount_entry.get().strip(),
            payment_mode=payment_mode_dropdown.get().strip(),
            reference_no=remark_text.get("1.0", "end-1c").strip(),
        )

        try:
            service.validate_and_record_payment(payment_input)
            success_msg = f"{config.window_title.replace('Add ', '')} recorded successfully!"
            messagebox.showinfo("Success", success_msg, parent=window)

            # Reset fields
            if config.name == "expense":
                target_dropdown.current(0)
            else:
                target_dropdown.set('')
            date_entry.delete(0, tk.END)
            amount_entry.delete(0, tk.END)
            payment_mode_dropdown.current(0)
            remark_text.delete("1.0", "end")
        except PaymentError as pe:
            if pe.level == "warning":
                messagebox.showwarning(pe.title, pe.message, parent=window)
            else:
                messagebox.showerror(pe.title, pe.message, parent=window)
        except Exception as exc:
            messagebox.showerror("Error", f"Failed to record payment: {str(exc)}", parent=window)

    # Submit Button (native Tkinter Button replacing raster image)
    button_text = BUTTON_LABELS.get(config.name, "Submit Payment")
    submit_button = Button(
        window,
        text=button_text,
        bg="#4F59C1",
        fg="#FFFFFF",
        activebackground="#3F48A6",
        activeforeground="#FFFFFF",
        font=("VarelaRound Regular", 12 * -1),
        bd=0,
        relief="flat",
        cursor="hand2",
        command=on_submit,
        highlightthickness=0
    )
    submit_button.place(x=55.0, y=325.0, width=270.0, height=30.0)

    window.resizable(False, False)
    window.bind("<Escape>", lambda event: Top_Close(window, parent))
    window.protocol("WM_DELETE_WINDOW", lambda: Top_Close(window, parent))
    window.wait_window()
