from tkinter import messagebox
from UI.restore import Restore_ui


def new_client_ui(parent = None):
    try:
        import UI.addClient
        UI.addClient.new_client_ui(parent)
    except Exception as e:
        messagebox.showerror("Unexpected Error", f"Unexpected error: {e}")

def manage_clients(parent = None):
    try:
        import UI.Manage_clients
        UI.Manage_clients.manage_clients(parent)
    except Exception as e:
        messagebox.showerror("Unexpected Error", f"Unexpected error: {e}")

def new_purchase_ui(parent = None):
    try:
        import UI.Add_purchase
        UI.Add_purchase.new_purchase_ui(parent)
    except Exception as e:
        messagebox.showerror("Unexpected Error", f"Unexpected error: {e}")
 
def manage_invoice_ui(parent = None):
    try:
        import UI.Manage_Invoices
        UI.Manage_Invoices.manage_invoice_ui(parent)
    except Exception as e:
        messagebox.showerror("Unexpected Error", f"Unexpected error: {e}")

def customer_payment_in(parent = None):
    try:
        import UI.paymentIn
        UI.paymentIn.customer_payment_in(parent)
    except Exception as e:
        messagebox.showerror("Unexpected Error", f"Unexpected error: {e}")

def expense_payments_out(parent = None):
    try:
        import UI.paymentOut
        UI.paymentOut.expense_payments_out(parent)
    except Exception as e:
        messagebox.showerror("Unexpected Error", f"Unexpected error: {e}")

def supplier_payments_out(parent = None):
    try:
        import UI.paySup
        UI.paySup.supplier_payments_out(parent)
    except Exception as e:
        messagebox.showerror("Unexpected Error", f"Unexpected error: {e}")
  
def pay_salery_ui(parent = None):
    try:
        import UI.Salery
        UI.Salery.pay_salery_ui(parent)
    except Exception as e:
        messagebox.showerror("Unexpected Error", f"Unexpected error: {e}")

def new_adjustment_ui(parent = None):
    try:
        import UI.Add_Adjustment
        UI.Add_Adjustment.new_adjustment_ui(parent)
    except Exception as e:
        messagebox.showerror("Unexpected Error", f"Unexpected error: {e}")

def manage_payments(parent = None):
    try:
        import UI.Manage_Payments
        UI.Manage_Payments.manage_payments(parent)
    except Exception as e:
        messagebox.showerror("Unexpected Error", f"Unexpected error: {e}")

def new_invoice_ui(parent = None):
    try:
        import UI.Add_Invoice
        UI.Add_Invoice.new_invoice_ui(parent)
    except Exception as e:
        messagebox.showerror("Unexpected Error", f"Unexpected error: {e}")

def company_info(Mode, parent = None):
    try:
        import UI.add_company
        UI.add_company.add_company(Mode, parent)
    except Exception as e:
        messagebox.showerror("Unexpected Error", f"Unexpected error: {e}")

def Reports_ui(parent = None):
    try:
        import UI.Reports
        UI.Reports.Reports_ui(parent)
    except Exception as e:
        messagebox.showerror("Unexpected Error", f"Unexpected error: {e}")

def Backup_ui(parent = None):
    try:
        import UI.Backup
        UI.Backup.Backup_ui(parent)
        
    except Exception as e:
        messagebox.showerror("Unexpected Error", f"Unexpected error: {e}")   

def PrintCheque_ui(Cheque_id = None, parent = None):
    try:
        import UI.ChequePrint
        UI.ChequePrint.PrintOnCheque(Cheque_id, parent)
        
    except Exception as e:
        messagebox.showerror("Unexpected Error", f"Unexpected error: {e}")   

def addChequeBook_ui(ChequeBook_id = None, parent = None):
    try:
        import UI.AddChequeBook
        UI.AddChequeBook.addChequeBook_ui(ChequeBook_id, parent)
        
    except Exception as e:
        messagebox.showerror("Unexpected Error", f"Unexpected error: {e}")   

def Manage_chequeBook_ui(parent = None):
    try:
        import UI.Manage_chequeBook
        UI.Manage_chequeBook.Manage_chequeBook(parent)
        
    except Exception as e:
        messagebox.showerror("Unexpected Error", f"Unexpected error: {e}")  

def Manage_Cheques_ui(parent = None):
    try:
        import UI.Manage_Cheques
        UI.Manage_Cheques.Manage_Cheques_ui(parent)
        
    except Exception as e:
        messagebox.showerror("Unexpected Error", f"Unexpected error: {e}")  

def payment_getway(parent = None):
    try:
        import UI.Payment_Getway
        UI.Payment_Getway.payment_getway(parent)

    except Exception as e:
        messagebox.showerror("Unexpected Error", f"Unexpected error: {e}") 

def terms_conditions(parent = None):
    try:
        from UI.terms_conditions import TermsPopup
        TermsPopup.ask_terms(parent)

    except Exception as e:
        messagebox.showerror("Unexpected Error", f"Unexpected error: {e}") 

def add_items(parent = None, Mode = "new", Item_id = None):
    try:
        from UI.Add_Item import AddItemUI
        AddItemUI(parent, mode=Mode, Item_id=Item_id)

    except Exception as e:
        messagebox.showerror("Unexpected Error", f"Unexpected error: {e}") 