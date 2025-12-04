import sys
from pathlib import Path

if getattr(sys, 'frozen', False):  # Running as a PyInstaller EXE
    root_path = Path(sys.executable).parent
else:  # Running as a Python script
    root_path = Path(__file__).parent.parent
sys.path.append(str(root_path))
 
from utilities.path_utils import *
import tkinter as tk

from tkinter import ttk, Canvas, Entry, Text, Button, PhotoImage,messagebox
from tkcalendar import DateEntry

def expense_payments_out(parent = None):
    ASSETS_PATH = Path(generate_path(root_path, "UI", "assets", "frame1"))

    def relative_to_assets(path: str) -> Path:
        return ASSETS_PATH / Path(path)

    def add_payment():
        # Get data from entry fields
        expanceType = Expance.get().strip()  # Remove leading/trailing spaces
        entity_type = 'Expense'
        date = date_entry.get()  # Ensure no spaces
        total_amount = float(entry_4.get())  # Ensure no leading/trailing whitespace
        payment_mode = payment_type.get().strip()  # Ensure no spaces
        reference_no = entry_5.get("1.0", "end-1c").strip() if entry_5.get("1.0", "end-1c").strip() else ""

        if not expanceType:
            messagebox.showerror("Error", "Expance type is required!", parent=window)
            return

        if not date:
            messagebox.showerror("Error", "Date is required!", parent=window)
            return
    
        if not total_amount:
            messagebox.showerror("Error", "Total amount is required!", parent=window)
            return
    
        if not payment_mode:
            messagebox.showerror("Error", "Payment mode is required!", parent=window)
            return

        if not reference_no:
            reference_no = ''

        total_amount = round(float(total_amount), 2)
            
        # Insert payment details into the Payments table
        run_query("""
            INSERT INTO Payments (entity_id, entity_type, date, total_amount, payment_mode, reference_no, Expanse_type)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (1, entity_type, date, total_amount, payment_mode, reference_no, expanceType))

        messagebox.showinfo("Success", "Payment details added successfully!", parent=window)

        Expance.set('')
        date_entry.delete(0, tk.END)
        entry_4.delete(0, tk.END)
        payment_type.delete(0, tk.END)
        entry_5.delete("1.0", "end")


    window = tk.Toplevel(parent)
    window.focus()
    window.iconbitmap(generate_path("UI", "assets", "BillMates.ico"))

    window.transient(parent)
    window.grab_set()
    
    window.title("Add Expaces Payments")
    center_window(window, 380, 380)
    window.configure(bg = "#FBF6FF")


    canvas = Canvas(
        window,
        bg = "#FBF6FF",
        height = 380,
        width = 380,
        bd = 0,
        highlightthickness = 0,
        relief = "ridge"
    )

    canvas.place(x = 0, y = 0)
    canvas.create_rectangle(
        0.0,
        0.0,
        380.0,
        90.0,
        fill="#E7EBFF",
        outline="")

    canvas.create_text(
        55.0,
        24.0,
        anchor="nw",
        text="Expanse Type ",
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

    entry_image_1 = PhotoImage(
        file=relative_to_assets("entry_1.png"))
    entry_bg_1 = canvas.create_image(
        190.0,
        52.91999530792236,
        image=entry_image_1
    )
    Expance_type = [
        "Rent",
        "Utilities",
        "Maintenance", 
        "Transposition",
        "Marketing",
        "Loan Interest",
        "Taxes",
        "Other Expances"
    ]
    
    
    Expance = ttk.Combobox(window, values=Expance_type, state="readonly")
    Expance.current(0)
    Expance.place(
        x=55.0,
        y=40.0,
        width=270.0,
        height=25.0
    )




    date_entry = DateEntry(window, width=12, background="#000000", foreground="white", borderwidth=2, date_pattern='dd/mm/yyyy')
    date_entry.place(
        x=55.0,
        y=112,
        width=270.0,
        height=25.0
    )




    paymentMode = ["Cash","UPI","Net Banking","Check", "Card"]
    payment_type = ttk.Combobox(window, values=paymentMode, state="readonly")
    payment_type.current(0)
    payment_type.place(
        x=55.0,
        y=160.0,
        width=270.0,
        height=25
    )

    float_validation = window.register(lambda value: value == "" or (
        value.replace(".", "", 1).isdigit() and 
        (("." in value and len(value.split(".")[0]) <= 10 and len(value.split(".")[1]) <= 3) or 
        ("." not in value and len(value) <= 10))
    ))
    entry_4 = Entry(window,
        bd=1,
        bg="#FFFFFF",
        fg="#000716",
        font=("VarelaRound Regular", 14 * -1),
        validate="key",
        validatecommand=(float_validation, "%P"),
        highlightthickness=0
    )
    entry_4.place(
        x=55.0,
        y=210.0,
        width=270.0,
        height=25.0
    )



    entry_5 = Text(window,
        bd=1,
        bg="#FFFFFF",
        fg="#000716",
        font=("VarelaRound Regular", 12 * -1),
        highlightthickness=0
    )
    entry_5.place(
        x=55.0,
        y=255.0,
        width=270.0,
        height=45.0
    )




    button_image_1 = PhotoImage(
        file=relative_to_assets("button_1.png"))
    button_1 = Button(window,
        image=button_image_1,
        borderwidth=0,
        highlightthickness=0,
        command=add_payment,
        relief="flat"
    )
    button_1.place(
        x=55.0,
        y=325.0,
        width=270.0,
        height=27.0
    )
    window.resizable(False, False)
    window.bind("<Escape>", lambda event: Top_Close(window, parent))
    window.protocol("WM_DELETE_WINDOW", lambda: Top_Close(window, parent))
    window.mainloop()


    
