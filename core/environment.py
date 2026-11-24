import sys
from pathlib import Path

if getattr(sys, 'frozen', False):  # Running as a PyInstaller EXE
    root_path = Path(sys.executable).parent
else:  # Running as a Python script
    root_path = Path(__file__).parent.parent
sys.path.append(str(root_path))

import os
from tkinter import messagebox
from utilities.path_utils import generate_path, database_path
from core.db_creater import create_database
from UI.Dashboard import App
from UI.add_company import add_company

class EnvironmentSetup:
    def __init__(self):
        self.db_path = database_path("clients.db")
        self.profile_path = database_path("config.ini")

    def setup(self):
        try:
            self.ensure_directories()
            self.ensure_database()
            self.ensure_profile()
        except Exception as e:
            messagebox.showerror("Setup failed", f"An error occurred: {str(e)}")
            sys.exit(1)

    def ensure_directories(self):
        db_folder = database_path()
        if not os.path.exists(db_folder):
            os.makedirs(db_folder, exist_ok=True)

    def ensure_database(self):
        try:
            if not create_database():
                messagebox.showerror("Error", "Failed to initialize application databases.")
                sys.exit(1)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to initialize database: {e}")
            sys.exit(1)


    def ensure_profile(self):
        if not os.path.exists(self.profile_path):
            try:
                add_company('new')
            except ImportError:
                messagebox.showerror("Error", "Failed to import 'add_company' module. Please reinstall the software.")
                sys.exit(1)

            if not os.path.exists(self.profile_path):
                messagebox.showerror("Error", "Failed to create Company.")
                sys.exit(1)
            else:
                App()
        else:
            App()
