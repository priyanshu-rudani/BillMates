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
from utilities import text

# UI
from UI.AddChequeBook import addChequeBook_ui

def Manage_chequeBook(parent = None):

    ASSETS_PATH = Path(generate_path(root_path, "UI", "assets", "frame6"))
    
    def relative_to_assets(path: str) -> Path:
        return ASSETS_PATH / Path(path)
    
    def on_close(*args):
        window.grab_release()
        window.destroy()
        
    def update_search_field(event):
        global entry_2
        global entry_1
        selected_option = entry_1.get()
        # Destroy the previous widget (Entry or Combobox)
        for widget in window.winfo_children():
            if widget.winfo_name() == 'entry_2':
                widget.destroy()

        if selected_option == "Bank Name":

            entry_2 = Combobox(
                window,
                values=text.Banks,
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

    def on_double_click(event):
        from UI.AddChequeBook import addChequeBook_ui 

        selected_item = tree.selection()
        if selected_item:
            row_data = tree.item(selected_item, "values")
            chequeBook_id = row_data[0]

            for row in tree.get_children():
                tree.delete(row)

            addChequeBook_ui(chequeBook_id, window)

            return
        return
        
    def search():
        try:
            global entry_1
            global entry_2
            type = str(entry_1.get())
            search = str(entry_2.get())
            
            if not type or type == "Select":
                return
        
            query_map = {
                "ID": "id",
                "ChequeBook Name": "book_name",
                "Bank Name": "bank_name",
                "Holder Name": "holder_name"
            }
            
            if type == "All ChequeBooks":
                query = f"SELECT id, book_name, bank_name, holder_name, account_no, starting_ChequeNo, Current_ChequeNo, total_cheques, issued_date FROM ChequeBook"
                result = fetch_data(query, db='Cheque.db')
            else: 
                query = f"SELECT id, book_name, bank_name, holder_name, account_no, starting_ChequeNo, Current_ChequeNo, total_cheques, issued_date FROM ChequeBook WHERE {query_map[type]} LIKE '%' || '{search}' || '%'"
                result = fetch_data(query, db='Cheque.db')
            
            # Clear current treeview data
            tree.delete(*tree.get_children())

            if result:
                for row in result:
                    tree.insert("", "end", values=row)
            else:
                messagebox.showinfo("Error", f"No result Found", parent=window)
        except Exception as e:
                messagebox.showinfo("Error", f"Error fetching ChequeBook: {e}", parent=window)
        
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

        tree.delete(*tree.get_children())

        query = f"SELECT id, book_name, bank_name, holder_name, account_no, starting_ChequeNo, Current_ChequeNo, total_cheques, issued_date FROM ChequeBook"
        data = fetch_data(query, db='Cheque.db')

        for row in data:
            tree.insert("", "end", values=row)

    def delete_row(selected_item):
        # Get the ID from the selected row (assuming the ID is in the first column)
        item_values = tree.item(selected_item, "values")
        id = item_values[0] # ID column value
        bookName = item_values[1]  
        
        # Confirm deletion
        result = messagebox.askyesno("Delete", f"Are you sure you want to delete ChequeBook with Name {bookName}?", parent=window)
        if result:
            try:

                run_query(f"DELETE FROM Cheques WHERE cheque_book_id = {id}", db='Cheque.db')
                run_query(f"DELETE FROM ChequeBook WHERE id = {id}", db='Cheque.db')

                tree.delete(selected_item)
                messagebox.showinfo("Deleted", "ChequeBook successfully deleted.", parent=window)
            except sqlite3.Error as e:
                messagebox.showerror("Error", f"Failed to delete ChequeBook: {e}", parent=window)

    def show_right_click_menu(event):
        # Get selected item
        selected_item = tree.selection()
        
        if selected_item:
            # Create the context menu
            menu = tk.Menu(window, tearoff=0)
            menu.add_command(label="   Delete Cheque   ", command=lambda: delete_row(selected_item))
            menu.post(event.x_root, event.y_root)


    window = tk.Toplevel(parent)
    window.focus()
    window.iconbitmap(generate_path("UI", "assets", "BillMates.ico"))

    window.transient(parent)
    window.grab_set() 
    
    window.title("Manage ChequeBooks")
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

    global entry_1
    entry_1 = None
    entry_1 = Combobox(
        window,
        values=["All ChequeBooks", "ID", "ChequeBook Name", "Bank Name", "Holder Name"],
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
        file=relative_to_assets("button_5.png"))
    button_3 = Button(
        window,
        image=button_image_3,
        borderwidth=0,
        highlightthickness=0,
        command=addChequeBook_ui,
        relief="flat"
    )
    button_3.place(
        x=937.0,
        y=48.0,
        width=202.0,
        height=30.0
    )
    
    # Define columns and their respective widths
    columns = ["ID", "ChequeBook", "Bank Name", "Holder Name", "Account no.", "Starting Cheque No", "Current Cheque No", "Total Cheque No", "Issued Date"]
    widths = [80, 200, 200, 180, 180, 150, 150, 150, 150]
    sql_table = ["id", "book_name", "bank_name", "holder_name", "account_no", "starting_ChequeNo", "Current_ChequeNo", "total_cheques", "issued_date"]

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


    query = f"SELECT id, book_name, bank_name, holder_name, account_no, starting_ChequeNo, Current_ChequeNo, total_cheques, issued_date FROM ChequeBook"
    data = fetch_data(query, db='Cheque.db')

    for row in data:
        tree.insert("", "end", values=row)

    tree.bind("<Double-1>", on_double_click)
    tree.bind("<Button-3>", show_right_click_menu)

    window.bind('<Control-n>', lambda event: addChequeBook_ui())
    window.bind("<Return>", lambda event: search())

    window.resizable(False, False)
    window.bind("<Escape>", on_close)
    window.protocol("WM_DELETE_WINDOW", on_close)
    window.mainloop()


if __name__ == "__main__":
    Manage_chequeBook()