import sys
from pathlib import Path

if getattr(sys, 'frozen', False):  # Running as a PyInstaller EXE
    root_path = Path(sys.executable).parent
else:  # Running as a Python script
    root_path = Path(__file__).parent.parent
sys.path.append(str(root_path))
 
from utilities.path_utils import *

from tkinter import Tk, Canvas, Entry, Text, Button, PhotoImage, messagebox, Menu
from tkinter import ttk
from tkcalendar import DateEntry
from tkinter.ttk import Combobox
import sqlite3
from UI.gui import *


def manage_payments(parent = None):

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
            # Create a Combobox for Client Names
            client_names = fetch_data("""SELECT name FROM Clients""")
            result = [item[0] for item in client_names]

            entry_2 = Combobox(
                window,
                values=result,
                state="readonly",  # Read-only mode to prevent manual input
                font=("VarelaRound Regular", 10)
            )
            entry_2.place(
                x=340.0,
                y=53.0,
                width=325.0,
                height=25.0
            )
            entry_2.set("Select")

        elif selected_option == "Type":
            # Create a Combobox for Client Names
            Types = ["Income", "Expense", "Salaries", "Adjustment"]
            entry_2 = Combobox(
                window,
                values=Types,
                state="readonly",  # Read-only mode to prevent manual input
                font=("VarelaRound Regular", 10)
            )
            entry_2.place(
                x=340.0,
                y=53.0,
                width=325.0,
                height=25.0
            )
            entry_2.set("Select") 

        else:
            entry_2 = DateEntry(window, width=12, background="#000000", foreground="white", borderwidth=2, date_pattern='dd/mm/yyyy', font=("VarelaRound Regular", 13 * -1))
            entry_2.place(
                x=340.0,
                y=53.0,
                width=325.0,
                height=25.0
            )

    def on_double_click(event):
        item = tree.identify_row(event.y)  # Get selected row
        col = tree.identify_column(event.x)  # Get selected column

        if not item or not col:  # Ensure user clicked on a valid cell
            return

        col_index = int(col[1:]) - 1  # Convert column '#2' to index 1, etc.

        if col_index in [0, 1, 2]:  # Prevent editing the "ID" column
            return

        # Get current value & column name
        cur_value = tree.item(item, "values")[col_index]
        col_sql = sql_table[col_index]  # Get actual SQL column name

        # Get cell coordinates
        bbox = tree.bbox(item, col_index)
        if not bbox:  # Prevent errors if bbox is empty
            return

        # Function to save new value
        def save_edit(event):
            new_value = entry.get()

            if new_value == cur_value or new_value == "":  # Ignore unchanged or empty values
                entry.destroy()
                return

            tree.set(item, column=columns[col_index], value=new_value)
            entry.destroy()  # Remove entry field

            # Update database
            row_id = tree.item(item, "values")[0]  # Get ID column
            run_query(f"UPDATE Payments SET {col_sql} = ? WHERE payment_id = ?", (new_value, row_id))


        
        entry = tk.Entry(tree, font=("VarelaRound Regular", 12 * -1))
        entry.insert(0, cur_value)
        entry.focus()
        entry.place(x=bbox[0], y=bbox[1], width=bbox[2], height=bbox[3])

        entry.bind("<<ComboboxSelected>>", save_edit)  # Save when an option is selected
        entry.bind("<FocusOut>", lambda e: entry.destroy())  # Destroy when focus is lost

    def search():
        try:
            type = entry_1.get()

            if not type or type == "Select":
                return
            
            global entry_2
            search = entry_2.get()

            conditions = {
                "Name": "client_name",
                "Type": "entity_type",
                "Date": "date"
            }

            if type not in conditions:
                messagebox.showinfo("Error", "Invalid type selected", parent=window)
                return

            column = conditions[type]
            query = f"""
            SELECT 
                payment_id, 
                c.name AS client_name, 
                Expanse_type, 
                date, 
                total_amount, 
                payment_mode, 
                reference_no
            FROM 
                Payments p
            JOIN 
                Clients c ON p.entity_id = c.id
            WHERE
                {column} = '{search}'
            """

            result = fetch_data(query)

            for row in tree.get_children():
                tree.delete(row)

            # Insert the filtered data into the treeview
            for row in result:
                tree.insert("", "end", values=row)

        except Exception as e:
            messagebox.showinfo("Error", f"Error fetching clients: {e}", parent=window)
            return
       
    def reset():
        entry_1.delete(0, tk.END)
        entry_1.set("Select")        
        
        for widget in window.winfo_children():
            if widget.winfo_name() == 'entry_2':
                widget.destroy()

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


        entry_2.delete(0, tk.END)
        tree.delete(*tree.get_children())

        query = """            
            SELECT 
                payment_id, 
                c.name AS client_name, 
                Expanse_type, 
                date, 
                total_amount, 
                payment_mode, 
                reference_no
            FROM 
                Payments p
            JOIN 
                Clients c ON p.entity_id = c.id
        """
        data = fetch_data(query)

        for row in data:
            tree.insert("", "end", values=row)

    def delete_row(selected_item):
        # Get the ID from the selected row (assuming the ID is in the first column)
        item_values = tree.item(selected_item, "values")
        item_id = item_values[0]  # ID column value
        
        # Confirm deletion
        result = messagebox.askyesno("Delete", f"Are you sure you want to delete Payment with ID {item_id}?", parent=window)
        if result:
            try:
                # Execute the SQL to delete the record from the database
                run_query("DELETE FROM Payments WHERE payment_id = ?", (item_id,))
                
                # Delete the row from the Treeview
                tree.delete(selected_item)
                messagebox.showinfo("Deleted", "Payment successfully deleted.", parent=window)
            except sqlite3.Error as e:
                messagebox.showerror("Error", f"Failed to delete Payment: {e}", parent=window)        

    def show_right_click_menu(event):
        # Get selected item
        selected_item = tree.selection()
        
        if selected_item:
            # Create the context menu
            menu = tk.Menu(window, tearoff=0)
            menu.add_command(label="Delete", command=lambda: delete_row(selected_item))
            menu.post(event.x_root, event.y_root)


    window = tk.Toplevel(parent)
    window.focus()
    window.iconbitmap(generate_path("UI", "assets", "BillMates.ico"))
    window.transient(parent)
    window.grab_set()
    
    window.title("Manage Payments")
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
        values=["Name", "Type", "Date"],
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
        command= search,
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
        file=relative_to_assets("button_4.png"))
    button_3 = Button(
        window,
        image=button_image_3,
        borderwidth=0,
        highlightthickness=0,
        relief="flat"
    )
    button_3.place(
        x=937.0,
        y=48.0,
        width=202.0,
        height=30.0
    )
    def toggle_submenu(menu, button):
        x = button.winfo_rootx()
        y = button.winfo_rooty() + button.winfo_height()
        menu.post(x, y)
    Dropdown = Menu(window, tearoff=0, bg="white", fg="black", font=("Poppins", 10, "normal"))
    Dropdown.add_command(label="  Add Invoice Payments   ", command=lambda: customer_payment_in(parent = window))
    Dropdown.add_command(label="  Add Purchase Payments   ", command=lambda: supplier_payments_out(parent = window))
    Dropdown.add_command(label="  Add Expance Payments    ", command=lambda: expense_payments_out(parent = window))
    Dropdown.add_command(label="  Add Adjustment         ", command=lambda: new_adjustment_ui(parent = window))
    Dropdown.add_command(label="  Payment Getway          ", command=lambda: payment_getway(parent = window))
    Dropdown.add_command(label="  Add Salery Payments     ", command=lambda: pay_salery_ui(parent = window))
    button_3.config(command=lambda: toggle_submenu(Dropdown, button_3))
    

    # Define columns and their respective widths
    columns = ["ID", "Name", "Payment Type", "Date", "Amount", "Mode", "Reference No"]
    widths = [80, 220, 150, 150, 150, 150, 165]  # Adjust width for each column
    sql_table = ["payment_id", "name", "Expanse_type", "date", "total_amount", "payment_mode", "reference_no"]

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
    style.configure("Treeview", rowheight=30)

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


    treeData = """
    SELECT 
        payment_id, 
        c.name AS client_name, 
        Expanse_type, 
        date, 
        total_amount, 
        payment_mode, 
        reference_no
    FROM 
        Payments p
    JOIN 
        Clients c ON p.entity_id = c.id;
    """
    data = fetch_data(treeData)

    for row in data:
        tree.insert("", "end", values=row)

    tree.bind("<Double-1>", on_double_click)
    tree.bind("<Button-3>", show_right_click_menu)

    window.resizable(False, False)
    window.bind("<Escape>", lambda event: Top_Close(window, parent))
    window.protocol("WM_DELETE_WINDOW", lambda: Top_Close(window, parent))
    window.bind("<Return>", lambda event: search())
    window.mainloop()


    
if __name__ == "__main__":
    manage_payments()
