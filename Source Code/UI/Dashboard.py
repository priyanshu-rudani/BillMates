import sys
from pathlib import Path
if getattr(sys, 'frozen', False):  # Running as a PyInstaller EXE
    root_path = Path(sys.executable).parent
else:  # Running as a Python script
    root_path = Path(__file__).parent.parent
sys.path.append(str(root_path))


from utilities.path_utils import *
import tkinter as tk
from tkinter import Frame, Tk, Button, Menu
from tkinter import ttk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from datetime import datetime, timedelta, date
from PIL import Image, ImageTk
from utilities.GenerateReport import export_report

from UI.gui import *


class HeaderFrame(Frame):
    def __init__(self, master, **options):
        super().__init__(master, **options)

        heading = tk.Label(self, text="Dashboard", fg="#151D48", bg=self.cget("bg"), font=("Poppins SemiBold", 20 * -1))
        heading.pack(side="left", pady=(5, 0), padx=(30, 0))

        UserName = tk.Label(self, text=read_ini("PROFILE", "name"), fg="#151D48", bg=self.cget("bg"), font=("Poppins SemiBold", 18 * -1))
        UserName.pack(side="right", pady=(5, 0), padx=(0, 30))

class Sidebar(Frame):
    def __init__(self, master, menu_data, frame_width, button_height=20, button_spacing=0, icon_size=(16, 16), inner_padx=(10, 10), inner_pady=(0, 0), bg ="#4F59C1", **options):
        super().__init__(master, width=frame_width, bg=bg,**options)

        self.parent_root = master # Keep a reference to the top-level window for commands
        self.menu_data = menu_data
        self.frame_width = frame_width
        self.button_height = button_height
        self.button_spacing = button_spacing
        self.icon_size = icon_size
        self.bg = bg
        self._button_icons = [] # List to hold PhotoImage references to prevent garbage collection

        self.pack_propagate(False)

        self._inner_content_frame = Frame(self, bg=self["bg"]) # Use the same background as the sidebar
        self._inner_content_frame.pack(
            fill="both",
            expand=True,
            padx=inner_padx, # Apply horizontal inner padding here
            pady=inner_pady  # Apply vertical inner padding (tuple allowed here)
        )
        # Prevent the inner frame from shrinking, so it fills the padded space
        self._inner_content_frame.pack_propagate(False)

        self._build_menu_items()


    def _toggle_submenu(self, menu, button):
        """
        Calculates the position relative to the button and posts the submenu.
        """
        # Get the absolute x and y coordinates of the button's top-left corner
        # Then add the button's width to get the x-coordinate for the right side
        x = button.winfo_rootx() + button.winfo_width()
        y = button.winfo_rooty() # Use the button's absolute y-coordinate
        menu.post(x, y)

    def _load_icon(self, icon_path):
        """Loads and resizes an image file for a button, returning a PhotoImage object."""
        try:
            img = Image.open(icon_path) # Open image using PIL
            img = img.resize(self.icon_size, Image.Resampling.LANCZOS) # Resize image with high quality
            photo_img = ImageTk.PhotoImage(img) # Convert to PhotoImage for Tkinter
            return photo_img
        except FileNotFoundError:
            messagebox.showerror("Icon not found", f"Icon file not found at '{icon_path}'.", parent=self)
            return None
        except Exception as e:
            messagebox.showerror("Error loading icon", f"Error loading icon '{icon_path}'.", parent=self)
            return None

    def _build_menu_items(self):
        top_buttons_data = []
        bottom_buttons_data = []

        for item_data in self.menu_data:
            if item_data.get("pack_side") == "bottom":
                bottom_buttons_data.append(item_data)
            else:
                top_buttons_data.append(item_data)

        # Process and pack 'top' buttons. They will stack from the top down.
        for item_data in top_buttons_data:
            self._create_and_pack_button(item_data, tk.TOP)

        # Process and pack 'bottom' buttons.
        # Iterating in reverse ensures the *last* item in your menu_data with "pack_side": "bottom"
        # will appear at the very bottom of the sidebar.
        for item_data in reversed(bottom_buttons_data):
            self._create_and_pack_button(item_data, tk.BOTTOM)

    def _create_and_pack_button(self, item_data, side):
        """
        Helper method to create a button, handle its command(s), and pack it.
        This centralizes button creation logic.
        """
        button_text = item_data.get("text")
        icon_path = item_data.get("icon")
        commands = item_data.get("commands", []) # List of dropdown commands for submenus
        single_command = item_data.get("single_command") # Single command for a direct action button

        button_options = {
            "text": button_text,
            "bg": self.bg,
            "fg": "White",
            "highlightthickness": 0,
            "activebackground": "#343D9D",
            "activeforeground": "White",
            "borderwidth": 0,
            "relief": "flat",
            "cursor": "hand2",
            "compound": "left",
            "anchor": "w", 
            "font": ("Poppins SemiBold", 11)
        }

        photo_image = None
        if icon_path:
            photo_image = self._load_icon(icon_path)
            if photo_image:
                button_options["image"] = photo_image
                button_options["padx"] = 10 # Adjust padding to give space from the left edge
                self._button_icons.append(photo_image) # Keep reference to prevent garbage collection

        # Create the main button, parented to 'self' (the Sidebar Frame)
        button = Button(self._inner_content_frame, **button_options)

        if commands: # If 'commands' list is provided and not empty, create a submenu
            dropdown_menu = Menu(
                self,
                tearoff=0, 
                bg="white",
                fg="black",
                font=("Poppins", 10, "normal")
            )

            for cmd_data in commands:
                if cmd_data.get("type") == "separator":
                    dropdown_menu.add_separator() # Adds a horizontal separator line to the menu
                else:
                    label = cmd_data.get("label")
                    command = cmd_data.get("command")
                    if label and command:
                        dropdown_menu.add_command(label=f"  {label}  ", command=command)

            button.config(command=lambda m=dropdown_menu, b=button: self._toggle_submenu(m, b))

        elif single_command: # If 'single_command' is provided, assign it directly as the button's action
            button.config(command=single_command)
        else:
            pass

        button.pack(
            fill="x",  # Make the button expand horizontally to fill the sidebar width
            ipadx=10,    # No horizontal padding, as button width is set by frame_width
            pady=self.button_spacing, # Vertical spacing between buttons
            side=side, # Pack from tk.TOP (default) or tk.BOTTOM as determined by menu_data
            anchor="n" if side == tk.TOP else "s" # Anchor content to north for top-packed, south for bottom-packed,
        )

