import sys
from pathlib import Path

if getattr(sys, 'frozen', False):  # Running as a PyInstaller EXE
    root_path = Path(sys.executable).parent
else:  # Running as a Python script
    root_path = Path(__file__).parent.parent
sys.path.append(str(root_path))
 
from utilities.path_utils import *

from tkinter import Canvas, Entry, Button, PhotoImage, messagebox
from tkinter import ttk
from tkinter.ttk import Combobox
import sqlite3

# UI
from UI.addClient import new_client_ui

def manage_clients(parent = None):

    ASSETS_PATH = Path(generate_path(root_path, "UI", "assets", "frame6"))
    
    def relative_to_assets(path: str) -> Path:
        return ASSETS_PATH / Path(path)
        
    def update_search_field(event):
        global entry_2
        selected_option = entry_1.get()
        # Destroy the previous widget (Entry or Combobox)
        for widget in window.winfo_children():
            if widget.winfo_name() == 'entry_2':
                widget.destroy()

        if selected_option == "Name":
            # Fetch all party names (Clients, Suppliers, Staff)
            client_names = [r[0] for r in fetch_data("SELECT DISTINCT name FROM Clients ORDER BY name ASC")]
            entry_2 = Combobox(
                window,
                values=client_names,
                state="readonly",
                font=("VarelaRound Regular", 10)
            )
            entry_2.place(
                x=340.0,
                y=53.0,
                width=325.0,
                height=25.0
            )
            entry_2.set("Select")
            entry_2.bind("<<ComboboxSelected>>", lambda e: search())

        elif selected_option == "Type":
            client_types = ["Client", "Supplier", "Staff"]
            entry_2 = Combobox(
                window,
                values=client_types,
                state="readonly",
                font=("VarelaRound Regular", 10)
            )
            entry_2.place(
                x=340.0,
                y=53.0,
                width=325.0,
                height=25.0
            )
            entry_2.set("Select")     
            entry_2.bind("<<ComboboxSelected>>", lambda e: search())

        else:
            entry_2 = Entry(
                window,
                bd=1,
                relief="solid",
                bg="#FFFFFF",
                fg="#000716",
                highlightthickness=0
            )
            entry_2.place(
                x=340.0,
                y=53.0,
                width=325.0,
                height=25.0
            )
            entry_2.bind("<Return>", lambda e: search())

            if selected_option == "Contact Number":
                quary = """SELECT DISTINCT contact_no FROM Clients WHERE contact_no IS NOT NULL AND contact_no != ''"""
            elif selected_option == "City":
                quary = """SELECT DISTINCT city FROM Clients WHERE city IS NOT NULL AND city != ''"""
            elif selected_option == "ID":
                quary = """SELECT DISTINCT id FROM Clients ORDER BY id ASC"""
            else:
                quary = None
                
            if quary is not None:
                data = [str(row[0]) for row in fetch_data(quary)]
                listbox = tk.Listbox(window, font=("VarelaRound Regular", 14 * -1), height=min(len(data), 6))
                SearchBox(entry_2, listbox, data)


    def refresh_table():
        query = "SELECT id, name, contact_no, gst, city, state, client_type, closing_bal FROM Clients"
        data = fetch_data(query)
        populate_tree(data)

    def open_edit_party(selected_item=None):
        if not selected_item:
            selected_item = tree.selection()
            if selected_item:
                selected_item = selected_item[0]
        if not selected_item:
            return
        item_values = tree.item(selected_item, "values")
        if not item_values:
            return
        client_id = item_values[0]
        new_client_ui(parent=window, client_id=client_id, on_saved=refresh_table)

    def on_double_click(event):
        item = tree.identify_row(event.y)
        if not item:
            return
        tree.selection_set(item)
        open_edit_party(item)


    def populate_tree(records):
        tree.delete(*tree.get_children())
        for row in records:
            tree.insert("", "end", values=row)

    def search():
        try:
            search_type = entry_1.get().strip() if entry_1.get() else ""
            search_term = entry_2.get().strip() if entry_2 and entry_2.get() else ""

            if not search_type or search_type == "Select":
                return

            base_query = "SELECT id, name, contact_no, gst, city, state, client_type, closing_bal FROM Clients"

            if search_type == "All":
                result = fetch_data(base_query)
            else:
                query_map = {
                    "ID": "id",
                    "Name": "name",
                    "Contact Number": "contact_no",
                    "City": "city",
                    "Type": "client_type"
                }

                column = query_map.get(search_type)
                if not column:
                    return

                if not search_term or search_term == "Select":
                    # If field is blank, show all records rather than erroring out
                    result = fetch_data(base_query)
                elif search_type == "ID":
                    # Exact numeric/ID match
                    query = f"{base_query} WHERE id = ?"
                    result = fetch_data(query, (search_term,))
                elif search_type == "Type":
                    # Exact category match (Client, Supplier, Staff)
                    query = f"{base_query} WHERE client_type = ?"
                    result = fetch_data(query, (search_term,))
                else:
                    # Case-insensitive partial matching for Name, Contact Number, City
                    query = f"{base_query} WHERE {column} LIKE ?"
                    result = fetch_data(query, (f"%{search_term}%",))

            populate_tree(result)

            if not result:
                messagebox.showinfo("No Results", "No matching clients found.", parent=window)

        except Exception as e:
            messagebox.showerror("Error", f"Error searching clients: {e}", parent=window)

    def reset():
        entry_1.set("Select")
        update_search_field(None)
        data = fetch_data("SELECT id, name, contact_no, gst, city, state, client_type, closing_bal FROM Clients")
        populate_tree(data)


    def delete_row(selected_item):
        # Get the ID from the selected row (assuming the ID is in the first column)
        item_values = tree.item(selected_item, "values")
        item_id = item_values[0]  # ID column value
        
        # Confirm deletion
        result = messagebox.askyesno("Delete", f"Are you sure you want to delete Client with ID {item_id}?", parent=window)
        if result:
            try:
                # Execute the SQL to delete the record from the database
                run_query("DELETE FROM Clients WHERE id = ?", (item_id,))
                run_query("DELETE FROM Payments WHERE entity_id = ?", (item_id,))
                run_query("DELETE FROM Invoices WHERE client_id = ?", (item_id,))
                run_query("DELETE FROM InvoiceItems WHERE client_id = ?", (item_id,))
                run_query("DELETE FROM Purchase WHERE client_id = ?", (item_id,))
                run_query("DELETE FROM PurchaseItems WHERE client_id = ?", (item_id,))
                
                # Delete the row from the Treeview
                tree.delete(selected_item)
                messagebox.showinfo("Deleted", "Client successfully deleted.", parent=window)
            except sqlite3.Error as e:
                messagebox.showerror("Error", f"Failed to delete Client: {e}", parent=window)

    def show_right_click_menu(event):
        # Identify row under cursor if not already selected
        row_id = tree.identify_row(event.y)
        if row_id:
            tree.selection_set(row_id)
        selected_item = tree.selection()
        
        if selected_item:
            menu = tk.Menu(window, tearoff=0)
            menu.add_command(label="Edit", command=lambda: open_edit_party(selected_item[0]))
            menu.add_command(label="Delete", command=lambda: delete_row(selected_item[0]))
            menu.post(event.x_root, event.y_root)


    window = tk.Toplevel(parent)
    window.focus()
    window.iconbitmap(generate_path("UI", "assets", "BillMates.ico"))

    window.transient(parent)
    window.grab_set()
    
    window.title("Manage Partys")
    center_window(window, 1224, 640)
    window.configure(bg = "#E7EBFF")


    canvas = Canvas(
        window,
        bg = "#E7EBFF",
        height = 640,
        width = 1224,
        bd = 0,
        highlightthickness = 0,
        relief = "ridge"
    )

    canvas.place(x = 0, y = 0)
    canvas.create_text(
        84.0,
        34.0,
        anchor="nw",
        text="Search as",
        fill="#000000",
        font=("VarelaRound Regular", 12 * -1)
    )


    entry_1 = Combobox(
        window,
        values=["All", "ID", "Name", "Contact Number", "City", "Type"],
        state="readonly",
        font=("VarelaRound Regular", 12 * -1)
    )
    entry_1.set("Select")
    entry_1.place(
        x=84.0,
        y=53.0,
        width=215.0,
        height=25.0
    )

    canvas.create_text(
        340.0,
        34.0,
        anchor="nw",
        text="Search",
        fill="#000000",
        font=("VarelaRound Regular", 12 * -1)
    )

    entry_1.bind("<<ComboboxSelected>>", update_search_field)

    global entry_2
    entry_2 = None
    entry_2 = Entry(
        window,
        bd=1,
        relief="solid",
        bg="#FFFFFF",
        fg="#000716",
        font=("VarelaRound Regular", 10 * -1),
        highlightthickness=0
    )
    entry_2.place(
        x=340.0,
        y=53.0,
        width=325.0,
        height=25.0
    )




    button_image_1 = PhotoImage(
        file=relative_to_assets("button_1.png"))
    button_1 = Button(
        window,
        image=button_image_1,
        borderwidth=0,
        highlightthickness=0,
        command=search,
        relief="flat"
    )
    button_1.place(
        x=706.0,
        y=48.0,
        width=85.0,
        height=30.0
    )

    button_image_2 = PhotoImage(
        file=relative_to_assets("button_2.png"))
    button_2 = Button(
        window,
        image=button_image_2,
        borderwidth=0,
        highlightthickness=0,
        command=reset,
        relief="flat"
    )
    button_2.place(
        x=811.0,
        y=48.0,
        width=85.0,
        height=30.0
    )

    button_image_3 = PhotoImage(
        file=relative_to_assets("button_3.png"))
    button_3 = Button(
        window,
        image=button_image_3,
        borderwidth=0,
        highlightthickness=0,
        command=lambda: new_client_ui(parent=window, on_saved=refresh_table),
        relief="flat"
    )
    button_3.place(
        x=937.0,
        y=48.0,
        width=202.0,
        height=30.0
    )

    # Define columns and their respective widths
    columns = ["ID", "Name", "Contact No", "GST No.", "City", "State", "Client Type", "Balance"]
    widths = [50, 220, 150, 150, 150, 150, 150, 165]  # Adjust width for each column
    sql_table = ["id", "name", "contact_no", "gst", "city", "state", "client_type", "closing_bal"]

    # Create Frame for Treeview
    frame = tk.Frame(window, bg="#FFFFFF")
    frame.place(x=29, y=121, width=1165, height=490)  # Adjust width and height for padding

    # Create Treeview
    tree = ttk.Treeview(frame, columns=columns, show="headings")

    # Define columns and their width
    for col, width in zip(columns, widths):
        tree.heading(col, text=col)
        tree.column(col, width=width, anchor="center")

    style = ttk.Style()
    style.configure("Treeview", rowheight=25)

    # Add Scrollbars
    vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    hsb = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

    # Positioning Widgets
    tree.grid(row=0, column=0, sticky="nsew")
    vsb.grid(row=0, column=1, sticky="ns")
    hsb.grid(row=1, column=0, sticky="ew")

    # Grid configuration to allow resizing
    frame.grid_rowconfigure(0, weight=1)
    frame.grid_columnconfigure(0, weight=1)


    query = """SELECT id, name, contact_no, gst, city, state, client_type, closing_bal FROM Clients"""
    data = fetch_data(query)

    for row in data:
        tree.insert("", "end", values=row)

    tree.bind("<Double-1>", on_double_click)
    tree.bind("<Button-3>", show_right_click_menu)

    window.bind("<Return>", lambda event: search())

    window.resizable(False, False)
    window.bind("<Escape>", lambda event: Top_Close(window, parent))
    window.protocol("WM_DELETE_WINDOW", lambda: Top_Close(window, parent))
    window.wait_window()


if __name__ == "__main__":
    manage_clients()