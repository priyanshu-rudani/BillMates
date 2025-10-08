import sys
from pathlib import Path

if getattr(sys, 'frozen', False):  # Running as a PyInstaller EXE
    root_path = Path(sys.executable).parent
else:  # Running as a Python script
    root_path = Path(__file__).parent.parent
sys.path.append(str(root_path))

import tkinter as tk
from tkinter import ttk
from utilities.path_utils import *

class AddItemUI(tk.Toplevel):
    
    def __init__(self, parent, mode="new", Item_id = None, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.parent = parent
        self.mode = mode
        self.item_id = Item_id

        center_window(self, 400, 400)
        self.title("Add New Item") if mode=="new" else self.title("Edit Item")
        self.transient(parent)
        self.grab_set() 
        self.focus()
        self.iconbitmap(generate_path("UI", "assets", "BillMates.ico"))

        self.resizable(False, False)
        self.bind("<Escape>", lambda event: Top_Close(self, self.parent))
        self.protocol("WM_DELETE_WINDOW", lambda: Top_Close(self, self.parent))

        self.create_widgets()

    def create_widgets(self):
        # Main frame with padding
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Item Details section
        item_details_frame = ttk.LabelFrame(main_frame, text="Item Details", padding="10")
        item_details_frame.pack(fill=tk.X, pady=(0, 10))

        # Item Code
        ttk.Label(item_details_frame, text="Item Code").grid(row=0, column=0, sticky="w", pady=5)
        self.item_code_entry = ttk.Entry(item_details_frame)
        self.item_code_entry.grid(row=0, column=1, sticky="ew", pady=5, padx=(10, 0))

        # Item Name
        ttk.Label(item_details_frame, text="Item Name *").grid(row=1, column=0, sticky="w", pady=5)
        self.item_name_entry = ttk.Entry(item_details_frame)
        self.item_name_entry.grid(row=1, column=1, sticky="ew", pady=5, padx=(10, 0))
        
        item_details_frame.columnconfigure(1, weight=1)

        # Pricing section
        pricing_frame = ttk.LabelFrame(main_frame, text="Pricing", padding="10")
        pricing_frame.pack(fill=tk.X, pady=(0, 10))

        # Product Price
        ttk.Label(pricing_frame, text="Product Price *").grid(row=0, column=0, sticky="w", pady=5)
        price_frame = ttk.Frame(pricing_frame)
        price_frame.grid(row=0, column=1, sticky="ew", pady=5, padx=(10, 0))
        ttk.Label(price_frame, text="₹").pack(side=tk.LEFT)
        self.price_entry = ttk.Entry(price_frame)
        self.price_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        
        # MRP
        ttk.Label(pricing_frame, text="MRP").grid(row=1, column=0, sticky="w", pady=5)
        mrp_frame = ttk.Frame(pricing_frame)
        mrp_frame.grid(row=1, column=1, sticky="ew", pady=5, padx=(10, 0))
        ttk.Label(mrp_frame, text="₹").pack(side=tk.LEFT)
        self.mrp_entry = ttk.Entry(mrp_frame)
        self.mrp_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
        
        pricing_frame.columnconfigure(1, weight=1)

        # Other Details section
        other_details_frame = ttk.LabelFrame(main_frame, text="Other Details", padding="10")
        other_details_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Sale Discount
        ttk.Label(other_details_frame, text="Discount").grid(row=0, column=0, sticky="w", pady=5)
        discount_frame = ttk.Frame(other_details_frame)
        discount_frame.grid(row=0, column=1, sticky="ew", pady=5, padx=(10, 0))
        self.discount_entry = ttk.Entry(discount_frame)
        self.discount_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Label(discount_frame, text="₹").pack(side=tk.LEFT, padx=(6, 2))

        # GST Rates
        ttk.Label(other_details_frame, text="GST Rates").grid(row=1, column=0, sticky="w", pady=5)
        gst_rates_frame = ttk.Frame(other_details_frame)
        gst_rates_frame.grid(row=1, column=1, sticky="ew", pady=5, padx=(10, 0))
        self.gst_entry = ttk.Entry(gst_rates_frame)
        self.gst_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Label(gst_rates_frame, text="%").pack(side=tk.LEFT, padx=(5, 0))
        
        other_details_frame.columnconfigure(1, weight=1)

        # Bottom buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(5, 0))

        button_text = "Add New Item" if self.mode=="new" else "Update Item"
        self.add_item_button = ttk.Button(button_frame, text=button_text, command=self.actions)
        self.add_item_button.pack(fill=tk.X)

        if self.mode == "edit":
            self.populate_data(self.item_id)

    def actions(self):
        if self.mode == "new":
            self.add_item()
        elif self.mode == "edit" and self.item_id != None:
            self.update_item(self.item_id)

    def add_item(self):
        item_code = self.item_code_entry.get().strip()
        item_name = self.item_name_entry.get().strip()
        price = self.price_entry.get().strip()
        mrp = self.mrp_entry.get().strip()
        discount = self.discount_entry.get().strip()
        gst = self.gst_entry.get().strip()

        if not item_name:
            messagebox.showerror("Validation Error", "Item Name cannot be empty.", parent=self)
            return

        if not price:
            messagebox.showerror("Validation Error", "Price cannot be empty.", parent=self)
            return

        try:
            run_query("""
                INSERT INTO Items (item_code, item_name, price, mrp, discount, gst)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (item_code, item_name, price, mrp, discount, gst))

            messagebox.showinfo("Success", "Item details added successfully!", parent=self)

            self.item_code_entry.delete(0, 'end')
            self.item_name_entry.delete(0, 'end')
            self.price_entry.delete(0, 'end')
            self.mrp_entry.delete(0, 'end')
            self.discount_entry.delete(0, 'end')
            self.gst_entry.delete(0, 'end')
            
        except Exception as e:
            messagebox.showerror("Database Error", f"An error occurred while adding the Item: {e}", parent=self)

    def update_item(self, item_id):
        item_code = self.item_code_entry.get().strip()
        item_name = self.item_name_entry.get().strip()
        price = self.price_entry.get().strip()
        mrp = self.mrp_entry.get().strip()
        discount = self.discount_entry.get().strip()
        gst = self.gst_entry.get().strip()

        if not item_name:
            messagebox.showerror("Validation Error", "Item Name cannot be empty.", parent=self)
            return

        if not price:
            messagebox.showerror("Validation Error", "Price cannot be empty.", parent=self)
            return

        try:
            run_query("""
                UPDATE Items 
                SET item_code = ?, item_name = ?, price = ?, mrp = ?, discount = ?, gst = ?
                WHERE id = ?
                """, (item_code, item_name, price, mrp, discount, gst, item_id))

            messagebox.showinfo("Success", "Item details updated successfully!", parent=self)

            self.item_code_entry.delete(0, 'end')
            self.item_name_entry.delete(0, 'end')
            self.price_entry.delete(0, 'end')
            self.mrp_entry.delete(0, 'end')
            self.discount_entry.delete(0, 'end')
            self.gst_entry.delete(0, 'end')

            self.mode = "new"
            self.item_id = None
            self.add_item_button.config(text="Add New Item")
            self.title("Add New Item")
            
        except Exception as e:
            messagebox.showerror("Database Error", f"An error occurred while updating the Item: {e}", parent=self)    

    def populate_data(self, item_id):
        item_code = fetch_data("SELECT item_code FROM Items WHERE id = ?", (item_id,))[0][0]
        item_name = fetch_data("SELECT item_name FROM Items WHERE id = ?", (item_id,))[0][0]
        price = fetch_data("SELECT price FROM Items WHERE id = ?", (item_id,))[0][0]
        mrp = fetch_data("SELECT mrp FROM Items WHERE id = ?", (item_id,))[0][0]
        discount = fetch_data("SELECT discount FROM Items WHERE id = ?", (item_id,))[0][0]
        gst = fetch_data("SELECT gst FROM Items WHERE id = ?", (item_id,))[0][0]

        self.item_code_entry.insert(0, item_code)
        self.item_name_entry.insert(0, item_name)
        self.price_entry.insert(0, price)
        self.mrp_entry.insert(0, mrp)
        self.discount_entry.insert(0, discount)
        self.gst_entry.insert(0, gst)


if __name__ == "__main__":
    root = tk.Tk()
    app = AddItemUI(root, mode="edit", Item_id= 1)
    root.mainloop()

