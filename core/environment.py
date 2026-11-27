import sys
import os
from tkinter import messagebox
from utilities.path_utils import get_database_path, _show_error
from core.db_creater import create_database
from UI.Dashboard import App
from UI.add_company import add_company


class EnvironmentSetup:
    def __init__(self):
        self.db_path = get_database_path("clients.db")
        self.profile_path = get_database_path("config.ini")

    def setup(self):
        try:
            self.ensure_directories()
            self.ensure_database()
            self.ensure_profile()
        except Exception as e:
            _show_error("Setup Error", "An error occurred during application startup. Please check the logs or contact support.", exc=e)
            sys.exit(1)

    def ensure_directories(self):
        db_folder = get_database_path()
        if not os.path.exists(db_folder):
            os.makedirs(db_folder, exist_ok=True)

    def ensure_database(self):
        try:
            if not create_database():
                _show_error("Database Error", "Failed to initialize application databases. Please check file permissions or contact support.")
                sys.exit(1)
        except Exception as e:
            _show_error("Database Error", "Failed to initialize application database. Please check file permissions or contact support.", exc=e)
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
