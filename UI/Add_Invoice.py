import sys
import os
from pathlib import Path

if getattr(sys, 'frozen', False):  # Running as a PyInstaller EXE
    root_path = Path(sys.executable).parent
else:  # Running as a Python script
    root_path = Path(__file__).parent.parent
sys.path.append(str(root_path))
 
from utilities.path_utils import *
from utilities.invoice_generator import create_invoice
import tkinter as tk
from tkinter import ttk, Canvas, Entry, Text, Button, PhotoImage, messagebox, Scrollbar, filedialog, END, Spinbox
from tkcalendar import DateEntry
import re
from datetime import datetime, timedelta

def new_invoice_ui(parent = None):

    ASSETS_PATH = Path(generate_path(root_path, "UI", "assets", "frame10"))
    
    def relative_to_assets(path: str) -> Path:
        return ASSETS_PATH / Path(path)

    # =============================================================================
    #  Save Invoice 
    # =============================================================================

    def save_invoice():
        i_invoice_no = invoice_no.get()
        i_customer_name = customer_name.get()
        i_invoice_type = invoice_type.get()
        i_payment_type = payment_type.get()
        i_date = date_entry.get()

        if not i_invoice_no:
            messagebox.showerror("Error", "Invoice Number cannot be empty.", parent=window)
            return

        if not i_customer_name or i_customer_name == "":
            messagebox.showerror("Error", "Customer Name cannot be empty.", parent=window)
            return

        if not i_date:
            messagebox.showerror("Missing Data", "Date is required.", parent=window)
            return

        inv_date = datetime.strptime(i_date, "%d/%m/%Y")
        i_due_date = inv_date + timedelta(days=30)

        inv_date = inv_date.strftime("%d/%m/%Y")
        i_due_date = i_due_date.strftime("%d/%m/%Y")

        try:
            i_total = get_total_for_invoice(i_invoice_no)
            i_paid = float(amount_paid.get()) if amount_paid.get() else 0.0
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid paid amount.", parent=window)
            return
    
        i_remarks = remark.get("1.0", tk.END).strip() if remark.get("1.0", tk.END).strip() else " "
        i_reference_no = Reference_no.get() if Reference_no.get() else " "
        i_remaining = i_total - i_paid
    
        def is_paid(remain, total):
            if remain == 0:
                return "Paid"
            elif remain > 0 and remain == total:
                return "Unpaid"
            elif remain > 0 and remain != total:
                return "Partially Paid"

        Total_Items = fetch_data("SELECT COUNT(*) FROM DummyInvoiceItems;")[0][0]
        if Total_Items <= 0:
            messagebox.showinfo("Save Error", f"Enter at least 1 Item to save the Invoice", parent=window)
            return

        if i_invoice_no.strip() == '0':
            messagebox.showinfo("Invoice No Error", "Invoice number Can not be 0", parent=window)
            invoice_no.delete(0, 'end')
            return
        
    
        result = fetch_data("""SELECT COUNT(*) FROM Invoices WHERE invoice_no = ? AND client_id = (SELECT id FROM Clients WHERE name = ? )
        """, (i_invoice_no, i_customer_name))

        if result[0][0] > 0:
            messagebox.showinfo("Invoice Exists", f"Invoice number {i_invoice_no} already exists.", parent=window)

        else:
            i_client_id = get_client_id(i_customer_name)
            
            # get dummy table items
            items = fetch_data('''
                SELECT rowid, item_code, item_name, quantity, unit, price, subtotal, discount_percent, discount_amount, GST_Rate, taxes, Total FROM DummyInvoiceItems WHERE invoice_no = ? AND client_id = ?''', 
                (i_invoice_no, i_client_id)
            )

            # Insert to Orignal Table
            for item in items:
                run_query('''
                    INSERT INTO InvoiceItems (invoice_no, client_id, item_code, item_name, quantity, unit, price, subtotal, discount_percent, discount_amount, GST_Rate, taxes, Total) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (i_invoice_no, i_client_id, item[1], item[2], item[3], item[4], item[5], item[6], item[7], item[8], item[9], item[10], item[11]))


            # Delete Dummy table data
            run_query('''
                DELETE FROM DummyInvoiceItems WHERE invoice_no = ? AND client_id = ?
                ''', (i_invoice_no, i_client_id))
            
            
            run_query('''
                INSERT INTO Invoices (invoice_no, Invoice_type, date, due_date, client_id, total, paid, remaining, remarks, reference_no, payment_type, paid_status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', 
                (i_invoice_no, i_invoice_type, i_date, i_due_date, i_client_id, i_total, i_paid, i_remaining, i_remarks, i_reference_no, i_payment_type, is_paid(i_remaining, i_total),
            ))


            Current_Balance = fetch_data(f"""SELECT closing_bal FROM Clients WHERE id = {i_client_id}""")[0][0]

            Closing_Balance = Current_Balance - i_total

            run_query(f"""UPDATE Clients SET closing_bal = {float(Closing_Balance)} WHERE id = {i_client_id}""")

            if i_paid > 0:
                run_query("""
                    INSERT INTO Payments (entity_id, entity_type, date, total_amount, payment_mode, reference_no, Expanse_type)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (i_client_id, "Income", i_date, i_paid, i_payment_type, i_invoice_no, 'Invoice Payment'))         

            
            messagebox.showinfo("Invoice Saved", f"Invoice {i_invoice_no} has been saved successfully.", parent=window)

            for row in treeview.get_children():
                treeview.delete(row)

            canvas.itemconfig(taxable_total_txt, text="0")
            canvas.itemconfig(CGST_txt, text="0.0")
            canvas.itemconfig(SGST_txt, text="0.0")
            canvas.itemconfig(IGST_txt, text="0.0")
            canvas.itemconfig(sub_total_txt, text="0.0")
            canvas.itemconfig(round_off_txt, text="0.0")
            canvas.itemconfig(grand_total_txt, text="0.0")

            customer_name.config(state='readonly')

            # Clear form fields
            invoice_no.delete(0, tk.END)
            customer_name.set('')
            payment_type.delete(0, tk.END)
            date_entry.delete(0, tk.END)
            contect_no.delete(0, tk.END)
            gst_no.delete(0, tk.END)
            amount_paid.delete(0, tk.END)
            remark.delete(1.0, tk.END)
            Reference_no.delete(0, tk.END)

    def get_total_for_invoice(invoice_no):
        i_customer_name = customer_name.get()
        i_client_id = get_client_id(i_customer_name)
    
        total = fetch_data('''
            SELECT SUM(Total) FROM DummyInvoiceItems WHERE invoice_no = ? AND client_id = ?
        ''', (invoice_no, i_client_id))
    
        return total[0][0] if total[0][0] is not None else 0.0
    
    def cleanup_unsaved_items(invoice_no):
        i_customer_name = customer_name.get()
        i_client_id = get_client_id(i_customer_name)

        try:
            # Check if the invoice exists in the Invoices table
            result = fetch_data('SELECT COUNT(*) FROM Invoices WHERE invoice_no = ? AND client_id = ?', (invoice_no, i_client_id))
            invoice_exists = result[0][0] > 0

            if not invoice_exists:
                # Delete unsaved items from the DummyInvoiceItems table if the invoice does not exist
                run_query('DELETE FROM DummyInvoiceItems WHERE invoice_no = ? AND client_id = ?', (invoice_no, i_client_id))

        except Exception as e:
            messagebox.showerror("Invoice Cleanup", f"Error: {e}", parent=window)

    def on_close(*args):
        i_invoice_no = invoice_no.get()
        if messagebox.askyesno("Exit Confirmation", "Are you sure you want to Close?", parent=window):
            cleanup_unsaved_items(i_invoice_no)
            Top_Close(window, parent)
    
    def calculate_total(*args):
        try:
            # Get the values from the input fields
            v_qty = float(qty.get() or 0)
            v_price = float(price.get() or 0)
            v_gst_rate = float(gst.get() or 0)
            v_discount_percent = float(discount.get() or 0)
    
            # Calculate subtotal (qty * price)
            subtotal = (v_qty * v_price)
            
            # Calculate discount amount (percentage based)
            discount_amount = (subtotal * v_discount_percent) / 100
            
            # Taxable amount after discount
            taxable_amount = subtotal - discount_amount
            
            # Calculate GST on taxable amount (after discount)
            gst_amount = (taxable_amount * v_gst_rate) / 100
            
            # Final item total = taxable amount + gst amount
            itemTotal = taxable_amount + gst_amount
    
            # Update the total entry field
            item_total.config(state='normal')
            item_total.delete(0, END)
            item_total.insert(0, f"{itemTotal:.2f}")
            item_total.config(state='readonly')

        except ValueError:
            # Handle any conversion errors
            item_total.config(state='normal')
            item_total.delete(0, END)
            item_total.insert(0, "Error")
            item_total.config(state='readonly')

    def update_value():
        i_invoice_no = invoice_no.get()
        i_customer_name = customer_name.get()
        i_client_id = get_client_id(i_customer_name)

        Compney_state = read_ini("PROFILE", "state")
        Clients_state = fetch_data(f"SELECT state FROM Clients WHERE id = {i_client_id}")[0][0]

        Sub_Total = fetch_data(f'SELECT SUM(subtotal) FROM DummyInvoiceItems WHERE invoice_no = {i_invoice_no} AND client_id = {i_client_id}')[0][0] or 0.0
        Discount_Amount = fetch_data(f'SELECT SUM(discount_amount) FROM DummyInvoiceItems WHERE invoice_no = {i_invoice_no} AND client_id = {i_client_id}')[0][0] or 0.0
        Total_Taxes = fetch_data(f'SELECT SUM(taxes) FROM DummyInvoiceItems WHERE invoice_no = {i_invoice_no} AND client_id = {i_client_id}')[0][0] or 0.0
        Gross_Total = fetch_data(f'SELECT SUM(Total) FROM DummyInvoiceItems WHERE invoice_no = {i_invoice_no} AND client_id = {i_client_id}')[0][0] or 0.0

        # Taxable amount = Subtotal - Discount (discount applied before tax)
        Taxable_Amount = float(Sub_Total) - float(Discount_Amount)
        
        # Total = Taxable Amount + Taxes
        Total = Taxable_Amount + float(Total_Taxes)

        if Compney_state == Clients_state:
            Central_Tax = State_Tax = float(Total_Taxes) / 2
            Integrated_Tax = 0.0
        else: 
            Integrated_Tax = float(Total_Taxes)
            Central_Tax = State_Tax = 0.0

        Round_Off = round(Total) - float(Gross_Total)
        Grand_Total = Total + Round_Off

        Taxable_Amount = round(float(Taxable_Amount), 2)
        Total_Taxes = round(float(Total_Taxes), 2)
        Central_Tax = round(float(Central_Tax), 2)
        State_Tax = round(float(State_Tax), 2)
        Integrated_Tax = round(float(Integrated_Tax), 2)
        Grand_Total = round(float(Grand_Total), 2)
        Round_Off = round(float(Round_Off), 2)
        
        
        canvas.itemconfig(sub_total_txt, text=f"{Sub_Total:.2f}")
        canvas.itemconfig(taxable_total_txt, text=f"{Taxable_Amount}")
        canvas.itemconfig(CGST_txt, text=f"{Central_Tax}")
        canvas.itemconfig(SGST_txt, text=f"{State_Tax}")
        canvas.itemconfig(IGST_txt, text=f"{Integrated_Tax}")
        canvas.itemconfig(round_off_txt, text=f"{Round_Off}")
        canvas.itemconfig(grand_total_txt, text=f"{Grand_Total}")

    def add_treeview(invoice_no):
        i_customer_name = customer_name.get()
        i_client_id = get_client_id(i_customer_name)
        # Clear any existing rows in the Treeview
        for row in treeview.get_children():
            treeview.delete(row)

        # Fetch data from the database
        rows = fetch_data('''
            SELECT rowid, item_code, item_name, quantity, unit, price, GST_Rate, taxes, discount_percent, discount_amount, Total 
            FROM DummyInvoiceItems 
            WHERE invoice_no = ? AND client_id = ?
        ''', (invoice_no, i_client_id))

        # Populate Treeview with data
        for idx, row in enumerate(rows, start=1):  # Add Sr No.

            item_id = row[0]
            if not row[1] or row[1] == "":
                item_name = row[2]
            else: 
                item_name = f"{row[2]} ({row[1]})"
            quantity = f"{row[3]} [{row[4]}]"
            price = row[5]
            gst = f"{row[6]}% ({row[7]})" if row[7] != 0 else "0"
            discount_pct = f"{row[8]}% (₹{row[9]})" if row[8] > 0 else "0"
            Total = row[10]

            # Insert data into Treeview including Delete column
            treeview.insert("", "end", iid=item_id, values=(idx, item_name, quantity, price, gst, discount_pct, Total, "X"))

        # Bind keyboard delete functionality
        treeview.bind("<Delete>", delete_item)
        treeview.bind("<Double-1>", on_treeview_double_click)
        treeview.bind("<Button-1>", on_treeview_button_click)

    edit_mode = {'item_id': None}  # To track if we are editing an item

    def on_treeview_double_click(event):
        # Detect row and column clicked
        row_id = treeview.identify_row(event.y)
        col_id = treeview.identify_column(event.x)

        if row_id and col_id != "#8":  # Exclude Delete column
            selected_item = row_id
            item_values = treeview.item(selected_item, 'values')

            gst_string = item_values[4]  # Example input
            match = re.search(r"(\d+(\.\d*)?)%", gst_string)  # Extract digits before %
            if match:
                gst_value = match.group(1)  # Extract matched digits
            else:
                gst_value = "0"  # Default to "0" if no match found

            qty_string = item_values[2]
            qmatch = re.search(r"(\d+(\.\d+)?)\s*\[", qty_string)
            if qmatch:
                qty_value = qmatch.group(1)  # Extract matched digits
            else:
                qty_value = "0"

            # Extract discount percentage
            discount_string = item_values[5]
            dmatch = re.search(r"(\d+(\.\d+)?)%", discount_string)
            if dmatch:
                discount_value = dmatch.group(1)
            else:
                discount_value = "0"

            # Populate entry fields with selected item values
            item_name.delete(0, END)
            qty.delete(0, END)
            price.delete(0, END)
            gst.delete(0, END)
            discount.delete(0, END)

            item_name.insert(0, item_values[1])
            qty.insert(0, qty_value)
            price.insert(0, item_values[3])
            gst.insert(0, gst_value)
            discount.insert(0, discount_value)

            # Save current selected item ID for update
            edit_mode['item_id'] = selected_item

    def on_treeview_button_click(event):
        # Detect row and column clicked
        region = treeview.identify_region(event.x, event.y)
        row_id = treeview.identify_row(event.y)
        col_id = treeview.identify_column(event.x)

        if region == "cell" and col_id == "#8":  # Delete button column
            treeview.selection_set(row_id)  # Ensure the row is selected
            delete_item()

    def update_item(selected_item):
        try:
            # Get updated values from entry fields
            updated_item_code = item_code.get()
            updated_item_name = item_name.get()
            updated_unit = entry_9.get()
            updated_qty = round(float(qty.get()), 2) if qty.get() else 0
            updated_price = round(float(price.get()), 2) if price.get() else 0
            updated_gst_rate = round(float(gst.get()), 2) if gst.get() else 0
            updated_discount_percent = round(float(discount.get()), 2) if discount.get() else 0

            updated_subtotal = round((updated_qty * updated_price), 2)
            updated_discount_amount = round((updated_subtotal * updated_discount_percent) / 100, 2)
            taxable_amount = round((updated_subtotal - updated_discount_amount), 2)
            gst_amount = round(((taxable_amount * updated_gst_rate) / 100), 2)
            updated_total = round((taxable_amount + gst_amount), 2)

            # Update the database
            run_query('''
                UPDATE DummyInvoiceItems 
                SET item_code = ?, item_name = ?, quantity = ?, unit = ?, price = ?, subtotal = ?, discount_percent = ?, discount_amount = ?, GST_Rate = ?, taxes = ?, Total = ?
                WHERE rowid = ?
            ''', (updated_item_code, updated_item_name, updated_qty, updated_unit, updated_price, updated_subtotal, updated_discount_percent, updated_discount_amount, updated_gst_rate, gst_amount, updated_total, selected_item))

            treeview.item(selected_item, values=(
                treeview.index(selected_item) + 1,
                f"{updated_item_name} ({updated_item_code})",
                f"{updated_qty} [{updated_unit}]",
                updated_price,
                f"{updated_gst_rate}% ({gst_amount})",
                f"{updated_discount_percent}% (₹{updated_discount_amount})",
                updated_total,
                "X"
            ))

            messagebox.showinfo("Item Updated", "Item has been updated successfully.", parent=window)
            edit_mode['item_id'] = None  # Exit edit mode

        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid data for the item fields.", parent=window)
        except Exception as e:
            messagebox.showerror("Error", str(e), parent=window)

    def delete_item(event=None):
        # Get selected item
        selected_item = treeview.selection()
        if selected_item:
            # Confirm deletion
            confirm = messagebox.askyesno("Delete Item", "Are you sure you want to delete this item?", parent=window)
            if confirm:
                try:
                    # Remove item from the database
                    run_query('''
                        DELETE FROM DummyInvoiceItems WHERE rowid = ?
                    ''', (selected_item[0],))

                    # Remove item from the Treeview
                    treeview.delete(selected_item)
                    messagebox.showinfo("Item Deleted", "Item has been deleted successfully.", parent=window)
                    update_value()
                except Exception as e:
                    messagebox.showerror("Error", str(e))
        else:
            messagebox.showwarning("No Selection", "Please select an item to delete.", parent=window)

    def check_invoice_exists(i_invoice_no, i_customer_name):

        result = fetch_data("""SELECT COUNT(*) FROM Invoices WHERE invoice_no = ? AND client_id = (SELECT id FROM Clients WHERE name = ? )
        """, (i_invoice_no, i_customer_name))

        if result[0][0] > 0:
            messagebox.showinfo("Invoice Exists", f"Invoice number already exists.", parent=window)
            
            invoice_no.delete(0, 'end')
            return
        
    def add_item():
        i_invoice_no = invoice_no.get().strip()
        i_customer_name = customer_name.get()
        i_date = date_entry.get()

        if not i_invoice_no:
            messagebox.showerror("Missing Invoice Number", "Please enter an Invoice Number before adding items.", parent=window)
            return
        
        if not i_customer_name:
            messagebox.showerror("Error", "Customer Name cannot be empty.", parent=window)
            return
        
        if not i_date:
            messagebox.showerror("Missing Data", "Date is required.", parent=window)
            return
        
        if i_invoice_no.strip() == '0':
            messagebox.showinfo("Invoice No Error", f"Invoice number Can not be 0", parent=window)
            invoice_no.delete(0, 'end')
            return
        
        Total_Items = fetch_data("SELECT COUNT(*) FROM DummyInvoiceItems;")[0][0]

        if Total_Items >= 15:
            messagebox.showinfo("Max Limit Reached", f"You can't add more then 15 items per invoice", parent=window)
            return

        # Get item details
        i_item_code = item_code.get()
        i_item_name = item_name.get()
        i_unit = entry_9.get()
        i_discount_percent = round(float(discount.get()), 2) if discount.get() else 0.0
        try:
            i_gst_rate = round(float(gst.get()), 2) if gst.get() else 0
            
            i_qty = round(float(qty.get()), 2)
            i_price = round(float(price.get()), 2)
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid quantity and price.", parent=window)
            return

        # Calculate subtotal
        i_subtotal = round((i_qty * i_price), 2)
        i_discount_amount = round((i_subtotal * i_discount_percent) / 100, 2)
        taxable_amount = round((i_subtotal - i_discount_amount), 2)
        gst_amount = round((taxable_amount * i_gst_rate) / 100, 2)
        final_total = round((taxable_amount + gst_amount), 2)


        if edit_mode['item_id']:
            update_item(edit_mode['item_id'])
        else:
            i_client_id = get_client_id(i_customer_name)

            # Add new item to the dummy table
            run_query('''
                INSERT INTO DummyInvoiceItems (invoice_no, client_id , item_code, item_name, quantity, unit, price, subtotal, discount_percent, discount_amount, GST_Rate, taxes, Total)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (i_invoice_no, i_client_id , i_item_code, i_item_name, i_qty, i_unit, i_price, i_subtotal, i_discount_percent, i_discount_amount, i_gst_rate, gst_amount, final_total))


        update_value()

        if not amount_paid.get() or amount_paid.get() == "":
            amount_paid.delete(0, END)
            amount_paid.insert(0,"0")
            update_payment()
        else:
            update_payment()
    
        add_treeview(i_invoice_no)
        customer_name.config(state='disabled')

        # Clear fields and exit edit mode
        item_code.delete(0, END)
        item_name.delete(0, END)
        qty.delete(0, END)
        qty.insert(0, "0")
        price.delete(0, END)
        price.insert(0, "0")
        gst.delete(0, END)
        gst.insert(0, "0")
        discount.delete(0, END)
        discount.insert(0, "0")
        edit_mode['item_id'] = None

    def update_payment(*args):
        try:
            i_total = get_total_for_invoice(invoice_no.get())
            i_paid = float(amount_paid.get()) if amount_paid.get() else 0.0
            i_remaining = i_total - i_paid
            amount_remain.config(state='normal')
            amount_remain.delete(0, tk.END)
            amount_remain.insert(0, f"{i_remaining:.2f}")
            amount_remain.config(state='readonly')
        except ValueError:
            amount_remain.config(state='normal')
            amount_remain.delete(0, tk.END)
            amount_remain.config(state='readonly')

    def export_invoice():
        inv = invoice_no.get()
        i_customer_name = customer_name.get()
        i_date = date_entry.get()
        id = get_client_id(str(i_customer_name))

        if not inv or inv == "":
            messagebox.showerror("Error", "Invoice Number cannot be empty.", parent=window)
            return

        if inv.strip() == '0':
            messagebox.showinfo("Invoice No Error", f"Invoice number Can not be 0", parent=window)
            invoice_no.delete(0, 'end')
            return
        
        if not i_customer_name or i_customer_name == "":
            messagebox.showerror("Error", "Customer Name cannot be empty.", parent=window)
            return

        if not i_date:
            messagebox.showerror("Missing Data", "Date is required.", parent=window)
            return
        
        if id == 0:
            messagebox.showerror("Missing Data", "Client Id not found from name", parent=window)
            return 
        
        display_Inv_no = "INV" + str(inv).zfill(3)

        inv_date = datetime.strptime(i_date, "%d/%m/%Y")
        safe_date = inv_date.strftime("%d-%m-%Y")

        filename = f"{display_Inv_no}_{safe_date}_{i_customer_name}.pdf"
        file_path = filedialog.asksaveasfilename(
            title="Save PDF At",
            initialfile=filename,
            defaultextension=".pdf",  # Set the default extension
            filetypes=[("PDF Files", "*.pdf")],
            parent=window
        )

        if file_path:
            save_invoice()
            create_invoice(id, inv, file_path)

            if not os.path.exists(file_path):
                messagebox.showerror("Export error", "Failed to Generate PDF", parent=window)
                return
            else:
                response = messagebox.askquestion("Invoice Saved", f"Invoice saved at {file_path} \nDo you want to open the PDF?", parent=window)
                if response == 'yes':
                    os.startfile(file_path)

    def get_client_names():
        try:
            # Fetch names of all clients where client_type is 'Client'
            result = fetch_data("SELECT name FROM Clients WHERE client_type = 'Client'")
            clients = [row[0] for row in result]
            return clients
        except Exception as e:
            messagebox.showinfo("Error", f"Error fetching client names: {e}", parent=window)
            return []

    def on_client_selected(event):
        selected_client = customer_name.get()
        client_id = get_client_id(selected_client)
        if selected_client:
            try:
                invoice_no.delete(0, 'end')
                gst_no.delete(0, 'end')
                contect_no.delete(0, 'end')

                # Fetch data for the selected client
                client_data = fetch_data("SELECT * FROM Clients WHERE client_type = 'Client' AND name = ?", (selected_client,))

                result = fetch_data('''SELECT MAX(invoice_no) FROM Invoices WHERE client_id = ?''', (client_id,))
                
                if not result[0] or result[0][0] is None:
                    db_invoice_no = 1
                else:
                    db_invoice_no = result[0][0] + 1

                Number = "00+ 00000 00000"

                if len(client_data[0][2]) == 10:
                    Number = f"91+ {client_data[0][2][:5]} {client_data[0][2][5:]}"
                    
                if client_data:
                    # Assuming columns are in order: id, name, contact_no, gst, city, state, client_type
                    contect_no.insert(0, Number)
                    gst_no.insert(0, client_data[0][3])
                    invoice_no.insert(0, db_invoice_no)

            except Exception as e:
                messagebox.showinfo("Error", f"Error fetching client Data: {e}", parent=window)

    def on_item_code_select(event):
        selection = listbox.curselection()
        if selection:
            selected_item_code = listbox.get(selection[0])
            item_code.delete(0, END)
            item_code.insert(0, selected_item_code)
            
            # Fetch item details
            item_details = fetch_data(f"SELECT item_name, price FROM Items WHERE item_code = '{selected_item_code}' LIMIT 1")
            if item_details:
                item_name.delete(0, END)
                item_name.insert(0, item_details[0][0])
                price.delete(0, END)
                price.insert(0, item_details[0][1])
            
            listbox.place_forget()

    def on_item_name_select(event):
        selection = listbox.curselection()
        if selection:
            selected_item_name = listbox.get(selection[0])
            item_name.delete(0, END)
            item_name.insert(0, selected_item_name)
            
            # Fetch item details
            item_details = fetch_data(f"SELECT item_code, price FROM Items WHERE item_name = '{selected_item_name}' LIMIT 1")
            if item_details:
                item_code.delete(0, END)
                item_code.insert(0, item_details[0][0])
                price.delete(0, END)
                price.insert(0, item_details[0][1])
            
            listbox.place_forget()


    # =============================================================================
    #  UI Creation
    # =============================================================================
    window = tk.Toplevel(parent)
    center_window(window, 1280, 720)
    window.resizable(False, False)
    window.title("Invoice")
    window.configure(bg = "#E7EBFF")
    window.transient(parent)
    window.grab_set() 
    window.focus()

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

    float_validation = window.register(lambda value: value == "" or value.replace(".", "", 1).isdigit())

# =====================================================================
# List View of added items
# =====================================================================

    # Define Treeview frame and dimensions
    treeview_frame_x = 20
    treeview_frame_y = 168
    treeview_width = 1230
    treeview_height = 368

    # Add Scrollbar
    scrollbar = Scrollbar(window, orient="vertical")
    scrollbar.place(x=treeview_frame_x + treeview_width - 20, y=treeview_frame_y, height=treeview_height)

    # Create Treeview
    columns = ("Sr No.", "Item Name", "Quantity", "Price", "Taxes", "Discount %", "Subtotal", "Delete")
    treeview = ttk.Treeview(
        window,
        columns=columns,
        show="headings",
        yscrollcommand=scrollbar.set,
        height=16,
        style="Treeview.Heading"
    )
    treeview.place(x=treeview_frame_x, y=treeview_frame_y, width=treeview_width, height=treeview_height)

    scrollbar.config(command=treeview.yview)

    # Define custom style for the Treeview headers
    style = ttk.Style(window)
    style.configure("Treeview.Heading", font=("Arial", 10, "bold"), background="#f0f0f0")
    style.configure("Treeview", font=("Arial", 9))

    # Define column headings with specific widths
    columns_config = [
        ("Sr No.", 74),
        ("Item Name", 354),
        ("Quantity", 155),
        ("Price", 150),
        ("Taxes", 127),
        ("Discount %", 140),
        ("Subtotal", 160),
        ("Delete", 74)
    ]

    
    for col_name, col_width in columns_config:
        treeview.heading(col_name, text=col_name, anchor="center")
        treeview.column(col_name, anchor="center", width=col_width, stretch=False)

    

# =====================================================================
# All Line of Text
# =====================================================================
    
    canvas.create_text(
        27.0,
        28.0,
        anchor="nw",
        text="Client Name",
        fill="#000000",
        font=("VarelaRound Regular", 12 * -1)
    )
    
    canvas.create_text(
        262.0,
        28.0,
        anchor="nw",
        text="Client No.",
        fill="#000000",
        font=("VarelaRound Regular", 12 * -1)
    )
    
    canvas.create_text(
        467.0,
        28.0,
        anchor="nw",
        text="Invoice No.",
        fill="#000000",
        font=("VarelaRound Regular", 12 * -1)
    )
    
    canvas.create_text(
        662.0,
        28.0,
        anchor="nw",
        text="Invoice Date",
        fill="#000000",
        font=("VarelaRound Regular", 12 * -1)
    )

    canvas.create_text(
        877.0,
        28.0,
        anchor="nw",
        text="Invoice Type",
        fill="#000000",
        font=("VarelaRound Regular", 12 * -1)
    )
    
    canvas.create_text(
        1022.0,
        28.0,
        anchor="nw",
        text="Client GST No.",
        fill="#000000",
        font=("VarelaRound Regular", 12 * -1)
    )
    
    canvas.create_text(
        27.0,
        102.0,
        anchor="nw",
        text="HSN Code",
        fill="#000000",
        font=("VarelaRound Regular", 12 * -1)
    )
    
    canvas.create_text(
        166.0,
        102.0,
        anchor="nw",
        text="Item Name",
        fill="#000000",
        font=("VarelaRound Regular", 12 * -1)
    )
    
    canvas.create_text(
        445.0,
        102.0,
        anchor="nw",
        text="Quantity ",
        fill="#000000",
        font=("VarelaRound Regular", 12 * -1)
    )

    canvas.create_text(
        574.0,
        102.0,
        anchor="nw",
        text="Unit",
        fill="#000000",
        font=("VarelaRound Regular", 12 * -1)
    )
    
    
    canvas.create_text(
        683.0,
        102.0,
        anchor="nw",
        text="Sale Price",
        fill="#000000",
        font=("VarelaRound Regular", 12 * -1)
    )

    canvas.create_text(
        951.0,
        102.0,
        anchor="nw",
        text="GST (%)",
        fill="#000000",
        font=("VarelaRound Regular", 12 * -1)
    )
    
    canvas.create_text(
        822.0,
        102.0,
        anchor="nw",
        text="Discount (%)",
        fill="#000000",
        font=("VarelaRound Regular", 12 * -1)
    )
    
    canvas.create_text(
        1080.0,
        102.0,
        anchor="nw",
        text="Item Total",
        fill="#000000",
        font=("VarelaRound Regular", 12 * -1)
    )
    
    canvas.create_text(
        28.0,
        552.0,
        anchor="nw",
        text="Reference No. ",
        fill="#000000",
        font=("VarelaRound Regular", 12 * -1)
    )

    canvas.create_text(
        28.0,
        607.0,
        anchor="nw",
        text="Remarks",
        fill="#000000",
        font=("VarelaRound Regular", 12 * -1)
    )

        
    canvas.create_text(
        303.0,
        556.0,
        anchor="nw",
        text="Payment Type",
        fill="#000000",
        font=("VarelaRound Regular", 12 * -1)
    )
    
    canvas.create_text(
        303.0,
        605.0,
        anchor="nw",
        text="Payment Amount",
        fill="#000000",
        font=("VarelaRound Regular", 12 * -1)
    )

    canvas.create_text(
        303.0,
        655.0,
        anchor="nw",
        text="Remaining Amount ",
        fill="#000000",
        font=("VarelaRound Regular", 12 * -1)
    )

    # Summary section labels
    
    canvas.create_text(
        735.0,
        548.0,
        anchor="nw",
        text="Taxable Total",
        fill="#000000",
        font=("Poppins SemiBold", 14 * -1)
    )

    canvas.create_text(
        735.0,
        574.0,
        anchor="nw",
        text="CGST",
        fill="#000000",
        font=("VarelaRound Regular", 14 * -1)
    )

    canvas.create_text(
        735.0,
        596.0,
        anchor="nw",
        text="SGST",
        fill="#000000",
        font=("VarelaRound Regular", 14 * -1)
    )

    canvas.create_text(
        735.0,
        618.0,
        anchor="nw",
        text="IGST",
        fill="#000000",
        font=("VarelaRound Regular", 14 * -1)
    )

    canvas.create_text(
        735.0,
        640.0,
        anchor="nw",
        text="Sub Total",
        fill="#000000",
        font=("Poppins SemiBold", 14 * -1)
    )

    canvas.create_text(
        735.0,
        665.0,
        anchor="nw",
        text="Round Off",
        fill="#000000",
        font=("VarelaRound Regular", 14 * -1)
    )

    canvas.create_text(
        735.0,
        685.0,
        anchor="nw",
        text="Grand Total",
        fill="#000000",
        font=("Poppins SemiBold", 14 * -1)
    )

    # Summary value texts
    taxable_total_txt = canvas.create_text(
        855.0,
        548.0,
        anchor="nw",
        text="0.0",
        fill="#000000",
        font=("Poppins SemiBold", 14 * -1)
    )

    CGST_txt = canvas.create_text(
        855.0,
        574.0,
        anchor="nw",
        text="0.0",
        fill="#000000",
        font=("VarelaRound Regular", 14 * -1)
    )

    SGST_txt = canvas.create_text(
        855.0,
        596.0,
        anchor="nw",
        text="0.0",
        fill="#000000",
        font=("VarelaRound Regular", 14 * -1)
    )

    IGST_txt = canvas.create_text(
        855.0,
        618.0,
        anchor="nw",
        text="0.0",
        fill="#000000",
        font=("VarelaRound Regular", 14 * -1)
    )

    sub_total_txt = canvas.create_text(
        855.0,
        640.0,
        anchor="nw",
        text="0.0",
        fill="#000000",
        font=("Poppins SemiBold", 14 * -1)
    )

    round_off_txt = canvas.create_text(
        855.0,
        665.0,
        anchor="nw",
        text="0.0",
        fill="#000000",
        font=("VarelaRound Regular", 14 * -1)
    )

    grand_total_txt = canvas.create_text(
        855.0,
        685.0,
        anchor="nw",
        text="0.0",
        fill="#000000",
        font=("Poppins SemiBold", 14 * -1)
    )
    

    # Customer details fields
    customer_name = ttk.Combobox(
        window, 
        values=get_client_names(), 
        state="readonly", 
        font=("VarelaRound Regular", 13 * -1)
    )
    customer_name.place(
        x=27.0,
        y=47.0,
        width=210.0,
        height=25.0
    )
    customer_name.bind("<<ComboboxSelected>>", on_client_selected)

    contect_no = Entry(window,
        bd=1,
        bg="#FFFFFF",
        fg="#000716",
        cursor="xterm",
        font=("VarelaRound Regular", 14 * -1),
        highlightthickness=0
    )
    contect_no.place(
        x=262.0,
        y=47.0,
        width=180.0,
        height=25.0
    )

    invoice_no = Entry(window,
        bd=1,
        bg="#FFFFFF",
        fg="#000716",
        cursor="xterm",
        font=("VarelaRound Regular", 14 * -1),
        highlightthickness=0
    )
    invoice_no.place(
        x=467.0,
        y=47.0,
        width=170.0,
        height=25.0
    )

    def on_invoice_no_change(event):
        T_invoice_number = invoice_no.get()
        T_customer_name = customer_name.get()
        check_invoice_exists(T_invoice_number, T_customer_name)
        
    invoice_no.bind("<KeyRelease>", on_invoice_no_change)

    
    date_entry = DateEntry(window, width=12, background="#000000", foreground="white", borderwidth=2, date_pattern='dd/mm/yyyy', font=("VarelaRound Regular", 13 * -1))
    date_entry.place(
        x=662.0,
        y=47.0,
        width=190.0,
        height=25.0
    )

    invoice_type = ttk.Combobox(
        window, 
        values=["GST Sales", "Non-GST Sales"], 
        state="readonly", 
        font=("VarelaRound Regular", 14 * -1)
    )
    invoice_type.set("GST Sales")
    invoice_type.place(
        x=877.0,
        y=47.0,
        width=120.0,
        height=25.0
    )

    def gst_enable(event):
        if invoice_type.get() == "GST Sales":
            gst_no.config(state="normal")
            gst.config(state="normal")
        else:
            gst_no.config(state="disabled")
            gst.delete(0,END)
            gst.insert(0,"0")
            gst.config(state="disabled")
    
    invoice_type.bind("<<ComboboxSelected>>", gst_enable)
    
    gst_no = Entry(window,
        bd=1,
        bg="#FFFFFF",
        fg="#000716",
        cursor="xterm",
        font=("VarelaRound Regular", 14 * -1),
        highlightthickness=0
    )
    gst_no.place(
        x=1022.0,
        y=47.0,
        width=170.0,
        height=25.0
    )
    

    item_code = Entry(window,
        bd=1,
        bg="#FFFFFF",
        fg="#000716",
        cursor="xterm",
        font=("VarelaRound Regular", 14 * -1),
        highlightthickness=0
    )
    item_code.place(
        x=27.0,
        y=122.0,
        width=120.0,
        height=25.0
    )

    quary = """SELECT DISTINCT item_code FROM Items;"""
    data = [row[0] for row in fetch_data(quary)]
    listbox = tk.Listbox(window, font=("VarelaRound Regular", 14 * -1), height=5)
    # SearchBox(item_code, listbox, data)
    listbox.bind('<<ListboxSelect>>', on_item_code_select)
    
    

    item_name = Entry(window,
        bd=1,
        bg="#FFFFFF",
        fg="#000716",
        cursor="xterm",
        font=("VarelaRound Regular", 14 * -1),
        highlightthickness=0
    )
    item_name.place(
        x=166.0,
        y=122.0,
        width=260.0,
        height=25.0
    )

    quary = """SELECT DISTINCT item_name FROM Items;"""
    data = [row[0] for row in fetch_data(quary)]
    listbox = tk.Listbox(window, font=("VarelaRound Regular", 14 * -1), height=5)
    # SearchBox(item_name, listbox, data)
    listbox.bind('<<ListboxSelect>>', on_item_name_select)


    qty = tk.Spinbox(
        window, 
        from_=0.0, 
        to=100.0, 
        increment=1, 
        format="%.2f", 
        width=30, 
        validate="key",
        validatecommand=(float_validation, "%P"),
        font=("VarelaRound Regular", 14 * -1)
    )
    qty.place(
        x=445.0,
        y=122.0,
        width=110.0,
        height=25.0
    )
    qty.bind("<FocusOut>", calculate_total)
    qty.bind("<KeyRelease>", calculate_total)

    unites = ["QTY","Meter","Pieces","Inch","CM","Roll"]
    entry_9 = ttk.Combobox(window, values=unites, state="readonly", font=("VarelaRound Regular", 14 * -1))
    entry_9.current(0)
    entry_9.place(
        x=574.0,
        y=122.0,
        width=90.0,
        height=25.0
    )

    price = Entry(
        window,
        bd=1,
        bg="#FFFFFF",
        fg="#000716",
        cursor="xterm",
        highlightthickness=1,
        validate="key",
        validatecommand=(float_validation, "%P"),
        font=("VarelaRound Regular", 14 * -1)
    )
    price.place(
        x=683.0,
        y=122.0,
        width=120.0,
        height=25.0
    )
    price.bind("<FocusOut>", calculate_total)
    price.bind("<KeyRelease>", calculate_total)

    gst = Entry(
        window,
        bd=1,
        bg="#FFFFFF",
        fg="#000716",
        cursor="xterm",
        highlightthickness=1,
        validate="key",
        validatecommand=(float_validation, "%P"),
        font=("VarelaRound Regular", 14 * -1)
    )
    gst.place(
        x=951.0,
        y=122.0,
        width=110.0,
        height=25.0
    )

    gst.bind("<FocusOut>", calculate_total)
    gst.bind("<KeyRelease>", calculate_total)
    
    discount = Entry(window,
        bd=1,
        bg="#FFFFFF",
        fg="#000716",
        cursor="xterm",
        highlightthickness=1,
        validate="key",
        validatecommand=(float_validation, "%P"),
        font=("VarelaRound Regular", 14 * -1)
    )
    discount.place(
        x=822.0,
        y=122.0,
        width=110.0,
        height=25.0
    )
    discount.bind("<FocusOut>", calculate_total)
    discount.bind("<KeyRelease>", calculate_total)



    item_total = Entry(window,
        bd=1,
        bg="#FFFFFF",
        fg="#000000",
        highlightthickness=1,
        font=("VarelaRound Regular", 14 * -1),
        state="readonly"
    )
    item_total.place(
        x=1080.0,
        y=122.0,
        width=110.0,
        height=25.0
    )


    Reference_no = Entry(window,
        bd=1,
        bg="#FFFFFF",
        fg="#000716",
        cursor="xterm",
        font=("VarelaRound Regular", 14 * -1),
        highlightthickness=0
    )
    Reference_no.place(
        x=28.0,
        y=574.0,
        width=240.0,
        height=25.0
    )
    
# Payment Type
    paymentMode = ["Cash","UPI","Net Banking","Check", "Card"]
    payment_type = ttk.Combobox(window, values=paymentMode, state="readonly")
    payment_type.current(0)
    payment_type.place(
        x=303.0,
        y=574.0,
        width=160.0,
        height=25.0
    )
    
    amount_paid = Entry(window,
        bd=1,
        bg="#FFFFFF",
        fg="#000716",
        cursor="xterm",
        font=("VarelaRound Regular", 14 * -1),
        validate="key",
        validatecommand=(float_validation, "%P"),
        highlightthickness=0
    )
    amount_paid.place(
        x=303.0,
        y=623.0,
        width=160.0,
        height=25.0
    )
    amount_paid.bind("<FocusOut>", update_payment)
    amount_paid.bind("<KeyRelease>", update_payment)

    amount_remain = Entry(window,
        bd=1,
        bg="#FFFFFF",
        fg="#000716",
        font=("VarelaRound Regular", 14 * -1),
        state="readonly",
        highlightthickness=0
    )
    amount_remain.place(
        x=303.0,
        y=672.0,
        width=160.0,
        height=25.0
    )

    
    remark = Text(window,
        bd=1,
        bg="#FFFFFF",
        fg="#000716",
        cursor="xterm",
        font=("VarelaRound Regular", 14 * -1),
        highlightthickness=0
    )
    remark.place(
        x=28.0,
        y=627.0,
        width=240.0,
        height=70.0
    )
    
    
    button_image_2 = PhotoImage(
        file=relative_to_assets("button_2.png"))
    button_add_item = Button(
        window,
        image=button_image_2,
        borderwidth=0,
        highlightthickness=0,
        cursor="hand2", 
        command= add_item,
        relief="flat"
    )
    button_add_item.place(
        x=1209.0,
        y=109.0,
        width=40.0,
        height=40.0
    )

    button_image_4 = PhotoImage(file=relative_to_assets("button_4.png"))
    button_4 = Button(
        window,
        image=button_image_4,
        borderwidth=0,
        highlightthickness=0,
        cursor="hand2", 
        command=save_invoice,
        relief="flat"
    )
    button_4.place(
        x=1072.0,
        y=568.0,
        width=170.0,
        height=50.0
    )
    
    button_image_3 = PhotoImage(
        file=relative_to_assets("button_3.png"))
    button_3 = Button(
        window,
        image=button_image_3,
        borderwidth=0,
        highlightthickness=0,
        cursor="hand2", 
        command=export_invoice,
        relief="flat"
    )
    button_3.place(
        x=1072.0,
        y=639.0,
        width=170.0,
        height=50.0
    )


    window.bind('<Control-s>', lambda event: save_invoice())
    window.bind('<Control-p>', lambda event: export_invoice())
    window.bind('<Shift-Return>', lambda event: add_item())
    
    window.resizable(False, False)
    window.protocol("WM_DELETE_WINDOW", on_close)
    window.bind("<Escape>", on_close)
    window.mainloop()


if __name__ == "__main__":
    new_invoice_ui()