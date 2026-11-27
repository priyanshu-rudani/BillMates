from tkinter import messagebox
from UI.restore import Restore_ui
from utilities.path_utils import _show_error


def new_client_ui(parent = None):
    try:
        import UI.addClient
        UI.addClient.new_client_ui(parent)
    except Exception as e:
        _show_error("Interface Error", "Failed to open Create/Edit Party window. Please try again.", parent=parent, exc=e)

def manage_clients(parent = None):
    try:
        import UI.Manage_clients
        UI.Manage_clients.manage_clients(parent)
    except Exception as e:
        _show_error("Interface Error", "Failed to open Manage Parties window. Please try again.", parent=parent, exc=e)

def new_invoice_ui(parent = None, invoice_id = None):
    try:
        from services.invoice_service import SALES_CONFIG
        from UI.Add_Invoice import open_invoice_window
        open_invoice_window(SALES_CONFIG, parent=parent, invoice_id=invoice_id)
    except Exception as e:
        _show_error("Interface Error", "Failed to open Sales Invoice window. Please try again.", parent=parent, exc=e)

def new_purchase_ui(parent = None, invoice_id = None):
    try:
        from services.invoice_service import PURCHASE_CONFIG
        from UI.Add_Invoice import open_invoice_window
        open_invoice_window(PURCHASE_CONFIG, parent=parent, invoice_id=invoice_id)
    except Exception as e:
        _show_error("Interface Error", "Failed to open Purchase window. Please try again.", parent=parent, exc=e)
 
def manage_invoice_ui(parent = None):
    try:
        import UI.Manage_Invoices
        UI.Manage_Invoices.manage_invoice_ui(parent)
    except Exception as e:
        _show_error("Interface Error", "Failed to open Manage Invoices window. Please try again.", parent=parent, exc=e)

def customer_payment_in(parent = None):
    try:
        from services.payment_service import CLIENT_PAYMENT_CONFIG
        from UI.payment_form import open_payment_window
        open_payment_window(CLIENT_PAYMENT_CONFIG, parent=parent)
    except Exception as e:
        _show_error("Interface Error", "Failed to open Customer Payment window. Please try again.", parent=parent, exc=e)

def expense_payments_out(parent = None):
    try:
        from services.payment_service import EXPENSE_PAYMENT_CONFIG
        from UI.payment_form import open_payment_window
        open_payment_window(EXPENSE_PAYMENT_CONFIG, parent=parent)
    except Exception as e:
        _show_error("Interface Error", "Failed to open Expense Payment window. Please try again.", parent=parent, exc=e)

def supplier_payments_out(parent = None):
    try:
        from services.payment_service import SUPPLIER_PAYMENT_CONFIG
        from UI.payment_form import open_payment_window
        open_payment_window(SUPPLIER_PAYMENT_CONFIG, parent=parent)
    except Exception as e:
        _show_error("Interface Error", "Failed to open Supplier Payment window. Please try again.", parent=parent, exc=e)
  
def pay_salary_ui(parent = None):
    try:
        from services.payment_service import SALARY_PAYMENT_CONFIG
        from UI.payment_form import open_payment_window
        open_payment_window(SALARY_PAYMENT_CONFIG, parent=parent)
    except Exception as e:
        _show_error("Interface Error", "Failed to open Salary Payment window. Please try again.", parent=parent, exc=e)

def new_adjustment_ui(parent = None):
    try:
        import UI.Add_Adjustment
        UI.Add_Adjustment.new_adjustment_ui(parent)
    except Exception as e:
        _show_error("Interface Error", "Failed to open Adjustment window. Please try again.", parent=parent, exc=e)

def manage_payments(parent = None):
    try:
        import UI.Manage_Payments
        UI.Manage_Payments.manage_payments(parent)
    except Exception as e:
        _show_error("Interface Error", "Failed to open Manage Payments window. Please try again.", parent=parent, exc=e)

def company_info(Mode, parent = None):
    try:
        import UI.add_company
        UI.add_company.add_company(Mode, parent)
    except Exception as e:
        _show_error("Interface Error", "Failed to open Company Profile window. Please try again.", parent=parent, exc=e)

def Reports_ui(parent = None):
    try:
        import UI.Reports
        UI.Reports.Reports_ui(parent)
    except Exception as e:
        _show_error("Interface Error", "Failed to open Reports window. Please try again.", parent=parent, exc=e)

def Backup_ui(parent = None):
    try:
        import UI.Backup
        UI.Backup.Backup_ui(parent)
    except Exception as e:
        _show_error("Interface Error", "Failed to open Backup window. Please try again.", parent=parent, exc=e)   

def PrintCheque_ui(Cheque_id = None, parent = None):
    try:
        import UI.ChequePrint
        UI.ChequePrint.PrintOnCheque(Cheque_id, parent)
    except Exception as e:
        _show_error("Interface Error", "Failed to open Print Cheque window. Please try again.", parent=parent, exc=e)   

def addChequeBook_ui(ChequeBook_id = None, parent = None):
    try:
        import UI.AddChequeBook
        UI.AddChequeBook.addChequeBook_ui(ChequeBook_id, parent)
    except Exception as e:
        _show_error("Interface Error", "Failed to open Add Cheque Book window. Please try again.", parent=parent, exc=e)   

def Manage_chequeBook_ui(parent = None):
    try:
        import UI.Manage_chequeBook
        UI.Manage_chequeBook.Manage_chequeBook(parent)
    except Exception as e:
        _show_error("Interface Error", "Failed to open Manage Cheque Books window. Please try again.", parent=parent, exc=e)  

def Manage_Cheques_ui(parent = None):
    try:
        import UI.Manage_Cheques
        UI.Manage_Cheques.Manage_Cheques_ui(parent)
    except Exception as e:
        _show_error("Interface Error", "Failed to open Manage Cheques window. Please try again.", parent=parent, exc=e)  

def payment_getway(parent = None):
    try:
        import UI.Payment_Getway
        UI.Payment_Getway.payment_getway(parent)
    except Exception as e:
        _show_error("Interface Error", "Failed to open Payment Gateway window. Please try again.", parent=parent, exc=e) 

def terms_conditions(parent = None):
    try:
        from UI.terms_conditions import TermsPopup
        TermsPopup.ask_terms(parent)
    except Exception as e:
        _show_error("Interface Error", "Failed to open Terms & Conditions window. Please try again.", parent=parent, exc=e)
