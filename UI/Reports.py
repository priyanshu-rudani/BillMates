import sys
from pathlib import Path

if getattr(sys, 'frozen', False):  # Running as a PyInstaller EXE
    root_path = Path(sys.executable).parent
else:  # Running as a Python script
    root_path = Path(__file__).parent.parent
sys.path.append(str(root_path))
 
from utilities.path_utils import *

from tkinter import Tk
from tkinter import ttk, Canvas, Frame, messagebox, Button, PhotoImage, NORMAL, DISABLED, HORIZONTAL, VERTICAL
from tkinter import Menu
from tkinter.ttk import Combobox
from tkcalendar import DateEntry
from datetime import datetime, timedelta, date
from utilities.GenerateReport import *
from UI.gui import *



ASSETS_PATH = Path(generate_path(root_path, "UI", "assets", "frame7"))


def relative_to_assets(path: str) -> Path:
    return ASSETS_PATH / Path(path)

def Reports_ui(parent = None):
    
    def get_date_range():
        query = """
            SELECT DISTINCT date 
            FROM Invoices
            UNION 
            SELECT DISTINCT date 
            FROM Purchase
            UNION 
            SELECT DISTINCT date 
            FROM Payments
        """

        dates = [row[0] for row in fetch_data(query)]

        parsed_dates = [datetime.strptime(date, '%d/%m/%Y') for date in dates]

        min_date = min(parsed_dates)
        max_date = max(parsed_dates)

        # Format the results back to dd/mm/yyyy
        min_date_str = min_date.strftime('%d/%m/%Y')
        max_date_str = max_date.strftime('%d/%m/%Y')

        return min_date_str, max_date_str

    def update_dates(event):
        if start_date is None or end_date is None:
            return

        selected_option = quick_date.get()
        selected_report = report_type.get()
        today = datetime.now()

        Min_date, max_date = get_date_range()

        if selected_option == "All":
            start_date.set_date(Min_date)
            end_date.set_date(max_date)
            start_date.configure(state=DISABLED)
            end_date.configure(state=DISABLED)

        elif selected_option == "Today":
            start_date.configure(state="readonly")
            end_date.configure(state="readonly")
            start_date.set_date(today)
            end_date.set_date(today)
            
        elif selected_option == "Last 7 Days":
            start_date.configure(state="readonly")
            end_date.configure(state="readonly")
            start_date.set_date(today - timedelta(days=7))
            end_date.set_date(today)

        elif selected_option == "Last 30 Days":
            start_date.configure(state="readonly")
            end_date.configure(state="readonly")
            start_date.set_date(today - timedelta(days=30))
            end_date.set_date(today)

        elif selected_option == "This Week":
            start_date.configure(state="readonly")
            end_date.configure(state="readonly")
            start_date.set_date(today - timedelta(days=today.weekday()))
            end_date.set_date(today + timedelta(days=6 - today.weekday())) 

        elif selected_option == "This Month":
            start_date.configure(state="readonly")
            end_date.configure(state="readonly")
            start_date.set_date(today.replace(day=1))
            next_month = today.replace(day=28) + timedelta(days=4)
            last_day_of_month = next_month - timedelta(days=next_month.day)
            end_date.set_date(last_day_of_month)

        elif selected_option == "This Year":
            start_date.configure(state="readonly")
            end_date.configure(state="readonly")
            start_date.set_date(today.replace(month=1, day=1))
            end_date.set_date(today.replace(month=12, day=31))

        elif selected_option == "Last Week":
            start_date.configure(state="readonly")
            end_date.configure(state="readonly")
            start_date.set_date(today - timedelta(days=today.weekday() + 7))
            end_date.set_date(start_date.get_date() + timedelta(days=6))

        elif selected_option == "Last Month":
            start_date.configure(state="readonly")
            end_date.configure(state="readonly")
            first_day_of_this_month = today.replace(day=1)
            last_day_of_last_month = first_day_of_this_month - timedelta(days=1)
            start_date.set_date(last_day_of_last_month.replace(day=1))
            end_date.set_date(last_day_of_last_month)

        elif selected_option == "Last Year":
            start_date.configure(state="readonly")
            end_date.configure(state="readonly")
            start_date.set_date(today.replace(year=today.year - 1, month=1, day=1))
            end_date.set_date(today.replace(year=today.year - 1, month=12, day=31))
        
        elif selected_option == "Financial Year":
            start_date.configure(state="readonly")
            end_date.configure(state="readonly")

            current_year = date.today().year
            current_month = date.today().month

            if current_month >= 4:  # If current month is April or later
                start_date_ = datetime(current_year, 4, 1)
                end_date_year = current_year + 1
                end_date_ = datetime(end_date_year, 3, 31)
            else:  # If current month is before April (Jan, Feb, Mar)
                start_date_ = datetime(current_year - 1, 4, 1)
                end_date_year = current_year
                end_date_ = datetime(end_date_year, 3, 31)
                
            start_date.set_date(start_date_)
            end_date.set_date(end_date_)
        
        if selected_report == "Profit and Loss Statement":
            start_date.configure(state=DISABLED)
            end_date.configure(state=DISABLED)
        elif selected_report == "Cash Flow Statement":
            start_date.configure(state=DISABLED)
            end_date.configure(state=DISABLED)
                
    def enable_fields(event):
        selected_option = report_type.get()
        date_options = [
            "All",
            "Today",
            "Last 7 Days",
            "Last 30 Days",
            "This Week",
            "This Month",
            "This Year",
            "Last Week",
            "Last Month",
            "Last Year",
            "Custom Range"
            ]

        if selected_option == "Sales Reports":
            start_date.configure(state='readonly')
            end_date.configure(state='readonly')
            start_date.set_date(datetime.now())
            end_date.set_date(datetime.now())
            quick_date.configure(values=date_options)
            Client_type.configure(values="Client")
            Client_type.set("Client")
            client_names = fetch_client_names("Client")
            Client.set("Select")
            Client['values'] = client_names
            Client_type.configure(state=DISABLED)
            Client.configure(state='readonly')

        elif selected_option == "Client Payment Reports":
            start_date.configure(state='readonly')
            end_date.configure(state='readonly')
            start_date.set_date(datetime.now())
            end_date.set_date(datetime.now())
            quick_date.configure(values=date_options)
            Client_type.configure(state="readonly")
            Client.configure(state="readonly")
            Client_type.configure(values=["Client", "Supplier"])

        elif selected_option == "Client Ledger":
            start_date.configure(state='readonly')
            end_date.configure(state='readonly')
            start_date.set_date(datetime.now())
            end_date.set_date(datetime.now())
            quick_date.configure(values=date_options)
            Client_type.configure(state="readonly")
            Client.configure(state="readonly")
            Client_type.configure(values=["Client", "Supplier"])

        elif selected_option == "Purchase Reports":
            start_date.configure(state='readonly')
            end_date.configure(state='readonly')
            start_date.set_date(datetime.now())
            end_date.set_date(datetime.now())
            quick_date.configure(values=date_options)
            Client_type.configure(values="Supplier")
            Client_type.set("Supplier")
            client_names = fetch_client_names("Supplier")
            Client.set("Select")
            Client['values'] = client_names
            Client_type.configure(state=DISABLED)
            Client.configure(state='readonly')

        elif selected_option == "Revenue Reports":
            start_date.configure(state='readonly')
            end_date.configure(state='readonly')
            start_date.set_date(datetime.now())
            end_date.set_date(datetime.now())
            quick_date.configure(values=date_options)
            Client_type.configure(values=["Client", "Supplier"])
            Client_type.set("Select")
            Client.set("Select")
            Client_type.configure(state=DISABLED)
            Client.configure(state=DISABLED)


        elif selected_option == "Expense Analysis":
            start_date.configure(state='readonly')
            end_date.configure(state='readonly')
            start_date.set_date(datetime.now())
            end_date.set_date(datetime.now())
            quick_date.configure(values=date_options)
            Client_type.configure(values=["Client", "Supplier"])
            Client_type.set("Select")
            Client.set("Select")
            Client_type.configure(state=DISABLED)
            Client.configure(state=DISABLED)
            
        elif selected_option == "Cash Flow Statement":
            start_date.configure(state=DISABLED)
            end_date.configure(state=DISABLED)
            start_date.set_date(datetime.now())
            end_date.set_date(datetime.now())
            date_options = [
                "This Month",
                "This Year",
                "Last Month",
                "Last Year",
                "Financial Year",
            ]
            quick_date.configure(values=date_options)
            Client_type.configure(values=["Client", "Supplier"])
            Client_type.set("Select")
            Client.set("Select")
            Client_type.configure(state=DISABLED)
            Client.configure(state=DISABLED)
            
        elif selected_option == "Profit and Loss Statement":
            start_date.configure(state=DISABLED)
            end_date.configure(state=DISABLED)
            start_date.set_date(datetime.now())
            end_date.set_date(datetime.now())
            date_options = [
                "This Month",
                "This Year",
                "Last Month",
                "Last Year",
            ]
            quick_date.configure(values=date_options)
            Client_type.configure(values=["Client", "Supplier"])
            Client_type.set("Select")
            Client.set("Select")
            Client_type.configure(state=DISABLED)
            Client.configure(state=DISABLED)

    def reset_data():
        report_type.set("Select Report")
        start_date.set_date(datetime.now().strftime("%d/%m/%Y"))
        end_date.set_date(datetime.now().strftime("%d/%m/%Y"))
        quick_date.set("Select")
        Client_type.set("Select")
        Client.set("Select")
        Client_type.configure(state=DISABLED)
        Client.configure(state=DISABLED)

        tree = Treeview
        # Clear existing data and columns
        for row in tree.get_children():
            tree.delete(row)

    def export_as_excel():
        report_type_value = report_type.get()
        start_date_value = start_date.get()
        end_date_value = end_date.get()
        client_value = Client.get()

        if report_type_value == "Select Report":
            messagebox.showerror("Error", "Please select a report type", parent=window)
            return

        if start_date_value is None:
            messagebox.showerror("Error", "Please select a Starting date", parent=window)
            return

        if end_date_value is None:
            messagebox.showerror("Error", "Please select a Ending date", parent=window)
            return

        if client_value == "Select":
            if report_type_value in ["Sales Reports", "Purchase Reports", "Client Payment Reports", "Client Ledger"]:
                messagebox.showerror("Error", "Please select a client", parent=window)
                return
            export_report(report_type_value, start_date_value, end_date_value)
        else:
            export_report(report_type_value, start_date_value, end_date_value, client_value)

    def export_as_pdf():
        messagebox.showerror("Upcoming Feature", "Export To PDF feature is coming soon", parent=window)
    

    window = tk.Toplevel(parent)
    window.focus()
    window.iconbitmap(generate_path("UI", "assets", "BillMates.ico"))

    window.transient(parent)
    window.grab_set()
    
    window.title("Reports Manager")
    center_window(window, 1280, 720)
    window.configure(bg = "#E7EBFF")

    def update_treeview(columns, data, column_widths=None, exclude_last_n_rows=0):
        tree = Treeview
        # Clear existing data and columns
        for row in tree.get_children():
            tree.delete(row)

        tree["columns"] = columns

        # Configure column headers
        tree.heading("#0", text="", anchor="center")  # Hide default first column
        tree.column("#0", width=0, stretch="no")  # Hide the empty column

        if exclude_last_n_rows > 0:
            data = data[:-exclude_last_n_rows]

        for col in columns:
            tree.heading(col, text=col, anchor="center")
            tree.column(col, anchor="center", width=150)

        for idx, col in enumerate(columns):
            # Set column widths if provided, else default to 150
            width = column_widths[idx] if column_widths and idx < len(column_widths) else 10
            tree.heading(col, text=col, anchor="center")  # Configure column heading
            tree.column(col, anchor="center", width=width)  # Configure column width and alignment


        for row in data:
            tree.insert("", "end", values=row)

    def fetch_and_display_data():
        report_type_value = report_type.get()
        starting_date = start_date.get()
        ending_date = end_date.get()
        client_name = Client.get() if Client.get() else None

        if starting_date is None:
            messagebox.showerror("Error", "Please select dates", parent=window)
            return
        
        if ending_date is None:
            messagebox.showerror("Error", "Please select dates", parent=window)
            return

        if report_type_value == "Select Report":
            messagebox.showerror("Error", "Please select a report type", parent=window)
            return

        elif report_type_value == 'Sales Reports':  
            if client_name == 'Select' or client_name == None:
                messagebox.showerror("Error", "Please select a client", parent=window)
                return
            columns  = ["Invoice No.", "Date", "Client Name", "Total", "Paid", "Remaining", "Paid Status", "Reference No."]
            data = customer_sales(client_name, starting_date, ending_date)
            update_treeview(columns, data, exclude_last_n_rows = 4)

        elif report_type_value == 'Purchase Reports':
            if client_name == 'Select' or client_name == None:
                messagebox.showerror("Error", "Please select a client", parent=window)
                return
            columns  = ["Invoice No.", "Date", "Suppiler Name", "Total", "Paid", "Unpaid", "Paid Status", "Reference No."]
            data = purchase_report(client_name, starting_date, ending_date)
            update_treeview(columns, data, exclude_last_n_rows = 4)

        elif report_type_value == 'Client Payment Reports':
            if client_name == 'Select' or client_name == None:
                messagebox.showerror("Error", "Please select a client", parent=window)
                return
            columns  = ["Date", "Payment Type", "Client Name", "Total Amount", "Payment Mode", "Reference No."]
            data = customer_payment(client_name, starting_date, ending_date)
            column_widths = [100, 200, 50, 150]
            update_treeview(columns, data, exclude_last_n_rows = 4)

        elif report_type_value == 'Client Ledger':
            if client_name == 'Select' or client_name == None:
                messagebox.showerror("Error", "Please select a client", parent=window)
                return
            columns  = ["Date", "Description", "Credited", "Debited", "Balance"]
            data = customer_ledger(client_name, starting_date, ending_date)
            update_treeview(columns, data)

        elif report_type_value == 'Cash Flow Statement':
            columns  = ["Date", "Client Name", "Payment Category", "Total", "Payment Mode", "Payment Type", "Reference No."]
            data = cashflow_report(starting_date, ending_date)
            update_treeview(columns, data, exclude_last_n_rows = 4)

        elif report_type_value == 'Profit and Loss Statement':
            columns  = ["Sr No.", "Category", " ", "Amount"]
            data = profit_loss_report(starting_date, ending_date)
            update_treeview(columns, data, exclude_last_n_rows = 0, column_widths = [150, 600, 200, 350])

        elif report_type_value == 'Revenue Reports':
            columns  = ["Payment Date", "Payment Type", "Client Name", "Amount", "Payment Status", "Reference no."]
            data = revenue_report(starting_date, ending_date)
            update_treeview(columns, data, exclude_last_n_rows = 4)

        elif report_type_value == 'Expense Analysis':
            columns  = ["Date", "Expense Type", "Client Name", "Amount", "Payment Mode", "Reference no."]
            data = expense_analysis(starting_date, ending_date)
            update_treeview(columns, data, exclude_last_n_rows = 4)
        else:
            columns = []
            data = []
            return

        if not columns or not data:
            messagebox.showerror("Error", "No data available for the selected report.", parent=window)
            return

    canvas = Canvas(
        window,
        bg = "#E7EBFF",
        height = 720,
        width = 1280,
        bd = 0,
        highlightthickness = 0,
        relief = "ridge"
    )

    canvas.place(x = 0, y = 0)

    options = [
        "Sales Reports",
        "Purchase Reports",
        "Client Payment Reports",
        "Client Ledger",
        "Revenue Reports",
        "Expense Analysis",
        "Cash Flow Statement",
        "Profit and Loss Statement"
    ]

    report_type = Combobox(
        window,
        values= options,
        state="readonly",
        font=("VarelaRound Regular", 10)
    )
    report_type.set("Select Report")
    report_type.place(
        x=43.0,
        y=56.0,
        width=190.0,
        height=25.0
    )
    report_type.bind("<<ComboboxSelected>>", enable_fields)


    start_date = DateEntry(
        window,
        bd=0,
        state=DISABLED,
        bg="#FFFFFF",
        fg="#000716",
        highlightthickness=0,
        date_pattern='dd/mm/yyyy',
    )
    start_date.place(
        x=267.0,
        y=56.0,
        width=120.0,
        height=25.0
    )

    end_date = DateEntry(
        window,
        bd=0,
        state=DISABLED,
        bg="#FFFFFF",
        fg="#000716",
        highlightthickness=0,
        date_pattern='dd/mm/yyyy',
    )
    end_date.place(
        x=424.0,
        y=56.0,
        width=120.0,
        height=25.0
    )


    date_options = [
    "All",
    "Today",
    "Last 7 Days",
    "Last 30 Days",
    "This Week",
    "This Month",
    "This Year",
    "Last Week",
    "Last Month",
    "Last Year",
    "Custom Range"
    ]
    quick_date = Combobox(
        window,
        values=date_options,
        state="readonly",  # Makes it read-only to prevent arbitrary input
        font=("VarelaRound Regular", 10)  # Styling the font
    )
    quick_date.set("Select")
    quick_date.bind("<<ComboboxSelected>>", update_dates)
    quick_date.place(
        x=578.0,
        y=56.0,
        width=150.0,
        height=25.0
    )

    Client_type = ttk.Combobox(
        window,
        values=["Client", "Supplier"],
        state=DISABLED,
        font=("VarelaRound Regular", 10)
    )
    Client_type.place(
        x=784.0,
        y=56.0,
        width=130.0,
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
        state=DISABLED,
        font=("VarelaRound Regular", 10)
    )
    Client.place(
        x=927.0,
        y=56.0,
        width=170.0,
        height=25.0
    )

    button_image_1 = PhotoImage(
        file=relative_to_assets("button_1.png"))
    button_1 = Button(
        window,
        image=button_image_1,
        borderwidth=0,
        highlightthickness=0,
        command= fetch_and_display_data,
        relief="flat"
    )
    button_1.place(
        x=1148.0,
        y=45.0,
        width=30.0,
        height=30.0
    )

    button_image_2 = PhotoImage(
        file=relative_to_assets("button_2.png"))
    reset_btn = Button(
        window,
        image=button_image_2,
        borderwidth=0,
        highlightthickness=0,
        command=reset_data,
        relief="flat"
    )
    reset_btn.place(
        x=1207.0,
        y=45.0,
        width=30.0,
        height=30.0
    )

    button_image_3 = PhotoImage(
        file=relative_to_assets("button_3.png"))
    button_3 = Button(
        window,
        image=button_image_3,
        borderwidth=0,
        highlightthickness=0,
        command=lambda: new_adjustment_ui(parent=window),
        relief="flat"
    )
    button_3.place(
        x=667.0,
        y=106.0,
        height=30.0
    )

    button_image_4 = PhotoImage(
        file=relative_to_assets("button_4.png"))
    button_4 = Button(
        window,
        image=button_image_4,
        borderwidth=0,
        highlightthickness=0,
        relief="flat"
    )
    button_4.place(
        x=837.0,
        y=106.0,
        width=120.0,
        height=30.0
    )

    button_image_5 = PhotoImage(
        file=relative_to_assets("button_5.png"))
    button_5 = Button(
        window,
        image=button_image_5,
        borderwidth=0,
        highlightthickness=0,
        command= export_as_excel,
        relief="flat"
    )
    button_5.place(
        x=977.0,
        y=106.0,
        width=120.0,
        height=30.0
    )

    button_image_6 = PhotoImage(
        file=relative_to_assets("button_6.png"))
    button_6 = Button(
        window,
        image=button_image_6,
        borderwidth=0,
        highlightthickness=0,
        command=export_as_pdf,
        relief="flat"
    )
    button_6.place(
        x=1117.0,
        y=106.0,
        width=120.0,
        height=30.0
    )

    canvas.create_text(
        784.0,
        37.0,
        anchor="nw",
        text="Client Type",
        fill="#000000",
        font=("VarelaRound Regular", 12 * -1)
    )

    canvas.create_text(
        927.0,
        37.0,
        anchor="nw",
        text="Client Name",
        fill="#000000",
        font=("VarelaRound Regular", 12 * -1)
    )

    canvas.create_text(
        267.0,
        37.0,
        anchor="nw",
        text="Starting Date",
        fill="#000000",
        font=("VarelaRound Regular", 12 * -1)
    )

    canvas.create_text(
        424.0,
        37.0,
        anchor="nw",
        text="Ending Date",
        fill="#000000",
        font=("VarelaRound Regular", 12 * -1)
    )

    canvas.create_text(
        398.0,
        60.0,
        anchor="nw",
        text="To",
        fill="#000000",
        font=("VarelaRound Regular", 13 * -1)
    )

    canvas.create_text(
        578.0,
        37.0,
        anchor="nw",
        text="Quick Date",
        fill="#000000",
        font=("VarelaRound Regular", 12 * -1)
    )

    canvas.create_text(
        43.0,
        37.0,
        anchor="nw",
        text="Report Type",
        fill="#000000",
        font=("VarelaRound Regular", 12 * -1)
    )

    def toggle_submenu(menu, button):
        x = button.winfo_rootx()
        y = button.winfo_rooty() + button.winfo_height()
        menu.post(x, y)


    Payments_dropdown = Menu(window, tearoff=0, bg="white", fg="black", font=("Poppins", 10, "normal"))
    Payments_dropdown.add_command(label="  Add Invoice Payments    ", command=lambda: customer_payment_in(parent=window))
    Payments_dropdown.add_command(label="  Add Purchase Payments   ", command=lambda: supplier_payments_out(parent=window))
    Payments_dropdown.add_command(label="  Add Expance Payments    ", command=lambda: expense_payments_out(parent=window))
    Payments_dropdown.add_command(label="  Add Salery Payments     ", command=lambda: pay_salery_ui(parent=window))
    button_4.config(command=lambda: toggle_submenu(Payments_dropdown, button_4))

    treeview_frame = Frame(window)
    treeview_frame.place(x=25, y=162, width=1230, height=495)

    # Scrollbars
    tree_x_scroll = ttk.Scrollbar(treeview_frame, orient=HORIZONTAL)
    tree_x_scroll.pack(side="bottom", fill="x")

    tree_y_scroll = ttk.Scrollbar(treeview_frame, orient=VERTICAL)
    tree_y_scroll.pack(side="right", fill="y")

    # Treeview
    Treeview = ttk.Treeview(
        treeview_frame,
        xscrollcommand=tree_x_scroll.set,
        yscrollcommand=tree_y_scroll.set,
    )
    Treeview.pack(expand=True, fill="both")

    # Configure scrollbars
    tree_x_scroll.config(command=Treeview.xview)
    tree_y_scroll.config(command=Treeview.yview)

    window.resizable(False, False)
    window.bind("<Escape>", lambda event: Top_Close(window, parent))
    window.protocol("WM_DELETE_WINDOW", lambda: Top_Close(window, parent))
    window.mainloop()


if __name__ == '__main__':
    Reports_ui()
    