class MainFrame(Frame):
    def __init__(self, master, **options):
        super().__init__(master, **options)

        self.grid_propagate(False)

        for i in range(5):
            self.grid_rowconfigure(i, weight=1, uniform="row_group")

        for i in range(5):
            self.grid_columnconfigure(i, weight=1, uniform="col_group")

        # First Row
        self.financial_year_card = DynamicCard(self, "Financial Year", "")
        self.financial_year_card.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

        self.total_sales_card = DynamicCard(self, "Total Sales Revenue", 0)
        self.total_sales_card.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")

        self.total_cogs_card = DynamicCard(self, "Total COGS Amount", 0)
        self.total_cogs_card.grid(row=0, column=2, padx=5, pady=5, sticky="nsew")

        self.total_purchase_card = DynamicCard(self, "Total Purchases", 0)
        self.total_purchase_card.grid(row=0, column=3, padx=5, pady=5, sticky="nsew")

        self.total_expanse_card = DynamicCard(self, "Total Expenditure", 0)
        self.total_expanse_card.grid(row=0, column=4, padx=5, pady=5, sticky="nsew")

        # Secound Row
        self.collected_revenue_card = DynamicCard(self, "Collected Revenue", 0)
        self.collected_revenue_card.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")

        self.amount_receivable_card = DynamicCard(self, "Amount Receivable", 0)
        self.amount_receivable_card.grid(row=1, column=1, padx=5, pady=5, sticky="nsew")

        self.settled_purchase_card = DynamicCard(self, "Settled Purchase", 0)
        self.settled_purchase_card.grid(row=1, column=2, padx=5, pady=5, sticky="nsew")

        self.amount_payable_card = DynamicCard(self, "Amount Payable", 0)
        self.amount_payable_card.grid(row=1, column=3, padx=5, pady=5, sticky="nsew")

        self.net_profit_Loss_card = DynamicCard(self, "Net Profit/Loss", 0)
        self.net_profit_Loss_card.grid(row=1, column=4, padx=5, pady=5, sticky="nsew")

        # Charts
        self.line_chart = LineChartFrame(self)
        self.line_chart.grid(row=2, column=0, rowspan=3, columnspan=3, padx=5, pady=20, sticky="nsew")

        self.pie_chart = PieChartFrame(self)
        self.pie_chart.grid(row=2, column=3, rowspan=3, columnspan=2, padx=5, pady=20, sticky="nsew")

        self.Card_data()

    def Card_data(self):
        today = date.today()
        current_year = today.year
        current_month = today.month

        if current_month >= 4:  # If current month is April or later
            start_date = date(current_year, 4, 1).strftime("%d/%m/%Y")
            end_date_year = current_year + 1
        else:  # If current month is before April (Jan, Feb, Mar)
            start_date = date(current_year - 1, 4, 1).strftime("%d/%m/%Y")
            end_date_year = current_year
        
        end_date = date(end_date_year, 3, 31).strftime("%d/%m/%Y")
        dates = get_dates_between(start_date, end_date)

        placeholders = ', '.join(['?'] * len(dates))

        financial_year = f"{end_date_year-1}-{end_date_year}"
        total_sales = fetch_data(f"SELECT COALESCE(SUM(total), 0) FROM Invoices WHERE date IN ({placeholders})", dates)[0][0]
        total_purchase = fetch_data(f"SELECT COALESCE(SUM(total), 0) FROM Purchase WHERE date IN ({placeholders})", dates)[0][0]
        total_expanse = fetch_data(f"SELECT COALESCE(SUM(total_amount), 0) FROM Payments WHERE Expanse_type IN ('Rent', 'Utilities', 'Maintenance', 'Marketing', 'Loan Interest', 'Taxes', 'Other Expances') AND entity_type = 'Expense' AND date IN ({placeholders})", dates)[0][0]
        total_cogs = fetch_data(f"SELECT COALESCE(SUM(total_amount), 0) FROM Payments WHERE Expanse_type IN ('Payment For Purchase', 'Salary', 'Transposition') AND entity_type IN ('Expense', 'Salaries') AND date IN ({placeholders})", dates)[0][0]
        collected_revenue = fetch_data(f"SELECT COALESCE(SUM(total_amount), 0) FROM Payments WHERE Expanse_type = 'Invoice Payment' AND entity_type = 'Income' AND date IN ({placeholders})", dates)[0][0]
        settled_purchase = fetch_data(f"SELECT COALESCE(SUM(total_amount), 0) FROM Payments WHERE Expanse_type = 'Payment For Purchase' AND entity_type = 'Expense' AND date IN ({placeholders})", dates)[0][0]
        amount_receivable = fetch_data(f"SELECT COALESCE(SUM(remaining), 0) FROM Invoices WHERE date IN ({placeholders})", dates)[0][0]
        amount_payable = fetch_data(f"SELECT COALESCE(SUM(remaining), 0) FROM Purchase WHERE date IN ({placeholders})", dates)[0][0]
        net_profit_Loss = total_sales - total_purchase - total_expanse
        
        self.financial_year_card._update_value(financial_year)
        self.total_sales_card._update_value(total_sales)
        self.total_purchase_card._update_value(-total_purchase)
        self.total_expanse_card._update_value(-total_expanse)
        self.total_cogs_card._update_value(-total_cogs)
        self.collected_revenue_card._update_value(collected_revenue)
        self.settled_purchase_card._update_value(-settled_purchase)
        self.amount_receivable_card._update_value(amount_receivable)
        self.amount_payable_card._update_value(-amount_payable)
        self.net_profit_Loss_card._update_value(net_profit_Loss)
    
    def reload_Charts(self):
        self.line_chart._update_chart()
        self.pie_chart._update_chart()

