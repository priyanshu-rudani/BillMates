import importlib.util
import sys
from tkinter import messagebox

class DependencyChecker:
    REQUIRED_MODULES = [
        "PIL",
        "tkcalendar",
        "reportlab",
        "qrcode",
        "openpyxl",
        "matplotlib",
        "num2words",
        "configparser",
    ]

    @classmethod
    def check(cls):
        missing_modules = [m for m in cls.REQUIRED_MODULES if importlib.util.find_spec(m) is None]
        if missing_modules:
            messagebox.showerror(
                "Missing Modules",
                f"The following required modules are not installed:\n{', '.join(missing_modules)}"
            )
            sys.exit(1)