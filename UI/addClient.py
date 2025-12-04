import sys
from pathlib import Path

if getattr(sys, 'frozen', False):  # Running as a PyInstaller EXE
    root_path = Path(sys.executable).parent
else:  # Running as a Python script
    root_path = Path(__file__).parent.parent
sys.path.append(str(root_path))
 
from utilities.path_utils import generate_path, center_window, fetch_data, run_query, Top_Close
from tkinter import ttk, Canvas, Entry, Text, Button, PhotoImage, messagebox
import tkinter as tk
from utilities.text import States
import re

def new_client_ui(parent = None):
    ASSETS_PATH = Path(generate_path(root_path, "UI", "assets", "frame5"))

    def relative_to_assets(path: str) -> Path:
        return ASSETS_PATH / Path(path)

    def update_text(event):

        selected_value = dropdown.get()

        if selected_value == "Staff":
            canvas.itemconfig(text_gst, text="Position")
            canvas.itemconfig(Heading, text="Add Staff")

    def add_client_to_db():
        # Fetch data from entry fields
        name = name_entry.get().strip()
        contact_no = contect_no_entry.get().strip()
        gst = gst_entry.get().strip().upper()
        city = city_entry.get().strip()
        state = state_entry.get().strip()
        client_type = dropdown.get().strip()
        Opening_Balance = Balance.get().strip()

        # Validation
        if not name:
            messagebox.showerror("Validation Error", "Name cannot be empty.", parent=window)
            return

        if not city:
            messagebox.showerror("Validation Error", "City cannot be empty.", parent=window)
            return

        if not state:
            messagebox.showerror("Validation Error", "State cannot be empty.", parent=window)
            return

        if client_type not in ["Client", "Supplier", "Staff"]:
            messagebox.showerror("Validation Error", "Invalid client type selected.", parent=window)
            return


        Clients = fetch_data(f"""SELECT count(name) FROM Clients WHERE name = '{name}' AND client_type = '{client_type}'""")
        
        if Clients[0][0] > 0:
            messagebox.showerror("Validation Error", "This name is already exists with this client type", parent=window)
            return
        
        gst_pattern = r"[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}"
        if not re.fullmatch(gst_pattern, gst):
            messagebox.showerror("Error", "Invalid GSTIN Number!\nExample: 22ABCDE1234F1Z5", parent=window)
            return

        # Add to database
        try:
            # Insert the client details
            run_query("""
                INSERT INTO Clients (name, contact_no, gst, city, state, client_type, opening_balance, closing_bal)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (name, contact_no, gst, city, state, client_type, float(Opening_Balance), float(Opening_Balance)))

            messagebox.showinfo("Success", "details added successfully!", parent=window)
            # Clear the input fields after successful addition
            contect_no_entry.delete(0, 'end')
            gst_entry.delete(0, 'end')
            city_entry.delete(0, 'end')
            state_entry.delete(0, 'end')
            name_entry.delete(0, 'end')
            dropdown.set("Client")

        except Exception as e:
            messagebox.showerror("Database Error", f"An error occurred while adding the client: {e}", parent=window)


    window = tk.Toplevel(parent)
    window.focus()
    window.iconbitmap(generate_path("UI", "assets", "BillMates.ico"))
    window.transient(parent)
    window.grab_set()
    window.title("Create Party")
    center_window(window, 480, 570)
    window.configure(bg = "#E7EBFF")

    canvas = Canvas(
        window,
        bg = "#E7EBFF",
        height = 570,
        width = 480,
        bd = 0,
        highlightthickness = 0,
        relief = "ridge"
    )
    canvas.place(x = 0, y = 0)

    canvas.create_text(
        95.0,
        121.0,
        anchor="nw",
        text="Name",
        fill="#000000",
        font=("VarelaRound Regular", 12 * -1)
    )

    canvas.create_text(
        95.0,
        177.0,
        anchor="nw",
        text="Contact No.",
        fill="#000000",
        font=("VarelaRound Regular", 12 * -1)
    )

    text_gst = canvas.create_text(
        95.0,
        233.0,
        anchor="nw",
        text="GST No. ",
        fill="#000000",
        font=("VarelaRound Regular", 12 * -1)
    )

    canvas.create_text(
        95.0,
        289.0,
        anchor="nw",
        text="City",
        fill="#000000",
        font=("VarelaRound Regular", 12 * -1)
    )

    canvas.create_text(
        95.0,
        345.0,
        anchor="nw",
        text="State",
        fill="#000000",
        font=("VarelaRound Regular", 12 * -1)
    )

    canvas.create_text(
        95.0,
        65.0,
        anchor="nw",
        text="Trader Type",
        fill="#000000",
        font=("VarelaRound Regular", 12 * -1)
    )

    canvas.create_text(
        95.0,
        400.0,
        anchor="nw",
        text="Opening Balance",
        fill="#000000",
        font=("VarelaRound Regular", 12 * -1)
    )


    name_entry = Entry(window,
        bd=1,
        bg="#FFFFFF",
        fg="#000716",
        font=("VarelaRound Regular", 14 * -1),
        highlightthickness=0
    )
    name_entry.place(
        x=95.0,
        y=137.0,
        width=290.0,
        height=25.0
    )

    mobile_validation = window.register(
        lambda value: re.fullmatch(r"[0-9]{0,10}", value) is not None
    )
    contect_no_entry = Entry(window,
        bd=1,
        bg="#FFFFFF",
        fg="#000716",
        font=("VarelaRound Regular", 14 * -1),
        validate="key",  # Trigger validation on keypress
        validatecommand=(mobile_validation, "%P"),
        highlightthickness=0
    )
    contect_no_entry.place(
        x=95.0,
        y=193.0,
        width=290.0,
        height=25.0
    )

    gst_entry = Entry(window,
        bd=1,
        bg="#FFFFFF",
        fg="#000716",
        font=("VarelaRound Regular", 14 * -1),
        highlightthickness=0
    )
    gst_entry.place(
        x=95.0,
        y=249.0,
        width=290.0,
        height=25.0
    )


    city_entry = Entry(window,
        bd=1,
        bg="#FFFFFF",
        fg="#000716",
        font=("VarelaRound Regular", 14 * -1),
        highlightthickness=0
    )
    city_entry.place(
        x=95.0,
        y=305.0,
        width=290.0,
        height=25.0
    )

    state_entry = ttk.Combobox(
        window, 
        values=States, 
        state="readonly"  # Makes it a dropdown (not editable)
    )
    state_entry.set("Select")
    state_entry.place(
        x=95.0,
        y=361.0,
        width=290.0,
        height=25.0
    )

    dropdown = ttk.Combobox(
        window, 
        values=["Client", "Supplier", "Staff"], 
        state="readonly"  # Makes it a dropdown (not editable)
    )
    dropdown.set("Client")
    dropdown.bind("<<ComboboxSelected>>", update_text) 

    # Place the Combobox in the window
    dropdown.place(
        x=95.0,
        y=81.0,
        width=290.0,
        height=25.0
    )

    float_validation = window.register(lambda value: value == "" or value.replace(".", "", 1).isdigit())
    Balance = Entry(window,
        bd=1,
        bg="#FFFFFF",
        fg="#000716",
        font=("VarelaRound Regular", 14 * -1),
        validate="key",
        validatecommand=(float_validation, "%P"),
        highlightthickness=0
    )
    Balance.insert(0, 00)
    Balance.place(
        x=95.0,
        y=417.0,
        width=290.0,
        height=25.0
    )


    Heading = canvas.create_text(
        195.0,
        25.0,
        anchor="nw",
        text="Add Client",
        fill="#000000",
        font=("VarelaRound Regular", 16 * -1)
    )


    button_image_1 = PhotoImage(
        file=relative_to_assets("button_1.png"))
    button_1 = Button(window,
        image=button_image_1,
        borderwidth=0,
        highlightthickness=0,
        command=add_client_to_db,
        relief="flat"
    )
    button_1.place(
        x=95.0,
        y=480.0,
        width=290.0,
        height=30.0
    )

    window.resizable(False, False)
    window.bind("<Escape>", lambda event: Top_Close(window, parent))
    window.protocol("WM_DELETE_WINDOW", lambda: Top_Close(window, parent))
    window.mainloop()


if __name__ == "__main__":
    new_client_ui()