import sys
from pathlib import Path

if getattr(sys, 'frozen', False):  # Running as a PyInstaller EXE (one Dir)
    root_path = Path(sys.executable).parent
else:  # Running as a Python script
    root_path = Path(__file__).parent.parent
sys.path.append(str(root_path))
 
from utilities.path_utils import *
from tkinter import Tk, Canvas, Button, PhotoImage, ttk
from tkinter import StringVar
from PIL import Image, ImageTk
from utilities import text
import qrcode
import io
import re

def payment_getway(parent = None):

    ASSETS_PATH = Path(generate_path(root_path, "UI", "assets", "frame14"))
    def relative_to_assets(path: str) -> Path:
        return ASSETS_PATH / Path(path)
    
    window = tk.Toplevel(parent)
    window.focus()
    center_window(window, 798, 480)
    window.iconbitmap(generate_path("UI", "assets", "BillMates.ico"))
    window.transient(parent)
    window.grab_set()
    window.title("Merchant Payment Getway")
    window.configure(bg = "#E7EBFF")


    def generate_upi_qr(upi_id, Amount, name):
        try:
            if upi_id:
                upi_url = f"upi://pay?pa={upi_id}&pn={name}&am={Amount}&cu=INR"
                qr = qrcode.make(upi_url)

                img_buffer = io.BytesIO()
                qr.save(img_buffer, format="PNG")
                img_buffer.seek(0)

                resized_img = Image.open(img_buffer).resize((160, 160), Image.LANCZOS)
                qr_tk = ImageTk.PhotoImage(resized_img)

                return qr_tk
            else:
                messagebox.showerror("UPI Error", f"UPI ID Not Found", parent=window)
        except Exception as e:
            messagebox.showerror("UPI Error", f"An error occurred: {e}", parent=window)

    def on_generate():
        Amount = upi_Amount.get() or 0
        upi_id = read_ini("PROFILE", "upi")
        name = read_ini("PROFILE", "name")

        qr_img = generate_upi_qr(upi_id, Amount, name)

        canvas.image = qr_img
        canvas.itemconfig(image_1, image=qr_img)


    def edit_default_bank():
        global entry1
        global entry2
        global entry3
        global entry4

        # Hide old canvas text (assuming these are canvas text IDs)
        canvas.itemconfig(default_bankName, state='hidden')
        canvas.itemconfig(default_Acc_no, state='hidden')
        canvas.itemconfig(default_IFSC, state='hidden')
        canvas.itemconfig(default_branchName, state='hidden')

        entry1 = ttk.Combobox(window, textvariable=BankName_var, values=text.Banks, state="readonly")
        entry1.place(x=180, y=64.0, width=220.0, height=20.0)
        BankName_var.set(read_ini("PROFILE", "bank"))

        int12_validation = window.register(lambda value: re.fullmatch(r"[0-9]{0,12}", value) is not None)
        entry2 = ttk.Entry(window, textvariable=AccountNo_var, validate="key", validatecommand=(int12_validation, "%P"))
        entry2.place(x=180, y=94.0, width=220.0, height=20.0)
        AccountNo_var.set(read_ini("PROFILE", "acc_no"))

        text_validation = window.register(lambda value: re.fullmatch(r"[a-zA-Z0-9\s\(\)_-]{0,15}", value) is not None)
        entry3 = ttk.Entry(window, textvariable=IFSC_Code_var, validate="key", validatecommand=(text_validation, "%P"))
        entry3.place(x=180, y=124.0, width=220.0, height=20.0)
        IFSC_Code_var.set(read_ini("PROFILE", "ifsc"))

        name_validation = window.register(lambda value: re.fullmatch(r"[a-zA-Z ]{0,20}", value) is not None)
        entry4 = ttk.Entry(window, textvariable=BranchName_var, validate="key", validatecommand=(name_validation, "%P"))
        entry4.place(x=180, y=154.0, width=220.0, height=20.0)
        BranchName_var.set(read_ini("PROFILE", "branch"))


        button_2.place_forget()
        button_4.place(
            x=368.0,
            y=37.0,
            width=32.0,
            height=20.0
        )

    def save_default_bank():
        button_4.place_forget()
        button_2.place(x=368.0, y=37.0, width=32.0, height=20.0)

        BankName = BankName_var.get()
        AccountNo = AccountNo_var.get()
        IFSC_Code = IFSC_Code_var.get()
        BranchName = BranchName_var.get()

        write_ini("PROFILE", "bank", BankName)
        write_ini("PROFILE", "acc_no", AccountNo)
        write_ini("PROFILE", "ifsc", IFSC_Code)
        write_ini("PROFILE", "branch", BranchName)

        entry1.destroy()
        entry2.destroy()
        entry3.destroy()
        entry4.destroy()

        canvas.itemconfig(default_bankName, text=BankName, state='normal')
        canvas.itemconfig(default_Acc_no, text=AccountNo, state='normal')
        canvas.itemconfig(default_IFSC, text=IFSC_Code, state='normal')
        canvas.itemconfig(default_branchName, text=BranchName, state='normal')


    def edit_other_bank():
        global entry01
        global entry02
        global entry03
        global entry04

        # Hide old canvas text (assuming these are canvas text IDs)
        canvas.itemconfig(other_bankName, state='hidden')
        canvas.itemconfig(other_Acc_no, state='hidden')
        canvas.itemconfig(other_IFSC, state='hidden')
        canvas.itemconfig(other_branchName, state='hidden')

        entry01 = ttk.Combobox(window, textvariable=BankName_var2, values=text.Banks, state="readonly")
        entry01.place(x=180, y=234.0, width=220.0, height=20.0)
        BankName_var2.set(read_ini("PROFILE", "other_bank"))

        int12_validation = window.register(lambda value: re.fullmatch(r"[0-9]{0,12}", value) is not None)
        entry02 = ttk.Entry(window, textvariable=AccountNo_var2, validate="key", validatecommand=(int12_validation, "%P"))
        entry02.place(x=180, y=264.0, width=220.0, height=20.0)
        AccountNo_var2.set(read_ini("PROFILE", "other_acc_no"))

        text_validation = window.register(lambda value: re.fullmatch(r"[a-zA-Z0-9\s\(\)_-]{0,15}", value) is not None)
        entry03 = ttk.Entry(window, textvariable=IFSC_Code_var2, validate="key", validatecommand=(text_validation, "%P"))
        entry03.place(x=180, y=294.0, width=220.0, height=20.0)
        IFSC_Code_var2.set(read_ini("PROFILE", "other_ifsc"))

        name_validation = window.register(lambda value: re.fullmatch(r"[a-zA-Z ]{0,20}", value) is not None)
        entry04 = ttk.Entry(window, textvariable=BranchName_var2, validate="key", validatecommand=(name_validation, "%P"))
        entry04.place(x=180, y=324.0, width=220.0, height=20.0)
        BranchName_var2.set(read_ini("PROFILE", "other_branch"))


        button_3.place_forget()
        button_5.place(
            x=374.0,
            y=207.0,
            width=32.0,
            height=20.0
        )

    def save_other_bank():
        button_5.place_forget()
        button_3.place(x=374.0, y=207.0, width=32.0, height=20.0)

        BankName = BankName_var2.get()
        AccountNo = AccountNo_var2.get()
        IFSC_Code = IFSC_Code_var2.get()
        BranchName = BranchName_var2.get()

        write_ini("PROFILE", "other_bank", BankName)
        write_ini("PROFILE", "other_acc_no", AccountNo)
        write_ini("PROFILE", "other_ifsc", IFSC_Code)
        write_ini("PROFILE", "other_branch", BranchName)

        entry01.destroy()
        entry02.destroy()
        entry03.destroy()
        entry04.destroy()

        canvas.itemconfig(other_bankName, text=BankName, state='normal')
        canvas.itemconfig(other_Acc_no, text=AccountNo, state='normal')
        canvas.itemconfig(other_IFSC, text=IFSC_Code, state='normal')
        canvas.itemconfig(other_branchName, text=BranchName, state='normal')

    def edit_upi():

        global entry_2
        global button_7

        button_6.place_forget()

        entry_2 = ttk.Entry(window, textvariable=upi_id_var)
        entry_2.place(x=130, y=386.0, width=220.0, height=20.0)
        upi_id_var.set(read_ini("PROFILE", "upi"))

        button_7 = Button(
            window,
            text= "Save",
            font=("VarelaRound Regular", 12, "underline"),
            borderwidth=0,
            bg="#E7EBFF",
            highlightthickness=0,
            cursor="hand2",
            command=save_upi,
            relief="flat"
        )
        button_7.place(x=360.0, y=385.0, width=35.0, height=20.0)
        
    def save_upi():
        new_upi = entry_2.get()
        if new_upi != "" or new_upi:
            upi_pattern = r"^[a-zA-Z0-9.\-_]{2,256}@[a-zA-Z]{2,64}$"
            if not re.fullmatch(upi_pattern, new_upi):
                messagebox.showerror("Error", "Invalid UPI ID!", parent=window)
                return
        
        write_ini("PROFILE", "upi", new_upi)
        canvas.itemconfig(text_upi, text=new_upi)

        entry_2.destroy()
        button_7.destroy()
        button_6.place(x=40.0, y=387.0, width=75.0, height=20.0)
        return

    BankName_var = StringVar()
    AccountNo_var = StringVar()
    IFSC_Code_var = StringVar()
    BranchName_var = StringVar()

    BankName_var2 = StringVar()
    AccountNo_var2 = StringVar()
    IFSC_Code_var2 = StringVar()
    BranchName_var2 = StringVar()

    upi_id_var = StringVar()


    canvas = Canvas(
        window,
        bg = "#E7EBFF",
        height = 480,
        width = 798,
        bd = 0,
        highlightthickness = 0,
        relief = "ridge"
    )
    canvas.place(x = 0, y = 0)
            

    canvas.create_text(
        40.0,
        427.0,
        anchor="nw",
        text="UPI Amount",
        fill="#000000",
        font=("VarelaRound Regular", 14 * -1)
    )

    float_validation = window.register(lambda value: value == "" or (
        value.replace(".", "", 1).isdigit() and 
        (("." in value and len(value.split(".")[0]) <= 10 and len(value.split(".")[1]) <= 3) or 
        ("." not in value and len(value) <= 10))
    ))
    upi_Amount = StringVar()
    entry_1 = ttk.Entry(
        window,
        textvariable=upi_Amount,
        validate="key", 
        validatecommand=(float_validation, "%P")
    ).place(
        x=130.0,
        y=425.0,
        width=220.0,
        height=20.0
    )

    button_image_1 = PhotoImage(file=relative_to_assets("button_1.png"))
    button_1 = Button(
        window,
        image=button_image_1,
        borderwidth=0,
        bg="#E7EBFF",
        highlightthickness=0,
        cursor="hand2",
        command=on_generate,
        relief="flat"
    )
    button_1.place(
        x=360.0,
        y=427.0,
        width=62.0,
        height=17.0
    )

    upi_id = read_ini("PROFILE", "upi")
    name = read_ini("PROFILE", "name")
    image_image_1 = generate_upi_qr(upi_id, 0, name)

    image_1 = canvas.create_image(
        634.0,
        213.0,
        image=image_image_1
    )
    canvas.image = image_image_1


    button_2 = Button(
        window,
        text= "Edit",
        font=("VarelaRound Regular", 12, "underline"),
        borderwidth=0,
        bg="#E7EBFF",
        highlightthickness=0,
        cursor="hand2",
        command=edit_default_bank,
        relief="flat"
    )
    button_2.place(
        x=368.0,
        y=37.0,
        width=32.0,
        height=20.0
    )

    button_4 = Button(
        window,
        text= "Save",
        font=("VarelaRound Regular", 12, "underline"),
        borderwidth=0,
        bg="#E7EBFF",
        highlightthickness=0,
        cursor="hand2",
        command=save_default_bank,
        relief="flat"
    )

    button_3 = Button(
        window,
        text= "Edit",
        font=("VarelaRound Regular", 12, "underline"),
        borderwidth=0,
        bg="#E7EBFF",
        highlightthickness=0,
        cursor="hand2",
        command=edit_other_bank,
        relief="flat"
    )
    button_3.place(
        x=374.0,
        y=207.0,
        width=32.0,
        height=20.0
    )

    button_5 = Button(
        window,
        text= "Save",
        font=("VarelaRound Regular", 12, "underline"),
        borderwidth=0,
        bg="#E7EBFF",
        highlightthickness=0,
        cursor="hand2",
        command=save_other_bank,
        relief="flat"
    )

    canvas.create_text(
        40.0,
        37.0,
        anchor="nw",
        text="Default Bank Details (Print in Invoice)",
        fill="#000000",
        font=("VarelaRound Regular", 14 * -1)
    )

    canvas.create_text(
        70.0,
        63.0,
        anchor="nw",
        text="Bank Name",
        fill="#000000",
        font=("Poppins SemiBold", 14 * -1)
    )

    canvas.create_text(
        70.0,
        123.0,
        anchor="nw",
        text="IFSC Code",
        fill="#000000",
        font=("Poppins SemiBold", 14 * -1)
    )

    canvas.create_text(
        70.0,
        93.0,
        anchor="nw",
        text="Account No.",
        fill="#000000",
        font=("Poppins SemiBold", 14 * -1)
    )

    canvas.create_text(
        70.0,
        153.0,
        anchor="nw",
        text="Branch Name",
        fill="#000000",
        font=("Poppins SemiBold", 14 * -1)
    )

    default_bankName = canvas.create_text(
        180.0,
        65.0,
        anchor="nw",
        fill="#000000",
        font=("VarelaRound Regular", 14 * -1)
    )

    default_IFSC = canvas.create_text(
        180.0,
        125.0,
        anchor="nw",
        fill="#000000",
        font=("VarelaRound Regular", 14 * -1)
    )

    default_Acc_no = canvas.create_text(
        180.0,
        95.0,
        anchor="nw",
        fill="#000000",
        font=("VarelaRound Regular", 14 * -1)
    )

    default_branchName = canvas.create_text(
        180.0,
        155.0,
        anchor="nw",
        fill="#000000",
        font=("VarelaRound Regular", 14 * -1)
    )

    canvas.itemconfig(default_bankName  , text= read_ini("PROFILE", "bank"))
    canvas.itemconfig(default_Acc_no    , text= read_ini("PROFILE", "acc_no"))
    canvas.itemconfig(default_IFSC      , text= read_ini("PROFILE", "ifsc"))
    canvas.itemconfig(default_branchName, text= read_ini("PROFILE", "branch"))

    canvas.create_text(
        46.0,
        207.0,
        anchor="nw",
        text="Other Bank Details",
        fill="#000000",
        font=("VarelaRound Regular", 14 * -1)
    )

    canvas.create_text(
        76.0,
        233.0,
        anchor="nw",
        text="Bank Name",
        fill="#000000",
        font=("Poppins SemiBold", 14 * -1)
    )

    canvas.create_text(
        76.0,
        293.0,
        anchor="nw",
        text="IFSC Code",
        fill="#000000",
        font=("Poppins SemiBold", 14 * -1)
    )

    canvas.create_text(
        76.0,
        263.0,
        anchor="nw",
        text="Account No.",
        fill="#000000",
        font=("Poppins SemiBold", 14 * -1)
    )

    canvas.create_text(
        76.0,
        323.0,
        anchor="nw",
        text="Branch Name",
        fill="#000000",
        font=("Poppins SemiBold", 14 * -1)
    )

    other_bankName = canvas.create_text(
        186.0,
        235.0,
        anchor="nw",
        fill="#000000",
        font=("VarelaRound Regular", 14 * -1)
    )

    other_Acc_no = canvas.create_text(
        186.0,
        295.0,
        anchor="nw",
        fill="#000000",
        font=("VarelaRound Regular", 14 * -1)
    )

    other_IFSC = canvas.create_text(
        186.0,
        265.0,
        anchor="nw",
        fill="#000000",
        font=("VarelaRound Regular", 14 * -1)
    )

    other_branchName = canvas.create_text(
        186.0,
        325.0,
        anchor="nw",
        fill="#000000",
        font=("VarelaRound Regular", 14 * -1)
    )

    canvas.itemconfig(other_bankName  , text= read_ini("PROFILE", "other_bank"))
    canvas.itemconfig(other_Acc_no    , text= read_ini("PROFILE", "other_acc_no"))
    canvas.itemconfig(other_IFSC      , text= read_ini("PROFILE", "other_ifsc"))
    canvas.itemconfig(other_branchName, text= read_ini("PROFILE", "other_branch"))



    button_6 = Button(
        window,
        text= "Edit UPI ID",
        font=("VarelaRound Regular", 10, "underline"),
        borderwidth=0,
        bg="#E7EBFF",
        highlightthickness=0,
        cursor="hand2",
        command=edit_upi,
        relief="flat"
    )
    button_6.place(
        x=40.0,
        y=387.0,
        width=75.0,
        height=20.0
    )

    text_upi = canvas.create_text(
        634.0,
        108.0,
        anchor="center",
        text= read_ini("PROFILE", "upi"),
        fill="#000000",
        font=("Poppins SemiBold", 10)
    )

    canvas.create_text(
        634.0,
        310.0,
        anchor="center",
        text = read_ini("PROFILE", "name"),
        fill="#000000",
        font=("VarelaRound Regular", 10)
    )

    image_image_2 = PhotoImage(
        file=relative_to_assets("image_2.png"))
    image_2 = canvas.create_image(
        632.0000305175781,
        247.0,
        image=image_image_2
    )

    image_image_3 = PhotoImage(
        file=relative_to_assets("image_3.png"))
    image_3 = canvas.create_image(
        469.99997993647276,
        239.0,
        image=image_image_3
    )

    window.resizable(False, False)
    window.bind("<Escape>", lambda key: window.destroy())
    window.mainloop()


if __name__ == "__main__":
    payment_getway(None)