import sys
from pathlib import Path

if getattr(sys, 'frozen', False):  # Running as a PyInstaller EXE
    root_path = Path(sys.executable).parent
else:  # Running as a Python script
    root_path = Path(__file__).parent.parent
sys.path.append(str(root_path))
 
from utilities.path_utils import *
import tkinter as tk
import re
from datetime import datetime
from tkinter import ttk
from tkcalendar import DateEntry
from utilities import text

def addChequeBook_ui(ChequeBook_id = None, parent = None):

    def submit_form():
        bookName = cheque_name_var.get()
        bankName = bank_name_var.get()
        accountHolder = acc_holder_var.get()
        accountNo = acc_no_var.get()
        startCq = start_cheque_var.get()
        currentCq = current_cheque_var.get()
        totalCq = total_cheques_var.get()
        date = issued_date_var.get()

        if not bookName:
            messagebox.showwarning("Missing Data", "Please enter Cheque Book Name.", parent=window)
            return
        elif not startCq:
            messagebox.showwarning("Missing Data", "Please enter Starting Cheque Number.", parent=window)
            return
        elif not currentCq:
            messagebox.showwarning("Missing Data", "Please enter Current Cheque Number.", parent=window)
            return
        elif not totalCq:
            messagebox.showwarning("Missing Data", "Please enter Total Cheque Number.", parent=window)
            return
        elif not date:
            messagebox.showwarning("Missing Data", "Please enter Cheque Date.", parent=window)
            return
        
        if ChequeBook_id:
            try:
                query = f"""
                    UPDATE ChequeBook SET
                        book_name = '{bookName}',
                        bank_name = '{bankName}', 
                        holder_name = '{accountHolder}', 
                        account_no = '{accountNo}', 
                        starting_ChequeNo = {startCq}, 
                        Current_ChequeNo = {currentCq}, 
                        total_cheques = {totalCq}, 
                        issued_date = '{date}'
                    WHERE id = {ChequeBook_id}
                """
                run_query(query, db='Cheque.db')
            except ValueError:
                messagebox.showwarning("Database Error", "Cheque Book not Updated.", parent=window)
        
        else:
            isNameExist = fetch_data(f"SELECT 1 FROM ChequeBook WHERE book_name = '{bookName}';", db='Cheque.db')
            if isNameExist:
                messagebox.showwarning("Duplicate Entry", "Cheque Book name is already exists try with other name.", parent=window)
                return

            if not bankName or accountHolder or accountNo:
                response = messagebox.askyesno(
                    "Warning!",
                    "Cheque book details are missing.\nDo you still want to create Cheque Book?",
                    icon="warning"
                )
                if not response:
                    return

            try:
                run_query(f"""
                    INSERT INTO ChequeBook (
                        book_name, bank_name, holder_name, account_no, starting_ChequeNo, Current_ChequeNo, total_cheques, issued_date
                    ) VALUES (
                        '{bookName}', '{bankName}', '{accountHolder}', '{accountNo}', {startCq}, {currentCq}, {totalCq}, '{date}');
                """, db='Cheque.db')
            except ValueError:
                messagebox.showwarning("Database Error", "Cheque Book not Added.", parent=window)

        cheque_name_var.set("")
        acc_holder_var.set("")
        acc_no_var.set("")
        start_cheque_var.set("")
        current_cheque_var.set("")
        total_cheques_var.set("")
        bankName_Entry.set("")
        date_entry.set_date(datetime.now())

        if ChequeBook_id:
            messagebox.showinfo("Success", "Cheque Book Updated Successfully!", parent=window)
            submit_btn.configure(text="Add Cheque Book")
            window.grab_release()
            window.destroy()
        else:
            messagebox.showinfo("Success", "Cheque Book Saved Successfully!", parent=window)

        
        

    def Load_ChequeBook(ChequeBook_id):

        filter = f"SELECT * FROM ChequeBook WHERE id = {ChequeBook_id}"
        Data = fetch_data(filter, db="Cheque.db")[0]

        cheque_name_var.set(Data[1])
        bankName_Entry.set(Data[2])
        acc_holder_var.set(Data[3])
        acc_no_var.set(Data[4])
        start_cheque_var.set(Data[5])
        current_cheque_var.set(Data[6])
        total_cheques_var.set(Data[7])
        date_entry.set_date(datetime.strptime(Data[8], "%d/%m/%Y"))


    window = tk.Toplevel(parent)
    window.focus()
    center_window(window, 540, 490)
    window.iconbitmap(generate_path("UI", "assets", "BillMates.ico"))
    window.transient(parent)
    window.grab_set()
    window.title("Add Cheque Book")
    window.configure(bg="#E7EBFF")

    style = ttk.Style()
    style.configure("TLabel", font=("Segoe UI", 11), background="#E7EBFF")
    style.configure("TEntry", font=("Segoe UI", 11))
    style.configure("TButton", font=("Segoe UI", 10, "bold"), padding=6)
    style.configure("Custom.TLabelframe", background="#E7EBFF")
    style.configure("Custom.TLabelframe.Label", background="#E7EBFF", font=("Segoe UI", 10, "bold"))

    # Variables
    cheque_name_var = tk.StringVar()
    bank_name_var = tk.StringVar()
    acc_holder_var = tk.StringVar()
    acc_no_var = tk.StringVar()
    start_cheque_var = tk.StringVar()
    current_cheque_var = tk.StringVar()
    total_cheques_var = tk.StringVar()
    issued_date_var = tk.StringVar()

    int5_validation = window.register(lambda value: re.fullmatch(r"[0-9]{0,5}", value) is not None)
    int18_validation = window.register(lambda value: re.fullmatch(r"[0-9]{0,18}", value) is not None)
    name_validation = window.register(lambda value: re.fullmatch(r"[a-zA-Z ]*", value) is not None)
    text_validation = window.register(lambda value: re.fullmatch(r"[a-zA-Z0-9\s\(\)_-]*", value) is not None)

    # Container frame
    form_frame = ttk.LabelFrame(window, text="Enter Cheque Book Details", padding=(20, 10), style="Custom.TLabelframe")
    form_frame.pack(padx=20, pady=10, fill="both", expand=True)

    label = ttk.Label(form_frame, text="Cheque Book Name")
    label.grid(row=1, column=0, padx=10, pady=8, sticky="w")
    entry = ttk.Entry(form_frame, textvariable=cheque_name_var, width=40, validate="key", validatecommand=(text_validation, "%P"))
    entry.grid(row=1, column=1, padx=10, pady=8)

    bank_List = list(text.Banks)

    label = ttk.Label(form_frame, text="Bank Name")
    label.grid(row=2, column=0, padx=10, pady=8, sticky="w")
    bankName_Entry = ttk.Combobox(form_frame, textvariable=bank_name_var, values=bank_List, state="readonly", width=37)
    bankName_Entry.grid(row=2, column=1, padx=10, pady=8)

    label = ttk.Label(form_frame, text="Account Holder Name")
    label.grid(row=3, column=0, padx=10, pady=8, sticky="w")
    entry = ttk.Entry(form_frame, textvariable=acc_holder_var, width=40, validate="key", validatecommand=(name_validation, "%P"))
    entry.grid(row=3, column=1, padx=10, pady=8)

    label = ttk.Label(form_frame, text="Account Number")
    label.grid(row=4, column=0, padx=10, pady=8, sticky="w")
    entry = ttk.Entry(form_frame, textvariable=acc_no_var, width=40, validate="key", validatecommand=(int18_validation, "%P"))
    entry.grid(row=4, column=1, padx=10, pady=8)

    label = ttk.Label(form_frame, text="Starting Cheque No.")
    label.grid(row=5, column=0, padx=10, pady=8, sticky="w")
    entry = ttk.Entry(form_frame, textvariable=start_cheque_var, width=40, validate="key", validatecommand=(int5_validation, "%P"))
    entry.grid(row=5, column=1, padx=10, pady=8)

    label = ttk.Label(form_frame, text="Current Cheque No.")
    label.grid(row=6, column=0, padx=10, pady=8, sticky="w")
    entry = ttk.Entry(form_frame, textvariable=current_cheque_var, width=40, validate="key", validatecommand=(int5_validation, "%P"))
    entry.grid(row=6, column=1, padx=10, pady=8)

    label = ttk.Label(form_frame, text="Total Cheques")
    label.grid(row=7, column=0, padx=10, pady=8, sticky="w")
    entry = ttk.Entry(form_frame, textvariable=total_cheques_var, width=40, validate="key", validatecommand=(int5_validation, "%P"))
    entry.grid(row=7, column=1, padx=10, pady=8)

    # Date picker
    ttk.Label(form_frame, text="Issued Date").grid(row=8, column=0, padx=10, pady=8, sticky="w")
    date_entry = DateEntry(form_frame, width=37, background='darkblue', foreground='white', borderwidth=2, date_pattern='dd/mm/yyyy', textvariable=issued_date_var)
    date_entry.grid(row=8, column=1, padx=10, pady=8)

    # Submit button
    submit_btn = ttk.Button(window, text="Add Cheque Book", width=30 , cursor="hand2", command=submit_form)
    submit_btn.pack(pady=20)

    if ChequeBook_id:
        Load_ChequeBook(ChequeBook_id)
        submit_btn.configure(text="Update Cheque Book")

    window.resizable(False, False)
    window.bind("<Escape>", lambda key: window.destroy())
    window.mainloop()


if __name__ == "__main__":
    addChequeBook_ui()