import sys
import os
from pathlib import Path

if getattr(sys, 'frozen', False):  # Running as a PyInstaller EXE
    root_path = Path(sys.executable).parent
else:  # Running as a Python script
    root_path = Path(__file__).parent.parent
sys.path.append(str(root_path))

from utilities.path_utils import *
from services.invoice_service import (
    InvoiceService, InvoiceError, InvoiceForm, ItemInput, SALES_CONFIG, calc_item,
)
import tkinter as tk
from tkinter import ttk, Canvas, Entry, Text, Button, PhotoImage, messagebox, Scrollbar, filedialog, END
from tkcalendar import DateEntry
from services.autocomplete import AutoComplete


FONT_LABEL = ("VarelaRound Regular", 12 * -1)
FONT_VALUE = ("VarelaRound Regular", 14 * -1)
FONT_BOLD = ("Poppins SemiBold", 14 * -1)

# key, label, y, font   (x: label=735, value=855)
SUMMARY_ROWS = [
    ("taxable", "Taxable Total", 548, FONT_BOLD),
    ("cgst", "CGST", 574, FONT_VALUE),
    ("sgst", "SGST", 596, FONT_VALUE),
    ("igst", "IGST", 618, FONT_VALUE),
    ("sub_total", "Sub Total", 640, FONT_BOLD),
    ("round_off", "Round Off", 665, FONT_VALUE),
    ("grand_total", "Grand Total", 685, FONT_BOLD),
]


def _entry(window, x, y, w, h=25, **opts):
    """Entry with the app's default look, placed at x/y."""
    cfg = dict(bd=1, bg="#FFFFFF", fg="#000716", cursor="xterm", font=FONT_VALUE, highlightthickness=0)
    cfg.update(opts)
    e = Entry(window, **cfg)
    e.place(x=x, y=y, width=w, height=h)
    return e