class DynamicCard(Frame):
    def __init__(self, parent, card_heading, initial_value=None, *args, **kwargs):
        super().__init__(parent, relief="solid", borderwidth=0, bg="White",
                         highlightbackground="#e0e0e0", highlightthickness=1,
                         width=220, height=150, *args, **kwargs)

        self.grid_propagate(False)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=2)
        self.columnconfigure(0, weight=2)
        self.columnconfigure(1, weight=0)

        self.heading_label = tk.Label(self, text=f"{card_heading}", fg="#737791", bg="#ffffff", font=("Poppins SemiBold", 15 * -1))
        self.heading_label.grid(row=0, column=0, sticky="sw", padx=(15, 0), pady=(10, 0))

        self.value_label = tk.Label(self, text=f"{initial_value}", fg="#151D48", bg="#ffffff", font=("Poppins SemiBold", 18 * -1))
        self.value_label.grid(row=1, column=0, sticky="nw", padx=(15, 0), pady=(0, 10))

        self.bar_frame = Frame(self, relief="solid", borderwidth=0, bg="#4F59C1", width=4)
        self.bar_frame.grid(row=0, column=1, rowspan=2, sticky="nse", padx=(5, 10), pady=10)

        self._update_value(initial_value)

    def _format_value(self, value):
        try:
            numeric_value = float(value)
            if numeric_value == int(numeric_value):
                return f"{int(numeric_value):,}"
            else:
                return f"{numeric_value:,.1f}"
        except ValueError:
            return str(value)

    def _apply_value_color(self, value):
        try:
            numeric_value = float(value)
            if numeric_value < 0:
                self.value_label.config(fg="#DC2626")
            else:
                self.value_label.config(fg="#00892A")
        except ValueError:
            self.value_label.config(fg="#151D48")


    def _update_value(self, new_value):
        formatted_value = self._format_value(new_value)
        self.value_label.config(text=formatted_value)
        self._apply_value_color(new_value)

