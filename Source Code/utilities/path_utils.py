import sys
import os
from pathlib import Path
import tkinter as tk
from tkinter import messagebox
import sqlite3
import configparser
from datetime import datetime, timedelta

  
def generate_path(*path_parts) -> Path:
    """Generates a cross-platform path."""
    
    if getattr(sys, 'frozen', False):  # Running as a PyInstaller EXE
        root_path = Path(sys.executable).parent
    else:  # Running as a Python script
        root_path = Path(__file__).parent.parent

    full_path = root_path.joinpath(*path_parts)  # Join root path with provided parts
    return full_path


def database_path(*path_parts) -> Path:
    current_dir = os.path.splitdrive(os.getcwd())[0]
    if current_dir == "C:":
        # If the directory is C, use generate_path() method
        appdata_path = os.path.join(os.getenv('APPDATA'), 'BillMates')
        full_path = os.path.join(appdata_path, *path_parts)
        return full_path
    else:
        # If it's not C, use appdata_path as a fallback
        return generate_path("db", *path_parts)


def center_window(window, width, height):
    # Update window to reflect current size (including title bar, borders, and other decorations)
    window.update_idletasks()

    # Get screen dimensions
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()

    # Calculate the position to center the window on the screen
    x = (screen_width // 2) - (width // 2)
    y = (screen_height // 2) - (height // 2) - 15

    # Apply geometry with correct size and position
    window.geometry(f"{width}x{height}+{x}+{y}")
    window.minsize(width, height)


def fetch_data(query, params=None, db="clients.db"):
    try:
        if not query:
            return
        
        connection = sqlite3.connect(database_path(db))
        cursor = connection.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        data = cursor.fetchall()
        connection.close()
        return data
    except sqlite3.OperationalError as op_err:
        messagebox.showerror("Operational Error", f"An operational error occurred: {op_err}")
    except sqlite3.IntegrityError as int_err:
        messagebox.showerror("Integrity Error", f"An integrity error occurred: {int_err}")
    except sqlite3.DatabaseError as db_err:
        messagebox.showerror("Database Error", f"An database error occurred: {db_err}")
    except Exception as e:
        connection.rollback()
        messagebox.showerror("Error", f"An unexpected error occurred: {e}")

def run_query(query, params=None, db="clients.db"):
    try:
        connection = sqlite3.connect(database_path(db))
        cursor = connection.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        
        connection.commit()
        connection.close()
        return
    except sqlite3.OperationalError as op_err:
        messagebox.showerror("Operational Error", f"An operational error occurred: {op_err}")
    except sqlite3.IntegrityError as int_err:
        messagebox.showerror("Integrity Error", f"An integrity error occurred: {int_err}")
    except sqlite3.DatabaseError as db_err:
        messagebox.showerror("Database Error", f"An database error occurred: {db_err}")
    except Exception as e:
        connection.rollback()
        messagebox.showerror("Error", f"An unexpected error occurred: {e}")



def get_client_id(customer_name):
    result = fetch_data('''SELECT id FROM Clients WHERE name = ?''', (customer_name,))
    return result[0][0] if result else 0

def get_client_name(customer_id):
    result = fetch_data('''SELECT name FROM Clients WHERE id = ?''', (customer_id,))
    return result[0][0] if result else 0

def get_client_type(client_name):
    result = fetch_data("SELECT client_type FROM Clients WHERE name = ?", (client_name,))
    return result[0][0] if result else 0

def fetch_client_names(type): 
    client_names = fetch_data("SELECT name FROM Clients WHERE client_type = ?", (type,))
    return [name[0] for name in client_names]

def fetch_client_id(type): 
    client_names = fetch_data("SELECT id FROM Clients WHERE client_type = ?", (type,))
    return [name[0] for name in client_names]



class SearchBox:
    def __init__(self, entry, listbox, data):        
        self.data = data  # Sample data (case-sensitive)

        self.entry = entry
        self.entry.bind("<KeyRelease>", self.on_key_release)
        self.entry.bind("<FocusOut>", self.on_focus_out)

        self.listbox = listbox
        self.listbox.place_forget()  # Initially hidden

        self.listbox.bind("<FocusOut>", self.on_focus_out)
        self.listbox.bind("<ButtonRelease-1>", self.on_select)

    def on_key_release(self, event):
        search_term = self.entry.get().strip()
        
        if not search_term:
            self.listbox.place_forget()
            return

        # Case-sensitive filtering
        filtered_data = [item for item in self.data if search_term.lower() in str(item).lower()]

        if filtered_data:
            self.listbox.delete(0, tk.END)
            for item in filtered_data:
                self.listbox.insert(tk.END, item)
            
            # Adjust listbox height dynamically (max 5 lines)
            listbox_height = min(len(filtered_data), 5)
            self.listbox.configure(height=listbox_height)

            # Show listbox below entry
            listbox_x = self.entry.winfo_x()
            listbox_y = self.entry.winfo_y() + self.entry.winfo_height() + 1
            self.listbox.place(x=listbox_x, y=listbox_y, width=self.entry.winfo_width())
            self.listbox.lift()
        else:
            self.listbox.place_forget()

    def on_select(self, event):
        try:
            selected_index = event.widget.curselection()
            if selected_index:
                selected_item = event.widget.get(selected_index[0])
                self.entry.delete(0, tk.END)
                self.entry.insert(0, selected_item)
        except IndexError:
            pass
        self.listbox.place_forget()

    def on_focus_out(self, event=None):
        self.listbox.place_forget()



def Top_Close(root, parent):
    """
    A robust function to close a Toplevel window, correctly handle modal grabs for nested windows,
    and reload data on the main application dashboard.

    Args:
        root (tk.Toplevel): The Toplevel window that needs to be closed.
        parent (tk.Widget): The immediate parent widget that opened the 'root' window.
                            This is used to correctly return the modal 'grab'.
    """
    # Find the absolute root window of the entire application (the main Tk() instance).
    # This allows us to reliably find the main dashboard, even from a nested dialog.
    app_root = root.winfo_toplevel()
    while app_root.master:
        app_root = app_root.master.winfo_toplevel()

    # Release the event grab from the window being closed.
    root.grab_release()

    # If the immediate parent window still exists, give the event grab back to it.
    # This is crucial for correctly handling nested modal dialogs.

    try:
        if parent.winfo_exists():
            parent.grab_set()
    except:
        messagebox.showwarning("Error", f"No parent Window Found.", parent=app_root)

    # Destroy the Toplevel window.
    root.destroy()
    
    # Now, attempt to reload data on the main application window (app_root).
    # This is wrapped in a try-except block to prevent crashes if the main
    # application frame or its methods don't exist for some reason.
    try:
        # We assume the main application's data frame is an attribute of the root
        # Tk() instance, named 'mainframe'.
        if hasattr(app_root, 'mainframe'):
            app_root.mainframe.Card_data()
            app_root.mainframe.reload_Charts()
        else:
            pass
    except Exception as e:
        # Show a clear error message, parented to the main application window for correct stacking.
        messagebox.showwarning("Data Re-load Error", f"Unable to Reload Dashboard Data.\nError: {e}", parent=app_root)

        


def read_ini(section, key, file_path=None):
    """Reads a value from an .ini file. If missing, creates the section/key with None."""

    DEFAULT_PATH = database_path("config.ini")

    file_path = file_path or DEFAULT_PATH
    config = configparser.ConfigParser()
    
    if not os.path.exists(file_path):
        with open(file_path, 'w') as f:
            f.write("")  # Create an empty file if it does not exist
    
    config.read(file_path)
    
    if not config.has_section(section):
        config.add_section(section)
    
    if not config.has_option(section, key):
        config.set(section, key, "")  # Default missing key to empty
    
    with open(file_path, 'w') as configfile:
        config.write(configfile)  # Save the updated config
    
    return config.get(section, key)

def write_ini(section, key, value="", file_path=None):
    """Writes a value to an .ini file, creating the file if it does not exist."""
    
    DEFAULT_PATH = database_path("config.ini")

    file_path = file_path or DEFAULT_PATH
    config = configparser.ConfigParser()
    
    if os.path.exists(file_path):
        config.read(file_path)
    
    if not config.has_section(section):
        config.add_section(section)
    
    config.set(section, key, str(value))  # Store the value as string
    
    with open(file_path, 'w') as configfile:
        config.write(configfile)


def get_dates_between(start_date, end_date):
    try:
        start = datetime.strptime(start_date, "%d/%m/%Y")
        end = datetime.strptime(end_date, "%d/%m/%Y")
        if start > end:
            raise ValueError("Start date must be before or equal to the end date.")
        
        difference = (end - start).days

        if difference > 730:
            messagebox.showerror("Invalid Date Range", "Date range cannot exceed 730 days (2 Years)!")
            return

        date_list = []
        current_date = start
        while current_date <= end:
            date_list.append(current_date.strftime("%d/%m/%Y"))
            current_date += timedelta(days=1)
        return date_list
    except ValueError as ve:
        messagebox.showerror("Input Error", str(ve))
        return []
    except Exception as e:
        messagebox.showerror("Unexpected Error", f"An unexpected error occurred: {e}")
        return []