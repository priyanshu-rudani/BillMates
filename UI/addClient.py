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


def new_client_ui(parent=None, client_id=None, on_saved=None):
    """
    Open window to create or edit a client/supplier/staff party.
    If client_id is provided, pre-populates fields and saves updates.
    on_saved: optional callback invoked upon successful save/update.
    """
    is_edit_mode = client_id is not None
    client_data = None

    if is_edit_mode:
        rows = fetch_data(
            "SELECT id, name, contact_no, gst, city, state, client_type, opening_balance, closing_bal FROM Clients WHERE id = ?",
            (client_id,)
        )
        if rows:
            client_data = rows[0]
        else:
            messagebox.showerror("Error", f"Party with ID {client_id} not found.", parent=parent)
            return

    def update_text(event=None):
        selected_value = dropdown.get()
        action_verb = "Edit" if is_edit_mode else "Add"

        if selected_value == "Staff":
            canvas.itemconfig(text_gst, text="Position")
            canvas.itemconfig(Heading, text=f"{action_verb} Staff")
            submit_button.config(text=f"{action_verb} Staff")
        elif selected_value == "Client":
            canvas.itemconfig(text_gst, text="GST No. ")
            canvas.itemconfig(Heading, text=f"{action_verb} Client")
            submit_button.config(text=f"{action_verb} Client")
        elif selected_value == "Supplier":
            canvas.itemconfig(text_gst, text="GST No. ")
            canvas.itemconfig(Heading, text=f"{action_verb} Supplier")
            submit_button.config(text=f"{action_verb} Supplier")

    def save_client_to_db():
        name = name_entry.get().strip()
        contact_no = contect_no_entry.get().strip()
        gst = gst_entry.get().strip().upper()
        city = city_entry.get().strip()
        state = state_entry.get().strip()
        client_type = dropdown.get().strip()
        opening_balance_val = Balance.get().strip()

        # Validation
        if not name:
            messagebox.showerror("Validation Error", "Name cannot be empty.", parent=window)
            return

        if not city:
            messagebox.showerror("Validation Error", "City cannot be empty.", parent=window)
            return

        if not state or state == "Select":
            messagebox.showerror("Validation Error", "Please select a valid State.", parent=window)
            return

        if client_type not in ["Client", "Supplier", "Staff"]:
            messagebox.showerror("Validation Error", "Invalid party type selected.", parent=window)
            return

        # Check duplicate name for same client_type
        if is_edit_mode:
            existing = fetch_data(
                "SELECT count(name) FROM Clients WHERE name = ? AND client_type = ? AND id != ?",
                (name, client_type, client_id)
            )
        else:
            existing = fetch_data(
                "SELECT count(name) FROM Clients WHERE name = ? AND client_type = ?",
                (name, client_type)
            )

        if existing and existing[0][0] > 0:
            messagebox.showerror("Validation Error", "This name already exists with this party type.", parent=window)
            return

        # Validate GST only if entered and party is not staff
        if gst and client_type != "Staff":
            gst_pattern = r"[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}"
            if not re.fullmatch(gst_pattern, gst):
                messagebox.showerror("Error", "Invalid GSTIN Number!\nExample: 22ABCDE1234F1Z5", parent=window)
                return

        try:
            op_bal_float = float(opening_balance_val) if opening_balance_val else 0.0
        except ValueError:
            messagebox.showerror("Validation Error", "Please enter a valid Opening Balance.", parent=window)
            return

        try:
            if is_edit_mode:
                # Recalculate closing balance: closing_bal = closing_bal + (new_op_bal - old_op_bal)
                old_op_bal = float(client_data[7] or 0.0)
                old_closing_bal = float(client_data[8] or 0.0)
                bal_diff = op_bal_float - old_op_bal
                new_closing_bal = old_closing_bal + bal_diff

                run_query("""
                    UPDATE Clients
                    SET name = ?, contact_no = ?, gst = ?, city = ?, state = ?, client_type = ?, opening_balance = ?, closing_bal = ?
                    WHERE id = ?
                """, (name, contact_no, gst, city, state, client_type, op_bal_float, new_closing_bal, client_id))

                messagebox.showinfo("Success", "Party details updated successfully!", parent=window)
                if on_saved:
                    on_saved()
                Top_Close(window, parent)
            else:
                run_query("""
                    INSERT INTO Clients (name, contact_no, gst, city, state, client_type, opening_balance, closing_bal)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (name, contact_no, gst, city, state, client_type, op_bal_float, op_bal_float))

                messagebox.showinfo("Success", "Party details added successfully!", parent=window)
                if on_saved:
                    on_saved()

                # Clear fields for next entry
                contect_no_entry.delete(0, 'end')
                gst_entry.delete(0, 'end')
                city_entry.delete(0, 'end')
                state_entry.set("Select")
                name_entry.delete(0, 'end')
                Balance.delete(0, 'end')
                Balance.insert(0, "0")
                dropdown.set("Client")
                update_text()

        except Exception as e:
            messagebox.showerror("Database Error", f"An error occurred: {e}", parent=window)

    window = tk.Toplevel(parent)
    window.focus()
    window.iconbitmap(generate_path("UI", "assets", "BillMates.ico"))
    window.transient(parent)
    window.grab_set()
    window.title("Edit Party" if is_edit_mode else "Create Party")
    center_window(window, 480, 570)
    window.configure(bg="#E7EBFF")

    canvas = Canvas(
        window,
        bg="#E7EBFF",
        height=570,
        width=480,
        bd=0,
        highlightthickness=0,
        relief="ridge"
    )
    canvas.place(x=0, y=0)

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

    name_entry = Entry(
        window,
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
    contect_no_entry = Entry(
        window,
        bd=1,
        bg="#FFFFFF",
        fg="#000716",
        font=("VarelaRound Regular", 14 * -1),
        validate="key",
        validatecommand=(mobile_validation, "%P"),
        highlightthickness=0
    )
    contect_no_entry.place(
        x=95.0,
        y=193.0,
        width=290.0,
        height=25.0
    )

    gst_entry = Entry(
        window,
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

    city_entry = Entry(
        window,
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
        state="readonly"
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
        state="readonly"
    )
    dropdown.set("Client")
    dropdown.bind("<<ComboboxSelected>>", update_text) 
    dropdown.place(
        x=95.0,
        y=81.0,
        width=290.0,
        height=25.0
    )

    def is_valid_signed_float(value: str) -> bool:
        if value in ("", "+", "-", ".", "+.", "-."):
            return True
        unsigned = value[1:] if value[0] in ("+", "-") else value
        return unsigned.replace(".", "", 1).isdigit()

    float_validation = window.register(is_valid_signed_float)
    Balance = Entry(
        window,
        bd=1,
        bg="#FFFFFF",
        fg="#000716",
        font=("VarelaRound Regular", 14 * -1),
        validate="key",
        validatecommand=(float_validation, "%P"),
        highlightthickness=0
    )
    Balance.insert(0, "0")
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

    submit_button = Button(
        window,
        text="Add Client",
        bg="#4F59C1",
        fg="#FFFFFF",
        activebackground="#3F48A6",
        activeforeground="#FFFFFF",
        font=("VarelaRound Regular", 11 * -1),
        bd=0,
        relief="flat",
        cursor="hand2",
        command=save_client_to_db
    )
    submit_button.place(
        x=95.0,
        y=480.0,
        width=290.0,
        height=30.0
    )

    # Pre-populate data if editing an existing party
    if is_edit_mode and client_data:
        # Columns: id, name, contact_no, gst, city, state, client_type, opening_balance, closing_bal
        p_name = client_data[1] or ""
        p_contact = client_data[2] or ""
        p_gst = client_data[3] or ""
        p_city = client_data[4] or ""
        p_state = client_data[5] or "Select"
        p_type = client_data[6] or "Client"
        p_op_bal = str(client_data[7]) if client_data[7] is not None else "0"

        name_entry.insert(0, p_name)
        contect_no_entry.insert(0, p_contact)
        gst_entry.insert(0, p_gst)
        city_entry.insert(0, p_city)
        if p_state in States:
            state_entry.set(p_state)
        dropdown.set(p_type)
        Balance.delete(0, 'end')
        Balance.insert(0, p_op_bal)

    update_text()

    window.resizable(False, False)
    window.bind("<Escape>", lambda event: Top_Close(window, parent))
    window.protocol("WM_DELETE_WINDOW", lambda: Top_Close(window, parent))
    window.wait_window()


def edit_client_ui(client_id, parent=None, on_saved=None):
    """Convenience entry point for editing a party by client_id."""
    return new_client_ui(parent=parent, client_id=client_id, on_saved=on_saved)


if __name__ == "__main__":
    new_client_ui()