class LineChartFrame(Frame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, relief="solid", borderwidth=0, bg="White",
                         highlightbackground="#ffffff", highlightthickness=0,
                         *args, **kwargs)
        
        # --- FIX 1: Prevent this frame from propagating its size based on children ---
        self.grid_propagate(False) 

        # Configure internal grid to ensure canvas expands within this frame
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.dates, self.revenue, self.expenses = self._generate_data()

        # Initialize Matplotlib Figure and Axis as instance variables
        self.fig = None
        self.ax = None
        self.chart_canvas = None

        self._create_chart()

    def _update_chart(self):
        # Re-fetch the latest data
        self.dates, self.revenue, self.expenses = self._generate_data()
        self.fig = None
        self.ax = None
        self.chart_canvas = None

        # Re-create the chart with the new data
        self._create_chart()
        
    def _create_chart(self):

        if self.chart_canvas:
            self.chart_canvas.get_tk_widget().destroy()
            self.fig.clear() # Clear the figure to redraw content

        # Create a Figure for the plot with a light gray background
        self.fig = Figure()
        self.ax = self.fig.add_subplot(111)

        # Plot the revenue and expenses lines
        self.ax.plot(self.dates, self.revenue, marker='o', linestyle='-', color='#007acc', label='Revenue')
        self.ax.plot(self.dates, self.expenses, marker='s', linestyle='--', color='#ff4500', label='Expenses')

        # --- Customize the plot appearance ---
        self.ax.set_ylabel('Amount (in Rs.)', fontsize=10)
        self.ax.set_xlabel('Last 7 Days', fontsize=10)

        self.ax.set_ylim(bottom=0)

        # Add a grid for better readabilit
        self.ax.grid(True, which='both', linestyle='--', linewidth=0.5)
        self.ax.legend(fontsize=10)
        self.fig.tight_layout(pad=2.0)

        # --- Embed the plot in Tkinter ---
        self.chart_canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.chart_canvas.draw()
        self.chart_canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew", padx=10, pady=10)


    def _generate_data(self):
        start_date = (datetime.now() - timedelta(days=6)).strftime('%d/%m/%Y')
        end_date = (datetime.now() - timedelta(days=0)).strftime('%d/%m/%Y')

        dates = get_dates_between(start_date, end_date)

        placeholders = ', '.join(['?'] * len(dates))
        case_statement = " ".join(
            [f"WHEN '{date}' THEN {index}" for index, date in enumerate(dates, start=1)]
        )

        last_7_days = [(datetime.now() - timedelta(days=i)).strftime('%d') for i in range(6, 1, -1)]
        last_7_days.extend(["Yesterday", "Today"])

        revenue_q = f"""
        SELECT date, COALESCE(CAST(SUM(total_amount) AS INTEGER), 0) AS total_expense FROM Payments
        WHERE (entity_type = 'Income' OR Expanse_type = 'Adjustment Credit') AND date IN ({placeholders}) 
        GROUP BY 
            date
        ORDER BY CASE date {case_statement} ELSE 999 END;
        """

        expenses_q = f"""
        SELECT date, COALESCE(CAST(SUM(total_amount) AS INTEGER), 0) AS total_expense FROM Payments
        WHERE (entity_type IN ('Expense', 'Salaries') OR Expanse_type = 'Adjustment Debit') AND date IN ({placeholders})
        GROUP BY 
            date
        ORDER BY 
            CASE 
                date
                {case_statement}
                ELSE 999
            END;
        """

        data1 = dict(fetch_data(revenue_q, dates))
        data2 = dict(fetch_data(expenses_q, dates))

        revenue = [data1.get(day, 0) for day in dates]
        expenses = [data2.get(day, 0) for day in dates]

        return last_7_days, revenue, expenses

