import sys
from pathlib import Path

if getattr(sys, 'frozen', False):  # Running as a PyInstaller EXE
    root_path = Path(sys.executable).parent
else:  # Running as a Python script
    root_path = Path(__file__).parent.parent
sys.path.append(str(root_path))
 
from utilities.path_utils import *
from tkinter import Canvas, PhotoImage, Button, messagebox
from tkinter import BooleanVar, StringVar
from tkinter import ttk, filedialog
from datetime import datetime
from tkcalendar import DateEntry
import re
from num2words import num2words
from utilities.cheque import export_Cheque
from utilities import text


def PrintOnCheque(Cheque_id = None, parent = None):
    ASSETS_PATH = Path(generate_path(root_path, "UI", "assets", "frame4"))

    def relative_to_assets(path: str) -> Path:
        return ASSETS_PATH / Path(path)


    window = tk.Toplevel(parent)
    window.focus()
    window.transient(parent)
    window.grab_set() 
    center_window(window, 854, 480)
    window.iconbitmap(generate_path("UI", "assets", "BillMates.ico"))
    window.title("Print On Cheque")
    window.configure(bg = "#E7EBFF")


    def save_Cheque():
        round_off(None)
        
        data_saveCheque = bool(saveCheque.get())
        data_Cheque_book = str(Cheque_book.get())
        data_Cheque_no = str(Cheque_no.get())
        data_Cheque_date = str(Cheque_date.get())
        data_Payee_name = str(Payee_name.get())
        data_Amount = Amount.get()
        data_Cheque_type = str(Cheque_type.get())

        if data_saveCheque:
            if not data_Cheque_book:
                messagebox.showwarning("Missing Data", "Please enter Cheque Book details.", parent=window)
                return
            elif not data_Cheque_no:
                messagebox.showwarning("Missing Data", "Please enter Cheque Number.", parent=window)
                return
            elif not data_Cheque_date:
                messagebox.showwarning("Missing Data", "Please enter Cheque Date.", parent=window)
                return
            elif not data_Payee_name:
                messagebox.showwarning("Missing Data", "Please enter Payee Name.", parent=window)
                return
            elif not data_Amount:
                messagebox.showwarning("Missing Data", "Please enter Amount.", parent=window)
                return
            else:
                try:
                    data_Amount = float(data_Amount)
                except ValueError:
                    messagebox.showwarning("Invalid Amount", "Amount must be a valid number.", parent=window)
        

        filename = f"Cheque to {data_Payee_name}.pdf" 

        file_path = filedialog.asksaveasfilename(
            title="Save PDF At",
            initialfile=filename,
            defaultextension=".pdf",  # Set the default extension
            filetypes=[("PDF Files", "*.pdf")],
            parent=window
        )
        if file_path:
            if data_saveCheque is True:
                data_id = fetch_data(f"SELECT id FROM ChequeBook WHERE book_name = '{data_Cheque_book}'", db='Cheque.db')[0][0]

                if Cheque_id:
                    
                    query = f"""
                        UPDATE Cheques SET
                            cheque_book_id = {data_id},
                            Cheque_No = '{data_Cheque_no}',
                            Cheque_Date = '{data_Cheque_date}',
                            Cheque_Type = '{data_Cheque_type}',
                            Payee_name = '{data_Payee_name}',
                            Amount = {data_Amount}
                        WHERE id = {Cheque_id}
                    """

                    run_query(query, db='Cheque.db')

                else:
                    query =f"""
                    INSERT INTO Cheques 
                        (cheque_book_id, Cheque_No, Cheque_Date, Cheque_Type, Payee_name, Amount)
                    VALUES
                        ({data_id}, '{data_Cheque_no}', '{data_Cheque_date}', '{data_Cheque_type}', '{data_Payee_name}', {data_Amount})
                    """

                    run_query(query, db='Cheque.db')

                    data_Cheque_no = int(data_Cheque_no) + 1

                    run_query(f"UPDATE ChequeBook SET Current_ChequeNo = {data_Cheque_no} WHERE id = {data_id}", db='Cheque.db')
                    

            export_Cheque(file_path, data_Payee_name, data_Amount, str(Date_formate.get()),  data_Cheque_date, data_Cheque_type, bool(isBearer.get()))
            
            if not os.path.exists(file_path):
                messagebox.showerror("Export error", "Failed to Generate PDF", parent=window)
                return
            else:
                clearData()
                if data_saveCheque is True:
                    messagebox.showinfo("Success", f"Cheque saved & Exported Successfully!", parent=window)
                elif data_saveCheque is False:
                    messagebox.showinfo("Success", f"Cheque Exported Successfully!", parent=window)
                os.startfile(file_path)
                if Cheque_id:
                    window.destroy()

    def Load_Cheque(id):

        filter = f"SELECT * FROM Cheques WHERE id = {id}"

        Data = fetch_data(filter, db="Cheque.db")[0]
        Cheque_book_Name = fetch_data(f"SELECT book_name FROM ChequeBook WHERE id = '{Data[1]}'", db='Cheque.db')[0][0]

        Cheque_book.set(Cheque_book_Name)
        onCheckbook_Select(None)
        Cheque_no.set(Data[2])
        entry_6.current(0)
        entry_7.set_date(datetime.strptime(Data[3], "%d/%m/%Y"))
        Cheque_type.set(Data[4])
        Payee_name.set(Data[5])
        Amount.set(Data[6])

        isBearer.set(False)
        saveCheque.set(True)
        Checkbox_1.config(state="disabled")


    def clearData():
        Cheque_book.set("")
        Bank_name.set("")
        Holder_name.set("")
        Account_no.set("")
        Cheque_no.set("")
        Date_formate.set("")
        entry_6.current(0)
        Cheque_date.set("")
        entry_7.set_date(datetime.now())
        Payee_name.set("")
        Amount.set("")

        isDate.set(True)
        Cheque_type.set("False")
        isBearer.set(False)
        saveCheque.set(True)

    def changeAmount(*args):
        amount_in_figures = Amount.get()

        if Amount.get() == "":  
            entry_9.delete(0, "end")  # Keep it empty if input is empty
            canvas.itemconfig(amount_in_Words, text="")
        else:
            if amount_in_figures:
                Words = num2words(amount_in_figures, lang="en_IN")  # Convert to words in Indian format
                Words = Words.replace(" and", "").title()  # Format properly
                Words = f"{Words} Rs. Only"
            else:
                Words = "Invalid Amount"  # Handle invalid input
            
            canvas.itemconfig(amount_in_Words, text=Words)

    def isDateState(*args):
        if isDate.get() is False:
            entry_6.config(state="disabled")
            entry_6.set("")
            entry_7.delete(0, 'end')
            entry_7.config(state="disabled")
            
        elif isDate.get() is True:
            entry_6.config(state="normal")
            entry_6.current(0)
            entry_7.config(state="normal")
            entry_7.set_date(datetime.now())

    def isSaveData(*args):
        if saveCheque.get() is False:
            entry_1.config(state="disabled")
            entry_1.set("")
            entry_2.config(state="disabled")
            entry_2.set("")
            entry_3.config(state="disabled")
            Holder_name.set("")
            entry_4.config(state="disabled")
            Account_no.set("")
            entry_5.config(state="disabled")
            Cheque_no.set("")

        elif isDate.get() is True:
            entry_1.config(state="normal")
            entry_2.config(state="normal")
            entry_3.config(state="normal")
            entry_4.config(state="normal")
            entry_5.config(state="normal")

    def isBearerCheck(*args):
        if isBearer.get() is False:
            radioBotton_3.config(state="normal")
        elif isBearer.get() is True:
            if Cheque_type.get() == "Cross":
                Cheque_type.set("Account")
            radioBotton_3.config(state="disabled")

    def onCheckbook_Select(event):
        Selected_Book = Cheque_book.get()
        if Selected_Book:
            Bank_name.set("")
            Holder_name.set("")
            Account_no.set("")
            Cheque_no.set("")

            Cheque_book_data = fetch_data(f"SELECT * FROM ChequeBook WHERE book_name = '{Selected_Book}'", db="Cheque.db")[0]
            
            if Cheque_book_data[6] >= (Cheque_book_data[5] + Cheque_book_data[7]):
                response = messagebox.askyesno(
                    "Warning!",
                    "The Cheque Book is out of cheques.\nDo you still want to create a cheque?",
                    icon="warning",
                    parent=window
                )
                if not response:
                    Cheque_book.set("")
                    return
            
            if Cheque_book_data:
                Bank_name.set(Cheque_book_data[2])
                Holder_name.set(Cheque_book_data[3])
                Account_no.set(Cheque_book_data[4])
                Cheque_no.set(Cheque_book_data[6])

 
    Cheque_book = StringVar()
    Bank_name = StringVar()
    Holder_name = StringVar()
    Account_no = StringVar()
    Cheque_no = StringVar()
    Date_formate = StringVar()
    Cheque_date = StringVar()
    Payee_name = StringVar()
    Amount = StringVar()

    isDate = BooleanVar(value=True)
    Cheque_type = StringVar(value="False")
    isBearer = BooleanVar(value=False)
    saveCheque = BooleanVar(value=True)


    canvas = Canvas(
        window,
        bg = "#E7EBFF",
        height = 480,
        width = 854,
        bd = 0,
        highlightthickness = 0,
        relief = "ridge"
    )
    canvas.place(x = 0, y = 0)

    canvas.create_rectangle(
        14.0,
        137.0,
        839.0,
        397.0,
        fill="",
        outline="#000000")

    canvas.create_rectangle(
        14.0,
        18.0,
        839.0,
        118.0,
        fill="",
        outline="#000000")


    Cheque_books = [row[0] for row in fetch_data("SELECT book_name FROM ChequeBook", db="Cheque.db")]
    entry_1 = ttk.Combobox(
        window,
        textvariable=Cheque_book,  # Holds selected value
        values=Cheque_books,  # Dropdown options
        state="readonly"  # Allows typing
    )
    entry_1.place(
        x=133.0,
        y=40.0,
        width=300.0,
        height=22.0
    )
    entry_1.bind("<<ComboboxSelected>>", onCheckbook_Select)
    

    entry_2 = ttk.Combobox(
        window,
        textvariable=Bank_name,  # Holds selected value
        values= text.Banks,  # Dropdown options
        state="readonly"  # Allows typing
    )
    entry_2.place(
        x=569.0,
        y=40.0,
        width=250.0,
        height=22.0
    )

    entry_3 = ttk.Entry(window, textvariable=Holder_name)
    entry_3.place(
        x=133.0,
        y=75.0,
        width=300.0,
        height=22.0
    )


    int_validation = window.register(lambda v: re.fullmatch(r"\d{0,18}", v) is not None)
    entry_4 = ttk.Entry(window, textvariable=Account_no, validate="key", validatecommand=(int_validation, "%P"))
    entry_4.place(
        x=569.0,
        y=75.0,
        width=250.0,
        height=22.0
    )

    int_validation = window.register(lambda v: re.fullmatch(r"\d{0,6}", v) is not None)
    entry_5 = ttk.Entry(window, textvariable=Cheque_no, validate="key", validatecommand=(int_validation, "%P"))
    entry_5.place(
        x=133.0,
        y=162.0,
        width=180.0,
        height=22.0
    )

    Formates = ["D D M M Y Y Y Y", "DD-MM-YYYY", "DD/MM/YYYY"]
    entry_6 = ttk.Combobox(
        window,
        textvariable=Date_formate,  # Holds selected value
        values=Formates,  # Dropdown options
        state="readonly"  # Allows typing
    )
    entry_6.place(
        x=634.0,
        y=162.0,
        width=185.0,
        height=22.0
    )
    entry_6.current(0)

    entry_7 = DateEntry(
        window,
        textvariable=Cheque_date,  # Holds selected date
        date_pattern="dd/mm/yyyy",  # Set desired format
        background="lightblue",
        foreground="black",
        borderwidth=2
    )
    entry_7.place(
        x=634.0,
        y=202.0,
        width=185.0,
        height=22.0
    )

    wordLimit = window.register(lambda v: re.fullmatch(r".{0,55}", v) is not None)
    entry_8 = ttk.Entry(window, textvariable=Payee_name, font=('Arial', 10), validate="key", validatecommand=(wordLimit, "%P"))
    entry_8.place(
        x=133.0,
        y=247.0,
        width=501.0,
        height=25.0
    )
    data = [row[0] for row in fetch_data("SELECT DISTINCT Payee_name FROM Cheques", db="Cheque.db")]
    listbox = tk.Listbox(
        window, 
        height=5,
        bg="#F5F5F5",        # Light background
        fg="#000000",        # Dark text
        font=('Arial', 10),
        highlightthickness=1,
        selectbackground="#C5D9F1",
        bd=2,
        highlightbackground="black",
        highlightcolor="black",
        relief="flat"
    )
    SearchBox(entry_8, listbox, data)


    def round_off(event):
        try:
            rounded_value = str(round(float(entry_9.get())))
            entry_9.delete(0, "end")
            entry_9.insert(0, rounded_value) 
        except ValueError:
            entry_9.delete(0, "end")


    float_validation = window.register(lambda value: value == "" or (
        value.replace(".", "", 1).isdigit() and 
        (("." in value and len(value.split(".")[0]) <= 10 and len(value.split(".")[1]) <= 2) or 
        ("." not in value and len(value) <= 10))
    ))
    entry_9 = ttk.Entry(window, textvariable=Amount, validate="key", validatecommand=(float_validation, "%P"))
    entry_9.place(
        x=620.0,
        y=297.0,
        width=199.0,
        height=23.0
    )
    entry_9.bind("<FocusOut>", round_off)
    entry_9.bind("<Return>", round_off)
    Amount.trace_add("write", changeAmount)



    canvas.create_text(
        40.0,
        251.0,
        anchor="nw",
        text="Payee Name",
        fill="#000000",
        font=("VarelaRound Regular", 14 * -1)
    )

    canvas.create_text(
        542.0,
        165.0,
        anchor="nw",
        text="Date Format",
        fill="#000000",
        font=("VarelaRound Regular", 14 * -1)
    )

    Checkbox_3 = ttk.Checkbutton(window, style="TCheckbutton", text="Cheque Date", variable=isDate)
    Checkbox_3.place(x=515, y=200)
    isDate.trace_add("write", isDateState)

    canvas.create_text(
        538.0,
        205.0,
        anchor="nw",
        text="Cheque Date",
        fill="#000000",
        font=("VarelaRound Regular", 14 * -1)
    )

    canvas.create_text(
        552.0,
        301.0,
        anchor="nw",
        text="Amount",
        fill="#000000",
        font=("VarelaRound Regular", 14 * -1)
    )

    style = ttk.Style()
    style.configure("TRadiobutton", background="#E7EBFF", font=("VarelaRound Regular", 11))
    style.configure("TCheckbutton", background="#E7EBFF", font=("VarelaRound Regular", 11))

    radioBotton_1 = ttk.Radiobutton(window, style="TRadiobutton", text="None", variable=Cheque_type, value="False")
    radioBotton_1.place(x=40, y=204)

    radioBotton_2 = ttk.Radiobutton(window, style="TRadiobutton", text="Account Payee Only", variable=Cheque_type, value="Account")
    radioBotton_2.place(x=121, y=204)

    radioBotton_3 = ttk.Radiobutton(window, style="TRadiobutton", text="Crossed Pay", variable=Cheque_type, value="Cross")
    radioBotton_3.place(x=299, y=204)

    Checkbox_1 = ttk.Checkbutton(window, style="TCheckbutton", text="Save cheque details", variable=saveCheque)
    Checkbox_1.place(x=40, y=301)
    saveCheque.trace_add("write", isSaveData)

    Checkbox_2 = ttk.Checkbutton(window, style="TCheckbutton", text="Or bearer", variable=isBearer)
    Checkbox_2.place(x=695, y=251)
    isBearer.trace_add("write", isBearerCheck)



    canvas.create_text(
        40.0,
        164.0,
        anchor="nw",
        text="Cheque No.",
        fill="#000000",
        font=("VarelaRound Regular", 14 * -1)
    )

    canvas.create_text(
        474.0,
        77.0,
        anchor="nw",
        text="Account no.",
        fill="#000000",
        font=("VarelaRound Regular", 14 * -1)
    )

    canvas.create_text(
        477.0,
        42.0,
        anchor="nw",
        text="Bank Name",
        fill="#000000",
        font=("VarelaRound Regular", 14 * -1)
    )

    canvas.create_text(
        34.0,
        77.0,
        anchor="nw",
        text="Holder Name",
        fill="#000000",
        font=("VarelaRound Regular", 14 * -1)
    )

    canvas.create_text(
        34.0,
        42.0,
        anchor="nw",
        text="Cheque book ",
        fill="#000000",
        font=("VarelaRound Regular", 14 * -1)
    )

    amount_in_Words = canvas.create_text(
        40.0,
        352.0,
        anchor="nw",
        text=" ",
        fill="#000000",
        font=("VarelaRound Regular", 13 * -1)
    )

    if Cheque_id:
        button_image_1 = PhotoImage(
            file=relative_to_assets("button_2.png"))
    else:
        button_image_1 = PhotoImage(
            file=relative_to_assets("button_1.png"))
        
    button_1 = Button(
        window,
        image=button_image_1,
        borderwidth=0,
        highlightthickness=0,
        cursor="hand2",
        command=lambda: save_Cheque(),
        relief="flat"
    )
    button_1.place(
        x=480.0,
        y=416.0,
        width=165.0,
        height=35.0
    )

    button_image_3 = PhotoImage(
        file=relative_to_assets("button_3.png"))
    button_3 = Button(
        window,
        image=button_image_3,
        borderwidth=0,
        highlightthickness=0,
        cursor="hand2",
        command=lambda: clearData(),
        relief="flat"
    )
    button_3.place(
        x=674.0,
        y=416.0,
        width=165.0,
        height=35.0
    )

    if Cheque_id:
        Load_Cheque(Cheque_id)

    window.resizable(False, False)
    window.bind("<Escape>", lambda key: window.destroy())
    window.mainloop()


if __name__ == "__main__":
    PrintOnCheque()