import sys
from pathlib import Path

if getattr(sys, 'frozen', False):  # Running as a PyInstaller EXE
    root_path = Path(sys.executable).parent
else:  # Running as a Python script
    root_path = Path(__file__).parent.parent
sys.path.append(str(root_path))

import tkinter as tk
from tkinter import ttk, messagebox
from utilities.path_utils import *
from utilities.text import States
import re

class CompanyForm(ttk.Frame):
    """
    A reusable Tkinter frame for creating or editing company details.
    The form can be opened in 'new' or 'edit' mode.
    """
    def __init__(self, parent, mode='new'):
        """
        Initialize the CompanyForm frame.
        
        Args:
            parent: The parent widget (e.g., a tk.Tk() or tk.Toplevel() window).
            mode (str): The mode to open the form in, either 'new' or 'edit'.
            details (dict, optional): A dictionary of existing company data.
                                      Required if mode is 'edit'. Defaults to None.
        """
        super().__init__(parent, padding="10")
        self.parent = parent
        self.mode = mode

        # --- Data Variables ---
        # We use tkinter's control variables to easily get/set widget values.
        self.business_name = tk.StringVar(value="")
        self.city = tk.StringVar(value="")
        self.state_name = tk.StringVar(value="")
        self.pin_code = tk.StringVar(value="")
        self.country = tk.StringVar(value="India")
        self.email = tk.StringVar(value="")
        self.phone = tk.StringVar(value="")
        self.pan_no = tk.StringVar(value="")
        self.gstin = tk.StringVar(value="")
        self.business_type = tk.StringVar(value="Not Applicable")

        # --- Create and Layout Widgets ---
        self._create_widgets()

        # --- Populate Form Based on Mode ---
        if self.mode == 'edit':
            self.parent.title("Edit Company Details")
            self._populate_form()
        else: # Default to 'new' mode
            self.parent.title("Add New Company")
            self.clear_form() # Ensure form is empty for new entries

    def _create_widgets(self):
        """Creates and lays out all the widgets in the form."""
        # Create the main LabelFrames for organization
        company_details_frame = ttk.LabelFrame(self, text="Company Details", padding=(10, 5))
        company_details_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)

        other_details_frame = ttk.LabelFrame(self, text="Other Details", padding=(10, 5))
        other_details_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=5)

        # Make the main column expandable
        self.columnconfigure(0, weight=1)

        # --- Widgets for Company Details Frame ---
        # Business Name
        ttk.Label(company_details_frame, text="Business Name *").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(company_details_frame, textvariable=self.business_name).grid(row=0, column=1, sticky="ew", padx=5, pady=5)

        # Address
        ttk.Label(company_details_frame, text="Address").grid(row=1, column=0, sticky="nw", padx=5, pady=5)
        address_frame = ttk.Frame(company_details_frame)
        address_frame.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        self.address_text = tk.Text(address_frame, height=4, width=30, wrap="word")
        self.address_text.pack(side="left", fill="both", expand=True)
        address_scrollbar = ttk.Scrollbar(address_frame, orient="vertical", command=self.address_text.yview)
        address_scrollbar.pack(side="right", fill="y")
        self.address_text.config(yscrollcommand=address_scrollbar.set)

        # City
        ttk.Label(company_details_frame, text="City *").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(company_details_frame, textvariable=self.city).grid(row=2, column=1, sticky="ew", padx=5, pady=5)

        ttk.Label(company_details_frame, text="State *").grid(row=3, column=0, sticky="w", padx=5, pady=5)
        state_combo = ttk.Combobox(company_details_frame, textvariable=self.state_name, values=States, state="readonly")
        state_combo.grid(row=3, column=1, sticky="ew", padx=5, pady=5)

        # Pin Code, Country, Email, Phone
        pincode_validation = self.register(lambda value: re.fullmatch(r"[0-9]{0,6}", value) is not None)
        ttk.Label(company_details_frame, text="Pin Code").grid(row=4, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(company_details_frame, textvariable=self.pin_code, validate="key", validatecommand=(pincode_validation, "%P")).grid(row=4, column=1, sticky="ew", padx=5, pady=5)
        ttk.Label(company_details_frame, text="Country").grid(row=5, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(company_details_frame, textvariable=self.country, state="disabled").grid(row=5, column=1, sticky="ew", padx=5, pady=5)
        ttk.Label(company_details_frame, text="Email").grid(row=6, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(company_details_frame, textvariable=self.email).grid(row=6, column=1, sticky="ew", padx=5, pady=5)

        contact_validation = self.register(lambda value: re.fullmatch(r"[0-9]{0,10}", value) is not None)
        ttk.Label(company_details_frame, text="Phone *").grid(row=7, column=0, sticky="w", padx=5, pady=5)
        ttk.Entry(company_details_frame, textvariable=self.phone, validate="key", validatecommand=(contact_validation, "%P")).grid(row=7, column=1, sticky="ew", padx=5, pady=5)
        company_details_frame.columnconfigure(1, weight=1)

        # --- Widgets for Other Details Frame ---
        # PAN No., GSTIN, Business Type
        ttk.Label(other_details_frame, text="PAN No.").grid(row=0, column=0, sticky="w", padx=[5,20], pady=5)
        ttk.Entry(other_details_frame, textvariable=self.pan_no).grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        ttk.Label(other_details_frame, text="GSTIN").grid(row=1, column=0, sticky="w", padx=[5,20], pady=5)
        ttk.Entry(other_details_frame, textvariable=self.gstin).grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        tax_methods = ["Not Applicable", "Private Limited", "Public Limited", "Sole Proprietorship", "Partnership", "LLP."]
        ttk.Label(other_details_frame, text="Business Type").grid(row=2, column=0, sticky="w", padx=[5,20], pady=5)
        tax_combo = ttk.Combobox(other_details_frame, textvariable=self.business_type, values=tax_methods, state="readonly")
        tax_combo.grid(row=2, column=1, sticky="ew", padx=5, pady=5)
        other_details_frame.columnconfigure(1, weight=1)

        # --- Save Button ---
        save_button = ttk.Button(self, text="Save Company", command=self._save_details)
        save_button.grid(row=2, column=0, sticky="ew", padx=5, pady=10, ipady=3)

    def _populate_form(self):
        """Fills the form with existing data for editing."""

        self.business_name.set(read_ini("PROFILE", "name"))
        self.address_text.delete("1.0", "end")
        self.address_text.insert("1.0", read_ini("PROFILE", "address"))
        self.city.set(read_ini("PROFILE", "city"))
        self.state_name.set(read_ini("PROFILE", "state"))
        self.pin_code.set(read_ini("PROFILE", "pin_code"))
        self.email.set(read_ini("PROFILE", "email"))
        self.phone.set(read_ini("PROFILE", "phone"))
        self.pan_no.set(read_ini("PROFILE", "pan_no"))
        self.gstin.set(read_ini("PROFILE", "gstin"))
        self.business_type.set(read_ini("PROFILE", "business_type"))

    def _save_details(self):
        """Handles the save logic based on the form's mode."""
        
        if self._validate_fields() == False:
            return

        try:
            write_ini("PROFILE", "name", self.business_name.get())
            write_ini("PROFILE", "address", self.address_text.get("1.0", "end-1c"))
            write_ini("PROFILE", "city", self.city.get())
            write_ini("PROFILE", "state", self.state_name.get())
            write_ini("PROFILE", "pin_code", self.pin_code.get())
            write_ini("PROFILE", "country", self.country.get())
            write_ini("PROFILE", "email", self.email.get())
            write_ini("PROFILE", "phone", self.phone.get())
            write_ini("PROFILE", "pan_no", self.pan_no.get())
            write_ini("PROFILE", "gstin", self.gstin.get())
            write_ini("PROFILE", "business_type", self.business_type.get())

            write_ini("POLICY", "line1", "Your Terms & Condition write here.....")
            
            messagebox.showinfo("Success", "Congratulations! Your company was created successfully. \nWelcome aboard!", parent=self)
            self.parent.destroy()

        except Exception as e:
            messagebox.showerror("Error", f"We were unable to create your company at this time. We were unable to create your company at this time. \n {e}", parent=self)
            return

    def _validate_fields(self):

        if not self.business_name.get():
            messagebox.showerror("Error", "Oops, the name tag is blank! Please tell us what to call your business.", parent=self)
            return False
        
        if not self.city.get():
            messagebox.showerror("Error", "We're a bit lost without your city.", parent=self)
            return False
        
        if not self.state_name.get():
            messagebox.showerror("Error", "Please select your state from the list.", parent=self)
            return False
        
        if not self.phone.get():
            messagebox.showerror("Error", "Don't be a stranger! We need a phone number to reach you.", parent=self)
            return False
        
        email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
        if not re.fullmatch(email_pattern, self.email.get()) and self.email.get():
            messagebox.showerror("Error", "Almost there! A valid email usually looks like name@example.com", parent=self)
            return False

        gst_pattern = r"[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}"
        if not re.fullmatch(gst_pattern, self.gstin.get()) and self.gstin.get():
            messagebox.showerror("Error", "Hold on, that doesn't look like a valid GSTIN.", parent=self)
            return False
        
        pan_pattern = r"[A-Z]{5}[0-9]{4}[A-Z]{1}"
        if not re.fullmatch(pan_pattern, self.pan_no.get()) and self.pan_no.get():
            messagebox.showerror("Error", "Just a small correction needed! A PAN should have 10 letters.", parent=self)
            return False
        
        return True
        
    def get_details(self):
        """Retrieves all the data from the form fields."""
        return {
            "business_name": self.business_name.get(),
            "address": self.address_text.get("1.0", "end-1c").strip(),
            "city": self.city.get(),
            "state": self.state_name.get(),
            "pin_code": self.pin_code.get(),
            "country": self.country.get(),
            "email": self.email.get(),
            "phone": self.phone.get(),
            "pan_no": self.pan_no.get(),
            "gstin": self.gstin.get(),
            "business_type": self.business_type.get(),
        }

    def clear_form(self):
        """Clears all the fields in the form for a new entry."""
        self.business_name.set("")
        self.address_text.delete("1.0", "end")
        self.city.set("")
        self.state_name.set("")
        self.pin_code.set("")
        self.email.set("")
        self.phone.set("")
        self.pan_no.set("")
        self.gstin.set("")
        self.business_type.set("Not Applicable")


def add_company(Mode='new', parent = None):
    if parent:
        app = tk.Toplevel(parent)
        app.transient(parent)
        app.grab_set() 
        app.focus()
    else:
        app = tk.Tk()
        
    app.iconbitmap(generate_path("UI", "assets", "BillMates.ico"))
    center_window(app, 450, 530)
    app.configure(bg = "#E7EBFF")
    app.focus()
    
    form = CompanyForm(app, mode=Mode)
    form.pack(fill="both", expand=True)

    app.resizable(False, False)
    app.bind("<Escape>", lambda key: app.destroy())
    app.mainloop()

    
# --- How to Call in New and Edit Modes ---
if __name__ == "__main__":
    add_company('new')