class PieChartFrame(Frame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, relief="solid", borderwidth=0, bg="White",
                         highlightbackground="#ffffff", highlightthickness=0,
                         *args, **kwargs)
        
        # --- FIX 1: Prevent this frame from propagating its size based on children ---
        self.grid_propagate(False)

        # Configure internal grid to ensure canvas expands within this frame
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.labels, self.value = self._generate_data()

        # Initialize Matplotlib Figure and Axis as instance variables
        self.figure = None
        self.axis = None
        self.canvas = None # Renamed from self.piecanvas for consistency

        self._create_Pie_chart()

        # --- FIX 2: Bind to <Configure> event for dynamic resizing ---
        self.bind("<Configure>", self._on_frame_resize)

    def _update_chart(self):
        # Re-fetch the latest data
        self.labels, self.value = self._generate_data()
        self.figure = None
        self.axis = None
        self.canvas = None

        # Re-create the chart with the new data
        self._create_Pie_chart()

    def _create_Pie_chart(self):

        if self.canvas:
            self.canvas.get_tk_widget().destroy()
            self.figure.clear() # Clear the figure to redraw content

        # Create a Figure for the plot. Initial figsize is a placeholder.
        self.figure = Figure(facecolor="#ffffff")
        self.axis = self.figure.add_subplot(111)

        # --- Check if there is data to plot ---
        if not self.value or sum(self.value) == 0:
            # If there are no expenses, display a message in the center.
            self.axis.text(0.5, 0.5, 'No Expenses', 
                    horizontalalignment='center', 
                    verticalalignment='center', 
                    fontsize=16, 
                    color='gray',
                    transform=self.axis.transAxes) # Use transform=ax.transAxes for relative coordinates
            
            # Hide the axis lines and ticks for a clean, empty look
            self.axis.set_xticks([])
            self.axis.set_yticks([])
            for spine in self.axis.spines.values():
                spine.set_visible(False)
        else:
            # If data exists, create the pie chart as before
            wedges, texts, autotexts = self.axis.pie(
                self.value, 
                autopct='%1.1f%%', # Add percentage labels
                startangle=90,
                textprops=dict(color="w") # Set percentage text color to white
            )
            
            self.axis.legend(wedges, self.labels,
                      title="Expense Types",
                      loc="best",
                      fontsize='small')

            plt.setp(autotexts, size=10, weight="bold")
            self.axis.axis('equal')

        self.figure.tight_layout(pad=1.0)

        self.canvas = FigureCanvasTkAgg(self.figure, master=self)
        self.canvas.draw()
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew", padx=10, pady=10)


    def _on_frame_resize(self, event):
        """
        Callback function for the <Configure> event.
        Resizes the Matplotlib figure to match the new size of the PieChartFrame.
        """
        new_width_pixels = event.width
        new_height_pixels = event.height

        # Convert pixels to inches, accounting for internal padding
        width_inches = (new_width_pixels - 10) / self.figure.dpi
        height_inches = (new_height_pixels - 20) / self.figure.dpi

        if width_inches > 0 and height_inches > 0:
            self.figure.set_size_inches(width_inches, height_inches, forward=True)
            self.canvas.draw_idle()

    def _generate_data(self):
        query = """
            SELECT Expanse_type, COALESCE(SUM(total_amount), 0.0) AS total_expense
            FROM Payments
            WHERE Expanse_type IN ('Rent', 'Utilities', 'Maintenance', 'Marketing', 'Loan Interest', 'Taxes', 'Other Expances') 
            AND entity_type = 'Expense'
            GROUP BY Expanse_type
        """
        data = fetch_data(query)
        
        if not data:
            labels, values = ['No Expense'], [0]
        else:
            labels, values = zip(*data)  # Extract labels and values

        # Remove zero-expense categories
        labels = [label for i, label in enumerate(labels) if values[i] > 0]
        values = [value for value in values if value > 0]

        return labels, values

