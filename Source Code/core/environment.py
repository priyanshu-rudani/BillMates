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
        self.db_script = self.find_module_path("core/db_creater")

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
            os.makedirs(os.path.dirname(db_folder), exist_ok=True)

    def ensure_database(self):
        if not os.path.exists(self.db_script):
            messagebox.showerror("Error", "Database script not found. Please reinstall the software.")
            sys.exit(1)

        if not os.path.exists(self.db_path):
            try:
                create_database()
            except ImportError:
                messagebox.showerror("Error", "Failed to import 'Database' module. Please reinstall the software.")
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

    def find_module_path(self, relative_path_no_ext):
        """
        Finds a module's full path regardless of its extension (.py, .pyd, .so),
        returning the first match or None if not found.

        Example Usage: find_module_path("core/db_creater")
        """
        if getattr(sys, 'frozen', False):  # Running as a packaged .exe
            root_path = Path(sys.executable).parent
        else:  # Running as a .py script
            # This points to the script's directory, e.g., F:\Project\Billsoft
            root_path = Path(__file__).parent.parent

        # Construct the base for the search, e.g., F:\Project\Billsoft\core\db_creater
        search_base = root_path / relative_path_no_ext

        try:
            # Search for "db_creater.*" and get the first result
            found_path = next(search_base.parent.glob(f"{search_base.name}.*"))
            return found_path
        except StopIteration:
            # The glob search found no matching files
            return None