def new_invoice_ui(parent=None):

    config = SALES_CONFIG
    service = InvoiceService(config)

    ASSETS_PATH = Path(generate_path(root_path, "UI", "assets", "frame10"))

    def relative_to_assets(path: str) -> Path:
        return ASSETS_PATH / Path(path)

    edit_mode = {'item_id': None}  # row being edited, if any

    # =============================================================================
    #  UI helpers (display only - no business logic here)
    # =============================================================================
    def show_error(err: InvoiceError):
        show = {"error": messagebox.showerror, "info": messagebox.showinfo,
                "warning": messagebox.showwarning}[err.level]
        show(err.title, err.message, parent=window)
        if err.clear_field == "invoice_no":
            invoice_no.delete(0, END)

    def current():
        return invoice_no.get().strip(), customer_name.get()

    def set_readonly(entry, text):
        entry.config(state='normal')
        entry.delete(0, END)
        entry.insert(0, text)
        entry.config(state='readonly')

    def render_summary(s=None):
        values = {k: "0.0" for k, *_ in SUMMARY_ROWS}
        if s is not None:
            values = {"taxable": f"{s.taxable}", "cgst": f"{s.cgst}", "sgst": f"{s.sgst}",
                      "igst": f"{s.igst}", "sub_total": f"{s.sub_total:.2f}",
                      "round_off": f"{s.round_off}", "grand_total": f"{s.grand_total}"}
        for key, text in values.items():
            canvas.itemconfig(summary_txt[key], text=text)

    def refresh_summary():
        render_summary(service.summary(customer_name.get()))

    def refresh_treeview():
        for row in treeview.get_children():
            treeview.delete(row)
        for idx, r in enumerate(service.draft_items(), start=1):
            label = f"{r.item_name} ({r.item_code})" if r.item_code else r.item_name
            gst_txt = f"{r.gst_rate}% ({r.taxes})" if r.taxes != 0 else "0"
            disc_txt = f"{r.discount_percent}% (₹{r.discount_amount})" if r.discount_percent > 0 else "0"
            treeview.insert("", "end", iid=r.row_id,
                            values=(idx, label, f"{r.qty} [{r.unit}]", r.price, gst_txt, disc_txt, r.total, "X"))

    def clear_item_fields():
        item_code.delete(0, END)
        item_name.delete(0, END)
        for w in (qty, price, gst, discount):
            w.delete(0, END)
            w.insert(0, "0")
        edit_mode['item_id'] = None
        item_code.focus_set()

    # =============================================================================
    #  Handlers
    # =============================================================================
    def calculate_total(*args):
        try:
            a = calc_item(float(qty.get() or 0), float(price.get() or 0),
                          float(gst.get() or 0), float(discount.get() or 0))
            set_readonly(item_total, f"{a.total:.2f}")
        except ValueError:
            set_readonly(item_total, "Error")

    def update_payment(*args):
        try:
            set_readonly(amount_remain, f"{service.remaining(amount_paid.get()):.2f}")
        except ValueError:
            set_readonly(amount_remain, "")

    def add_item():
        inv, name = current()
        item = ItemInput(item_code.get(), item_name.get(), entry_9.get(),
                         qty.get(), price.get(), gst.get(), discount.get())
        try:
            action = service.save_item(inv, name, date_entry.get(), item, edit_mode['item_id'])
        except InvoiceError as err:
            show_error(err)
            return
        except Exception as e:
            messagebox.showerror("Error", str(e), parent=window)
            return

        if action == "updated":
            messagebox.showinfo("Item Updated", "Item has been updated successfully.", parent=window)

        refresh_summary()
        if not amount_paid.get():
            amount_paid.insert(0, "0")
        update_payment()
        refresh_treeview()
        customer_name.config(state='disabled')
        clear_item_fields()

    def delete_item(event=None):
        selected = treeview.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select an item to delete.", parent=window)
            return
        if not messagebox.askyesno("Delete Item", "Are you sure you want to delete this item?", parent=window):
            return
        try:
            service.delete_item(selected[0])
            if edit_mode['item_id'] == selected[0]:
                edit_mode['item_id'] = None
            refresh_treeview()
            messagebox.showinfo("Item Deleted", "Item has been deleted successfully.", parent=window)
            refresh_summary()
            update_payment()
        except Exception as e:
            messagebox.showerror("Error", str(e), parent=window)

    def on_treeview_double_click(event):
        row_id = treeview.identify_row(event.y)
        col_id = treeview.identify_column(event.x)
        if not row_id or col_id == "#8":  # ignore Delete column
            return
        r = service.get_draft_item(row_id)
        if not r:
            return
        for w, val in ((item_code, r.item_code), (item_name, r.item_name), (qty, r.qty),
                       (price, r.price), (gst, r.gst_rate), (discount, r.discount_percent)):
            w.delete(0, END)
            w.insert(0, val)
        entry_9.set(r.unit)
        calculate_total()
        edit_mode['item_id'] = row_id

    def on_treeview_button_click(event):
        if treeview.identify_region(event.x, event.y) == "cell" and treeview.identify_column(event.x) == "#8":
            treeview.selection_set(treeview.identify_row(event.y))
            delete_item()

    def reset_form():
        for row in treeview.get_children():
            treeview.delete(row)
        render_summary(None)
        customer_name.config(state='readonly')
        invoice_no.delete(0, END)
        customer_name.set('')
        payment_type.delete(0, END)
        date_entry.delete(0, END)
        contect_no.delete(0, END)
        gst_no.delete(0, END)
        amount_paid.delete(0, END)
        set_readonly(amount_remain, "")
        remark.delete(1.0, END)
        Reference_no.delete(0, END)
        edit_mode['item_id'] = None

    def save_invoice():
        """Returns True when invoice is saved or already exists, False on failure."""
        form = InvoiceForm(invoice_no.get(), customer_name.get(), invoice_type.get(),
                           payment_type.get(), date_entry.get(), amount_paid.get(),
                           remark.get("1.0", END), Reference_no.get())
        try:
            result = service.save_invoice(form)
        except InvoiceError as err:
            show_error(err)
            return False
        except Exception as e:
            messagebox.showerror("Save Error", str(e), parent=window)
            return False

        messagebox.showinfo(result.title, result.message, parent=window)
        if result.status == "saved":
            reset_form()
        return result.ok

    def export_invoice():
        inv, name = current()
        try:
            target = service.prepare_export(inv, name, date_entry.get())
        except InvoiceError as err:
            show_error(err)
            return

        file_path = filedialog.asksaveasfilename(
            title="Save PDF At",
            initialfile=target.filename,
            defaultextension=".pdf",
            filetypes=[("PDF Files", "*.pdf")],
            parent=window
        )
        if not file_path:
            return
        if not save_invoice():
            return

        service.generate_pdf(target.client_id, target.invoice_no, file_path)
        if not os.path.exists(file_path):
            messagebox.showerror("Export error", "Failed to Generate PDF", parent=window)
            return
        if messagebox.askquestion("Invoice Saved", f"Invoice saved at {file_path} \nDo you want to open the PDF?",
                                  parent=window) == 'yes':
            os.startfile(file_path)

    def on_client_selected(event=None):
        name = customer_name.get()
        if not name:
            return
        try:
            p = service.client_profile(name)
        except InvoiceError as err:
            show_error(err)
            return
        except Exception as e:
            messagebox.showinfo("Error", f"Error fetching client Data: {e}", parent=window)
            return
        invoice_no.delete(0, END)
        gst_no.delete(0, END)
        contect_no.delete(0, END)
        contect_no.insert(0, p.contact_display)
        gst_no.insert(0, p.gst_no)
        if p.next_invoice_no is not None:
            invoice_no.insert(0, p.next_invoice_no)

    def on_invoice_no_change(event):
        inv, name = current()
        if service.invoice_exists(inv, name):
            messagebox.showinfo("Invoice Exists", "Invoice number already exists.", parent=window)
            invoice_no.delete(0, END)

    def gst_enable(event):
        if invoice_type.get() == config.gst_invoice_type:
            gst_no.config(state="normal")
            gst.config(state="normal")
        else:
            gst_no.config(state="disabled")
            gst.delete(0, END)
            gst.insert(0, "0")
            gst.config(state="disabled")

    def _apply_master(m, skip):
        """Fill the other item fields from a lookup result."""
        if not m:
            return
        if skip != "code" and m.item_code:
            item_code.delete(0, END)
            item_code.insert(0, m.item_code)
        if skip != "name" and m.item_name:
            item_name.delete(0, END)
            item_name.insert(0, m.item_name)
        if m.price is not None:
            price.delete(0, END)
            price.insert(0, m.price)
        calculate_total()

    def on_item_code_select(value):
        _apply_master(service.item_by_code(value), skip="code")

    def on_item_name_select(value):
        _apply_master(service.item_by_name(value), skip="name")

    def on_close(*args):
        if messagebox.askyesno("Exit Confirmation", "Are you sure you want to Close?", parent=window):
            service.discard_draft()
            Top_Close(window, parent)

    # =============================================================================
    #  UI Creation
    # =============================================================================
    window = tk.Toplevel(parent)
    center_window(window, 1280, 720)
    window.iconbitmap(generate_path("UI", "assets", "BillMates.ico"))
    window.title(config.window_title)
    window.resizable(False, False)
    window.configure(bg="#E7EBFF")
    window.transient(parent)
    window.grab_set()
    window.focus()

    canvas = Canvas(window, bg="#E7EBFF", height=720, width=1280, bd=0, highlightthickness=0, relief="ridge")
    canvas.place(x=0, y=0)

    float_validation = window.register(lambda value: value == "" or value.replace(".", "", 1).isdigit())

    # ---- Treeview ---------------------------------------------------------------
    treeview_frame_x, treeview_frame_y = 20, 168
    treeview_width, treeview_height = 1230, 368

    scrollbar = Scrollbar(window, orient="vertical")
    scrollbar.place(x=treeview_frame_x + treeview_width - 20, y=treeview_frame_y, height=treeview_height)

    columns = ("Sr No.", "Item Name", "Quantity", "Price", "Taxes", "Discount %", "Subtotal", "Delete")
    treeview = ttk.Treeview(window, columns=columns, show="headings", yscrollcommand=scrollbar.set,
                            height=16, style="Treeview.Heading")
    treeview.place(x=treeview_frame_x, y=treeview_frame_y, width=treeview_width, height=treeview_height)
    scrollbar.config(command=treeview.yview)

    style = ttk.Style(window)
    style.configure("Treeview.Heading", font=("Arial", 10, "bold"), background="#f0f0f0")
    style.configure("Treeview", font=("Arial", 9))

    columns_config = [("Sr No.", 74), ("Item Name", 354), ("Quantity", 155), ("Price", 150),
                      ("Taxes", 127), ("Discount %", 140), ("Subtotal", 160), ("Delete", 74)]
    for col_name, col_width in columns_config:
        treeview.heading(col_name, text=col_name, anchor="center")
        treeview.column(col_name, anchor="center", width=col_width, stretch=False)

    treeview.bind("<Delete>", delete_item)
    treeview.bind("<Double-1>", on_treeview_double_click)
    treeview.bind("<Button-1>", on_treeview_button_click)

    # ---- Static labels ----------------------------------------------------------
    cl = config.client_label
    for x, y, text in [
        (27, 28, f"{cl} Name"), (262, 28, f"{cl} No."), (467, 28, "Invoice No."),
        (662, 28, "Invoice Date"), (877, 28, "Invoice Type"), (1022, 28, f"{cl} GST No."),
        (27, 102, "HSN Code"), (166, 102, "Item Name"), (445, 102, "Quantity "), (574, 102, "Unit"),
        (683, 102, config.price_label), (822, 102, "Discount (%)"), (951, 102, "GST (%)"),
        (1080, 102, "Item Total"),
        (28, 552, "Reference No. "), (28, 607, "Remarks"),
        (303, 556, "Payment Type"), (303, 605, "Payment Amount"), (303, 655, "Remaining Amount "),
    ]:
        canvas.create_text(x, y, anchor="nw", text=text, fill="#000000", font=FONT_LABEL)

    summary_txt = {}
    for key, label, y, font in SUMMARY_ROWS:
        canvas.create_text(735, y, anchor="nw", text=label, fill="#000000", font=font)
        summary_txt[key] = canvas.create_text(855, y, anchor="nw", text="0.0", fill="#000000", font=font)

    # ---- Header fields ----------------------------------------------------------
    try:
        client_names = service.client_names()
    except Exception as e:
        messagebox.showinfo("Error", f"Error fetching client names: {e}", parent=window)
        client_names = []
 
    customer_name = ttk.Combobox(window, values=client_names, state="readonly", font=("VarelaRound Regular", 13 * -1))
    customer_name.place(x=27.0, y=47.0, width=210.0, height=25.0)
    customer_name.bind("<<ComboboxSelected>>", on_client_selected)
 
    contect_no = _entry(window, 262, 47, 180)
    invoice_no = _entry(window, 467, 47, 170)
    invoice_no.bind("<KeyRelease>", on_invoice_no_change)
 
    date_entry = DateEntry(window, width=12, background="#000000", foreground="white", borderwidth=2,
                           date_pattern='dd/mm/yyyy', font=("VarelaRound Regular", 13 * -1))
    date_entry.place(x=662.0, y=47.0, width=190.0, height=25.0)
 
    invoice_type = ttk.Combobox(window, values=list(config.invoice_types), state="readonly", font=FONT_VALUE)
    invoice_type.set(config.default_invoice_type)
    invoice_type.place(x=877.0, y=47.0, width=120.0, height=25.0)
    invoice_type.bind("<<ComboboxSelected>>", gst_enable)
 
    gst_no = _entry(window, 1022, 47, 170)
 
    # ---- Item entry row ---------------------------------------------------------
    item_code = _entry(window, 27, 122, 120)
    AutoComplete(item_code, service.item_codes, on_select=on_item_code_select)
 
    item_name = _entry(window, 166, 122, 260)
    AutoComplete(item_name, service.item_names, on_select=on_item_name_select)
 
    qty = tk.Spinbox(window, from_=0.0, to=100.0, increment=1, format="%.2f", width=30,
                     validate="key", validatecommand=(float_validation, "%P"), font=FONT_VALUE)
    qty.place(x=445.0, y=122.0, width=110.0, height=25.0)
 
    unites = ["QTY", "Meter", "Pieces", "Inch", "CM", "Roll"]
    entry_9 = ttk.Combobox(window, values=unites, state="readonly", font=FONT_VALUE)
    entry_9.current(0)
    entry_9.place(x=574.0, y=122.0, width=90.0, height=25.0)
 
    num = dict(highlightthickness=1, validate="key", validatecommand=(float_validation, "%P"))
    price = _entry(window, 683, 122, 120, **num)
    discount = _entry(window, 822, 122, 110, **num)
    gst = _entry(window, 951, 122, 110, **num)
    for w in (qty, price, gst, discount):
        w.bind("<FocusOut>", calculate_total)
        w.bind("<KeyRelease>", calculate_total)
 
    item_total = _entry(window, 1080, 122, 110, fg="#000000", cursor="", highlightthickness=1, state="readonly")
 
    # ---- Payment / remarks ------------------------------------------------------
    Reference_no = _entry(window, 28, 574, 240)
 
    paymentMode = ["Cash", "UPI", "Net Banking", "Check", "Card"]
    payment_type = ttk.Combobox(window, values=paymentMode, state="readonly")
    payment_type.current(0)
    payment_type.place(x=303.0, y=574.0, width=160.0, height=25.0)
 
    amount_paid = _entry(window, 303, 623, 160, validate="key", validatecommand=(float_validation, "%P"))
    amount_paid.bind("<FocusOut>", update_payment)
    amount_paid.bind("<KeyRelease>", update_payment)
 
    amount_remain = _entry(window, 303, 672, 160, cursor="", state="readonly")

    remark = Text(window, bd=1, bg="#FFFFFF", fg="#000716", cursor="xterm", font=FONT_VALUE, highlightthickness=0)
    remark.place(x=28.0, y=627.0, width=240.0, height=70.0)

    # ---- Buttons ----------------------------------------------------------------
    def make_button(img_name, command, x, y, w, h):
        img = PhotoImage(file=relative_to_assets(img_name))
        btn = Button(window, image=img, borderwidth=0, highlightthickness=0, cursor="hand2",
                     command=command, relief="flat")
        btn.image = img  # keep a reference
        btn.place(x=x, y=y, width=w, height=h)
        return btn

    button_add_item = make_button("button_2.png", add_item, 1209, 109, 40, 40)
    button_4 = make_button("button_4.png", save_invoice, 1072, 568, 170, 50)
    button_3 = make_button("button_3.png", export_invoice, 1072, 639, 170, 50)

    window.bind('<Control-s>', lambda event: save_invoice())
    window.bind('<Control-p>', lambda event: export_invoice())
    window.bind('<Shift-Return>', lambda event: add_item())

    window.resizable(False, False)
    window.protocol("WM_DELETE_WINDOW", on_close)
    window.bind("<Escape>", on_close)
    window.mainloop()


if __name__ == "__main__":
    new_invoice_ui()