class popupMassage:
    def __init__(self, parent, title, message, button_texts=None):
        self.result = None # Stores the text of the button clicked
        self.window = tk.Toplevel(parent)
        self.window.title(title)
        self.iconbitmap(generate_path("UI", "assets", "BillMates.ico"))
        self.window.transient(parent) # Make the message box appear on top of the parent
        self.window.grab_set()       # Make the message box modal (block parent interaction)

        # Center the message box over the parent window
        self._center_window(parent)

        # Handle window close protocol (e.g., 'X' button)
        self.window.protocol("WM_DELETE_WINDOW", self._on_close)

        # --- Message Label ---
        # Using ttk.Label for better styling
        message_label = ttk.Label(self.window, text=message, wraplength=300, justify="center",
                                  font=('Arial', 10))
        message_label.pack(padx=20, pady=20)

        # --- Buttons Frame ---
        buttons_frame = ttk.Frame(self.window)
        buttons_frame.pack(pady=10)

        if button_texts is None:
            button_texts = ['OK'] # Default button

        # Create buttons dynamically
        for text in button_texts:
            # Using ttk.Button for better styling
            button = ttk.Button(buttons_frame, text=text,
                                command=lambda t=text: self._button_click(t))
            button.pack(side=tk.LEFT, padx=5)

        # Wait until the window is closed before returning control to the caller
        self.window.wait_window(self.window)

    def _button_click(self, button_text):
        self.result = button_text
        self.window.destroy()

    def _on_close(self):
        self.result = None # Indicate that no button was clicked
        self.window.destroy()

    def get_result(self):
        return self.result
        

