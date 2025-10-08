import sys
from pathlib import Path

if getattr(sys, 'frozen', False):  # Running as a PyInstaller EXE
    root_path = Path(sys.executable).parent
else:  # Running as a Python script
    root_path = Path(__file__).parent.parent
sys.path.append(str(root_path))
 
from utilities.path_utils import *
import tkinter as tk

from tkinter import ttk, Canvas, Entry, Text, Button, PhotoImage, messagebox
from tkcalendar import DateEntry


def customer_payment_in(parent = None):
    ASSETS_PATH = Path(generate_path(root_path, "UI", "assets", "frame0"))


    def relative_to_assets(path: str) -> Path:
        return ASSETS_PATH / Path(path)
    
    def add_payment():
        # Get data from entry fields
        Cus_name = customer_name.get().strip()  # Remove leading/trailing spaces
        entity_type = 'Client'
        date = date_entry.get()  # Ensure no spaces
        total_amount = entry_4.get().strip()  
        payment_mode = payment_type.get().strip()  # Ensure no spaces
        reference_no = entry_5.get("1.0", "end-1c").strip() if entry_5.get("1.0", "end-1c").strip() else ""

        total_amount = round(float(total_amount), 2)

        if not Cus_name:
            messagebox.showwarning("Error", "Customer name is required!", parent=window)
            return

        if not date:
            messagebox.showwarning("Error", "Date is required!", parent=window)
            return
    
        if not total_amount:
            messagebox.showwarning("Error", "Total amount is required!", parent=window)
            return
    
        if not payment_mode:
            messagebox.showwarning("Error", "Payment mode is required!", parent=window)
            return

        if not reference_no:
            reference_no = ''

        
        entity_id = get_client_id(Cus_name)
        
        # If a result is found, proceed with inserting payment details
        if entity_id:

            amount = float(total_amount)

            Added_Balance = amount
            invoices = fetch_data(f"""SELECT invoice_id, total, paid, remaining FROM Invoices WHERE client_id = {entity_id} AND remaining > 0 AND paid_status != 'Paid' ORDER BY created_at ASC""")

            for invoice in invoices:
                if amount <= 0:
                    break
                
                invoice_id, total, paid, remaining = invoice
                if amount >= remaining:
                    # Full payment for this invoice
                    run_query("UPDATE Invoices SET paid = ?, remaining = 0, paid_status = ? WHERE invoice_id = ?", (total, 'Paid', invoice_id))
                    amount -= remaining
                else:
                    # Partial payment
                    run_query("UPDATE Invoices SET paid = ?, remaining = ?, paid_status = ? WHERE invoice_id = ?", (paid + amount, remaining - amount, 'Partially Paid', invoice_id))
                    amount = 0
                    break  # Stop since no more payment is left
                
            Opening_Balance = fetch_data(f"""SELECT closing_bal FROM Clients WHERE id = {entity_id}""")[0][0]

            Closing_Balance = Opening_Balance + Added_Balance

            run_query(f"""UPDATE Clients SET closing_bal = {float(Closing_Balance)} WHERE id = {entity_id}""")

            # # Insert payment details into the Payments table

            query = """
                INSERT INTO Payments (entity_id, entity_type, date, total_amount, payment_mode, reference_no, Expanse_type)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            params = (entity_id, "Income", date, total_amount, payment_mode, reference_no, "Invoice Payment")

            run_query(query, params)

            # Show success message
            messagebox.showinfo("Success", "Payment details added successfully!", parent=window)

        else:
            # Show error message if client not found
            messagebox.showerror("Error", "No client found with the given name and type.", parent=window)


        customer_name.set('')
        date_entry.delete(0, tk.END)
        entry_4.delete(0, tk.END)
        payment_type.delete(0, tk.END)
        entry_5.delete("1.0", "end")




    window = tk.Toplevel(parent)
    window.focus()
    window.transient(parent)
    window.grab_set()
    window.iconbitmap(generate_path("UI", "assets", "BillMates.ico"))
    window.title("Add Customer Payments")
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
        27.0,
        anchor="nw",
        text="Client Name",
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



    customer_name = ttk.Combobox(
        window, 
        values=fetch_client_names('Client'), 
        state="readonly", 
        font=("VarelaRound Regular", 14 * -1)
    )
    customer_name.place(
        x=55.0,
        y=43,
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


if __name__ == "__main__":
    customer_payment_in()

