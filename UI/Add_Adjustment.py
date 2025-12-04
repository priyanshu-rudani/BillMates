import sys
from pathlib import Path

if getattr(sys, 'frozen', False):  # Running as a PyInstaller EXE
    root_path = Path(sys.executable).parent
else:  # Running as a Python script
    root_path = Path(__file__).parent.parent
sys.path.append(str(root_path))
 

from tkcalendar import DateEntry
from datetime import datetime
from tkinter import Tk, Canvas, Entry, Text, Button, PhotoImage, ttk, messagebox
from utilities.path_utils import *


def new_adjustment_ui(parent = None):

    ASSETS_PATH = Path(generate_path(root_path, "UI", "assets", "frame12"))

    def relative_to_assets(path: str) -> Path:
        return ASSETS_PATH / Path(path)

    window = tk.Toplevel()
    window.iconbitmap(generate_path("UI", "assets", "BillMates.ico"))
    window.title("Add Adjustment")
    center_window(window, 500, 390)
    window.configure(bg = "#FBF6FF")
    window.transient(parent)
    window.grab_set() 
    window.focus()


    def Adjustment():
        client_type = Client_type.get()
        Client_name = Client.get()
        Client_id = get_client_id(Client_name)
        Type = dropdown.get()
        Date = date_selector.get()
        Payment = payment_type.get()
        Amount = round(float(amount.get()), 2)
        Text = entry_7.get("1.0", "end").strip()

        if not client_type or Client_type == 'Select':
            messagebox.showerror("Error", "Please select client type", parent=window)
            return
        elif not Client_name or Client_name == 'Select':
            messagebox.showerror("Error", "Please select client name", parent=window)
            return
        elif not Type or Type == 'Select':
            messagebox.showerror("Error", "Please select a Adjustment type", parent=window)
            return
        elif not Date:
            messagebox.showerror("Error", "Please select a date", parent=window)
            return
        elif not Payment:
            messagebox.showerror("Error", "Please select a payment type", parent=window)
            return
        elif not Amount:
            messagebox.showerror("Error", "Please enter an amount", parent=window)
            return
        elif not Text:
            Text = ''

        try:
            expanse_type = 'Adjustment Credit' if Type == 'Credit (+)' else 'Adjustment Debit'
            query = """
                INSERT INTO Payments (entity_id, entity_type, date, total_amount, payment_mode, reference_no, Expanse_type)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            params = (Client_id, "Adjustment", Date, Amount, Payment, Text, expanse_type)
            run_query(query, params)
            messagebox.showinfo("Success", "Adjustment Payment added successfully!", parent=window)
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Failed to add adjustment payment: {e}", parent=window)

        Client_type.set('Select')
        Client.set('Select')
        Client.configure(values="")
        dropdown.set('Select')
        payment_type.set('Select')
        date_selector.set_date(datetime.now())
        amount.delete(0, "end")
        entry_7.delete("1.0", "end")



    canvas = Canvas(
        window,
        bg = "#FBF6FF",
        height = 390,
        width = 500,
        bd = 0,
        highlightthickness = 0,
        relief = "ridge"
    )

    canvas.place(x = 0, y = 0)
    canvas.create_rectangle(
        0.0,
        0.0,
        500.0,
        80.0,
        fill="#E7EBFF",
        outline="")

    canvas.create_text(
        46.0,
        19.0,
        anchor="nw",
        text="Client Type",
        fill="#000000",
        font=("VarelaRound Regular", 12 * -1)
    )

    canvas.create_text(
        242.0,
        19.0,
        anchor="nw",
        text="Client Name",
        fill="#000000",
        font=("VarelaRound Regular", 12 * -1)
    )

    Client_type = ttk.Combobox(
        window,
        values=["Client", "Supplier"],
        state="readonly",
        font=("VarelaRound Regular", 10)
    )
    Client_type.place(
        x=46.0,
        y=38.0,
        width=175.0,
        height=25.0
    )
        
    def update_client_names(event):
        client_type = Client_type.get()  # Get selected client type
        client_names = fetch_client_names(client_type)
        Client.set("Select")
        Client['values'] = client_names

    Client_type.bind("<<ComboboxSelected>>", update_client_names)

    Client = ttk.Combobox(
        window,
        values="",
        state="readonly",
        font=("VarelaRound Regular", 10)
    )
    Client.place(
        x=242.0,
        y=38.0,
        width=215.0,
        height=25.0
    )

    canvas.create_text(
        46.0,
        89.0,
        anchor="nw",
        text="Date",
        fill="#000000",
        font=("VarelaRound Regular", 12 * -1)
    )

    date_selector = DateEntry(
        window,
        bd=0,
        state="readonly",
        bg="#FFFFFF",
        fg="#000716",
        highlightthickness=0,
        date_pattern='dd/mm/yyyy',
    )
    date_selector.place(
        x=46.0,
        y=108.0,
        width=175.0,
        height=25.0
    )

    canvas.create_text(
        242.0,
        154.0,
        anchor="nw",
        text="Amount",
        fill="#000000",
        font=("VarelaRound Regular", 12 * -1)
    )

    dropdown = ttk.Combobox(
        window, 
        values=["Credit (+)", "Debit (-)"], 
        state="readonly",
        font=("VarelaRound Regular", 10)
    )
    dropdown.set("Select")
    dropdown.place(
        x=242.0,
        y=108.0,
        width=215.0,
        height=25.0
    )

    canvas.create_text(
        46.0,
        154.0,
        anchor="nw",
        text="Payment Mode",
        fill="#000000",
        font=("VarelaRound Regular", 12 * -1)
    )

    canvas.create_text(
        242.0,
        89.0,
        anchor="nw",
        text="Adjustment Types",
        fill="#000000",
        font=("VarelaRound Regular", 12 * -1)
    )


    paymentMode = ["Cash","UPI","Net Banking","Check", "Card"]
    payment_type = ttk.Combobox(window, values=paymentMode, state="readonly")
    payment_type.current(0)
    payment_type.place(
        x=46.0,
        y=173.0,
        width=175.0,
        height=25.0
    )


    float_validation = window.register(lambda value: value == "" or value.replace(".", "", 1).isdigit())
    amount = Entry(
        window,
        bd=1,
        bg="#FFFFFF",
        fg="#000716",
        validate="key",
        validatecommand=(float_validation, "%P"),
        font=("VarelaRound Regular", 12 * -1),
        highlightthickness=1
    )
    amount.place(
        x=242.0,
        y=173.0,
        width=215.0,
        height=25.0
    )

    canvas.create_text(
        46.0,
        219.0,
        anchor="nw",
        text="Remark",
        fill="#000000",
        font=("VarelaRound Regular", 12 * -1)
    )


    entry_7 = Text(
        window,
        bd=1,
        bg="#FFFFFF",
        fg="#000716",
        font=("VarelaRound Regular", 12 * -1),
        highlightthickness=0
    )
    entry_7.place(
        x=46.0,
        y=238.0,
        width=411.0,
        height=53.0
    )

    button_image_1 = PhotoImage(
        file=relative_to_assets("button_1.png"))
    button_1 = Button(
        window,
        image=button_image_1,
        borderwidth=0,
        highlightthickness=0,
        command=Adjustment,
        relief="flat"
    )
    button_1.place(
        x=46.0,
        y=319.0,
        width=411.0,
        height=30.31463623046875
    )

    window.resizable(False, False)
    window.bind("<Escape>", lambda event: Top_Close(window, parent))
    window.protocol("WM_DELETE_WINDOW", lambda: Top_Close(window, parent))
    window.mainloop()