def export_year_report(report_type):
    try:
        if report_type not in ["Revenue Reports", "Expense Analysis", "Cash Flow Statement", "Profit and Loss Statement"]:
            return  

        start_date = date.today().replace(month=1, day=1).strftime("%d/%m/%Y")
        end_date = date.today().replace(month=12, day=31).strftime("%d/%m/%Y")  
    
        export_report(report_type, start_date, end_date)

    except Exception as e:
        messagebox.showerror("Unexpected Error", f"Unexpected error: {e}")

def on_closing(root):
        """Stop the after function, check backup, and close the window"""

        root.config(cursor="watch")  # Show waiting cursor before quitting
        root.update_idletasks()

        last_backup_str = read_ini("BACKUP", "lastbackup")

        if last_backup_str:
            try:
                last_backup_datetime = datetime.strptime(last_backup_str, "%d/%m/%Y : %H:%M:%S")
                today = datetime.now()
                if (today - last_backup_datetime) > timedelta(days=30):
                    if messagebox.askyesno(parent=root, title="Backup Reminder", message="It has been more than 30 days since the last backup. Do you want to open the backup options?", icon=messagebox.WARNING):
                        root.config(cursor="")
                        Backup_ui(parent=root)  # Open the backup UI
                        return
                    
            except ValueError:
                # Handle case where lastbackup date is not in the correct format
                if messagebox.askyesno(parent=root, title="Backup Information Invalid", message="The last backup information is not in the correct format. Do you want to open the backup options?", icon=messagebox.WARNING):
                    root.config(cursor="")
                    Backup_ui(parent=root)
                    return
        else:
            # Handle case where lastbackup key doesn't exist
            if messagebox.askyesno(parent=root, title="No Backup Found", message="No previous backup information found. Do you want to open the backup options?", icon=messagebox.WARNING):
                root.config(cursor="")
                Backup_ui(parent=root)
                return

        root.quit()
        sys.exit()

class App(Tk):
    def __init__(self):
        super().__init__()

        self.geometry("1280x720")
        self.minsize(1280, 720)
        self.attributes('-fullscreen', True)
        Compney_name = str(read_ini("PROFILE", "name"))
        self.title(f"Dashboard - {Compney_name} (Admin) - BillMates")
        self.iconbitmap(generate_path("UI", "assets", "BillMates.ico"))
        self.configure(bg="#E7EBFF")

        menu_data = [
        {
            "text": "Invoice",
            "icon": self.relative_to_assets("invoice.png"),
            "commands": [
                {"label": "Add Invoice (F1)", "command": lambda: new_invoice_ui(parent=self)},
                {"label": "Add Purchase (F2)", "command": lambda: new_purchase_ui(parent=self)},
                {"label": "Manage Invoices (F8)", "command": lambda: manage_invoice_ui(parent=self)}
            ]
        },
        {
            "text": "Clients",
            "icon": self.relative_to_assets("user.png"),
            "commands": [
                {"label": "Add Clients (F3)", "command": lambda: new_client_ui(parent=self)},
                {"label": "Manage Clients (F9)", "command": lambda: manage_clients(parent=self)}
            ]
        },
        {
            "text": "Payments",
            "icon": self.relative_to_assets("payment.png"),
            "commands": [
                {"label": "Add Invoice Payments (F4)", "command": lambda: customer_payment_in(parent=self)},
                {"label": "Add Adjustment", "command": lambda: new_adjustment_ui(parent=self)},
                {"label": "Payment Getway", "command": lambda: payment_getway(parent=self)},
                {"label": "Manage Payments (F7)", "command": lambda: manage_payments(parent=self)}
            ]
        },
        {
            "text": "Expance",
            "icon": self.relative_to_assets("expanse.png"),
            "commands": [
                {"label": "Add Purchase Payments (F5)", "command": lambda: supplier_payments_out(parent=self)},
                {"label": "Add Expance Payments (F6)", "command": lambda: expense_payments_out(parent=self)},
                {"label": "Add Salery Payments", "command": lambda: pay_salery_ui(parent=self)},
                {"label": "Manage Payments (F7)", "command": lambda: manage_payments(parent=self)}
            ]
        },
        {
            "text": "Reports",
            "icon": self.relative_to_assets("report.png"),
            "commands": [
                {"label": "Manage Reports (F10)", "command": lambda: Reports_ui(parent=self)},
                {"type": "separator"},
                {"label": "Revenue Reports", "command": lambda: export_year_report("Revenue Reports")},
                {"label": "Expense Analysis", "command": lambda: export_year_report("Expense Analysis")},
                {"label": "Cash Flow Statement", "command": lambda: export_year_report("Cash Flow Statement")},
                {"label": "Profit and Loss Statement", "command": lambda: export_year_report("Profit and Loss Statement")}
            ]
        },
        {
            "text": "Cheques",
            "icon": self.relative_to_assets("cheque.png"),
            "commands": [
                {"label": "Add/Print Cheque (F11)", "command": lambda: PrintCheque_ui(parent=self)},
                {"label": "Manage Cheques", "command": lambda: Manage_Cheques_ui(parent=self)},
                {"type": "separator"},
                {"label": "Add Cheque Book", "command": lambda: addChequeBook_ui(parent=self)},
                {"label": "Manage ChequeBooks", "command": lambda: Manage_chequeBook_ui(parent=self)}
            ]
        },
        {
            "text": "Settings",
            "icon": self.relative_to_assets("settings.png"),
            "commands": [
                {"label": "Edit Company", "command": lambda: company_info('edit', parent = self)},
                {"label": "Backup Management", "command": lambda: Backup_ui(parent=self)},
                {"label": "Add Terms & Conditions", "command": lambda: terms_conditions(parent=self)},
                {"label": "Restore Management", "command": lambda: Restore_ui()}
            ]
        },
        {
            "text": "Logout",
            "icon": self.relative_to_assets("logout.png"),
            "pack_side": "bottom", # This button will be packed from the very bottom of the sidebar
            "single_command": lambda: on_closing(self), # Direct command for logout
        }
        ]

        self.header = HeaderFrame(self, bg="#FFFFFF")
        self.header.pack(side="top", fill="x")

        self.sidebar = Sidebar(self, frame_width=200, inner_pady=(10, 25), menu_data=menu_data)
        self.sidebar.pack(side="left", fill="y")

        self.mainframe = MainFrame(self, bg="#E8ECFF")
        self.mainframe.pack(side="top", fill="both", expand=True, pady=(10, 20), padx=(10,10))

        self.bind('<F1>', lambda event: new_invoice_ui(parent = self))
        self.bind('<F2>', lambda event: new_purchase_ui(parent = self))
        self.bind('<F3>', lambda event: new_client_ui(parent = self))
        self.bind('<F4>', lambda event: customer_payment_in(parent = self))
        self.bind('<F5>', lambda event: supplier_payments_out(parent = self))
        self.bind('<F6>', lambda event: expense_payments_out(parent = self))
        self.bind('<F7>', lambda event: manage_payments(parent = self))
        self.bind('<F8>', lambda event: manage_invoice_ui(parent = self))
        self.bind('<F9>', lambda event: manage_clients(parent = self))
        self.bind('<F10>', lambda event: Reports_ui(parent = self))
        self.bind('<F11>', lambda event: PrintCheque_ui(parent=self))
        
        self.bind("<Escape>", lambda event: on_closing(self))
        self.protocol("WM_DELETE_WINDOW", lambda: on_closing(self))


        self.resizable(True, True)
        self.mainloop()

    def relative_to_assets(self, path: str) -> Path:
        ASSETS_PATH = Path(generate_path(root_path, "UI", "assets", "Dashboard"))
        return ASSETS_PATH / Path(path)


if __name__ == "__main__":
    App()