import sys
from pathlib import Path

if getattr(sys, 'frozen', False):  # Running as a PyInstaller EXE
    root_path = Path(sys.executable).parent
else:  # Running as a Python script
    root_path = Path(__file__).parent.parent
sys.path.append(str(root_path))
 
from utilities.path_utils import *
from datetime import datetime, timedelta
from tkinter import messagebox, filedialog
import sqlite3
import os
from openpyxl import Workbook
from openpyxl.utils import get_column_letter
from openpyxl.styles import Font, Alignment, PatternFill
from services.report_service import ReportRepository, ReportFilterError

# ================================================================================================================
# Customer Specific & General Reports (Delegated to optimized ReportRepository)
# ================================================================================================================

def get_opening_balance(client_id, start_date):
    try:
        return ReportRepository.get_opening_balance(client_id, start_date)
    except Exception as e:
        messagebox.showerror("Report Error", f"Unable to calculate opening balance: {e}")
        return 0.0

def customer_sales(client_name, first_date, last_date):
    try:
        client_id = get_client_id(client_name)
        res = ReportRepository.get_customer_sales(client_id, first_date, last_date)
        rows = res["rows"]
        if not rows:
            return []
        data = [
            ('', '', '', '', '', '', '', ''),
            ('', '', '', '', '', '', '', ''),
            ('Paid sales', res["total_paid"], '', 'Credit Sales', res["total_remaining"], '', 'Total Sales', res["total_sales"]),
            ('', '', '', '', '', '', '', '')
        ]
        return rows + data
    except ReportFilterError as rfe:
        messagebox.showwarning("Filter Warning", str(rfe))
        return []
    except Exception as e:
        messagebox.showerror("Report Error", f"Error generating customer sales: {e}")
        return []

def purchase_report(client_name, first_date, last_date):
    try:
        client_id = get_client_id(client_name)
        res = ReportRepository.get_purchase_report(client_id, first_date, last_date)
        rows = res["rows"]
        if not rows:
            return []
        data = [
            ('', '', '', '', '', '', '', ''),
            ('', '', '', '', '', '', '', ''),
            ('Paid sales', res["total_paid"], '', 'Credit Sales', res["total_remaining"], '', 'Total Sales', res["total_purchases"]),
            ('', '', '', '', '', '', '', '')
        ]
        return rows + data
    except ReportFilterError as rfe:
        messagebox.showwarning("Filter Warning", str(rfe))
        return []
    except Exception as e:
        messagebox.showerror("Report Error", f"Error generating purchase report: {e}")
        return []

def customer_payment(client_name, first_date, last_date):
    try:
        client_id = get_client_id(client_name)
        res = ReportRepository.get_customer_payment(client_id, first_date, last_date)
        rows = res["rows"]
        if not rows:
            return []
        data = [
            ('', '', '', '', '', ''),
            ('', '', '', '', '', ''),
            ('', '', 'Total Payment', res["total_amount"], '', ''),
            ('', '', '', '', '', '')
        ]
        return rows + data
    except ReportFilterError as rfe:
        messagebox.showwarning("Filter Warning", str(rfe))
        return []
    except Exception as e:
        messagebox.showerror("Report Error", f"Error generating customer payment report: {e}")
        return []

def customer_ledger(client_name, first_date, last_date):
    try:
        client_id = get_client_id(client_name)
        client_type = get_client_type(client_name)
        if client_type not in ['Client', 'Supplier']:
            return []
        return ReportRepository.get_customer_ledger(client_id, first_date, last_date)
    except ReportFilterError as rfe:
        messagebox.showwarning("Filter Warning", str(rfe))
        return []
    except Exception as e:
        messagebox.showerror("Report Error", f"Error generating customer ledger: {e}")
        return []

def cashflow_report(first_date, last_date):
    try:
        res = ReportRepository.get_cashflow_report(first_date, last_date)
        rows = res["rows"]
        if not rows:
            return []
        data = [
            ('', '', '', '', '', '', ''),
            ('', '', '', '', '', '', ''),
            ('', 'Total Payment In', res["total_in"], '', 'Total Payment Out', res["total_out"], ''),
            ('', '', '', '', '', '', '')
        ]
        return rows + data
    except ReportFilterError as rfe:
        messagebox.showwarning("Filter Warning", str(rfe))
        return []
    except Exception as e:
        messagebox.showerror("Report Error", f"Error generating cashflow report: {e}")
        return []

def profit_loss_report(first_date, last_date):
    try:
        report = ReportRepository.get_profit_loss_report(first_date, last_date)
        if not report or report[0] is None:
            return []
        data = [
            (' ', 'Revenue', '', ''),
            (1, 'Collected Revenue', '', round(report[0], 2)),
            (2, 'Accounts Receivable', '', round(report[1], 2)),
            (3, 'Gross Revenue', '(1+2)', round(report[2], 2)),
            (' ', '', '', ''),
            (' ', 'Cost of Goods Sold (COGS)', '', ''),
            (4, 'Settled Purchases', '', round(report[3], 2)),
            (5, 'Accounts Payable', '', round(report[4], 2)),
            (6, 'Comprehensive Logistics Costs', '', round(report[6], 2)),
            (7, 'Total COGS Expenditure', '(4+5+6)', round(report[7], 2)),
            (' ', '', '', ''),
            (8, 'Gross Profit/Loss', '(3-7)', round(report[8], 2)),
            (' ', '', '', ''),
            (' ', 'Operating Expenses (OPEX)', '', ''),
            (9, 'Staff Salaries & Wages', '', round(report[5], 2)),
            (10, 'Rental Expenses', '', round(report[9], 2)),
            (11, 'Utilities Expenditure', '', round(report[10], 2)),
            (12, 'Upkeep Expenses', '', round(report[11], 2)),
            (13, 'Marketing Expenses', '', round(report[12], 2)),
            (14, 'Loan Interest Cost', '', round(report[13], 2)),
            (15, 'Statutory Dues', '', round(report[14], 2)), 
            (16, 'Other Expances', '', round(report[15], 2)),
            (17, 'Total Operating Expenses', '(9 To 16)', round(report[16], 2)),
            (' ', '', '', ''),
            (18, 'Net Profit/Loss', '(8-17)', round(report[17], 2)),
        ]
        return data
    except ReportFilterError as rfe:
        messagebox.showwarning("Filter Warning", str(rfe))
        return []
    except Exception as e:
        messagebox.showerror("Report Error", f"Error generating profit & loss report: {e}")
        return []

def revenue_report(first_date, last_date):
    try:
        res = ReportRepository.get_revenue_report(first_date, last_date)
        rows = res["rows"]
        if not rows:
            return []
        data = [
            ('', '', '', '', '', ''),
            ('', '', '', '', '', ''),
            ('', '', '', 'Total Revenue', res["total_amount"], ''),
            ('', '', '', '', '', '')
        ]
        return rows + data
    except ReportFilterError as rfe:
        messagebox.showwarning("Filter Warning", str(rfe))
        return []
    except Exception as e:
        messagebox.showerror("Report Error", f"Error generating revenue report: {e}")
        return []

def expense_analysis(first_date, last_date):
    try:
        res = ReportRepository.get_expense_analysis(first_date, last_date)
        rows = res["rows"]
        if not rows:
            return []
        data = [
            ('', '', '', '', '', ''),
            ('', '', '', '', '', ''),
            ('', '', 'Total Expanse', res["total_amount"], '', ''),
            ('', '', '', '', '', '')
        ]
        return rows + data
    except ReportFilterError as rfe:
        messagebox.showwarning("Filter Warning", str(rfe))
        return []
    except Exception as e:
        messagebox.showerror("Report Error", f"Error generating expense analysis: {e}")
        return []



# Export as Excel
def export_report(report_type, start_date, end_date, client_name=None):
    try:
        safe_start_date = datetime.strptime(start_date, "%d/%m/%Y").strftime("%d-%m-%Y")
        safe_end_date = datetime.strptime(end_date, "%d/%m/%Y").strftime("%d-%m-%Y")
        if client_name is None:
            file_name = f"{report_type}-{safe_start_date}_{safe_end_date}"
        else:
            file_name = f"{client_name}-{report_type}_{safe_start_date}_{safe_end_date}"

        file_path = filedialog.asksaveasfilename(
            defaultextension=".xlsx", 
            filetypes=[("Excel files", "*.xlsx")],
            initialfile = file_name,
            title=f"Save {report_type}"
        )

        if file_path:

            wb = Workbook()
            sheet = wb.active
            sheet.title = report_type


            if report_type == 'Sales Reports':  
                headers  = ["Invoice No.", "Date", "Client Name", "Total", "Paid", "Remaining", "Paid Status", "Reference No."]
                data = customer_sales(client_name, start_date, end_date)
                column_widths = [17, 17, 17, 17, 17, 17, 17, 20]

            elif report_type == 'Purchase Reports':
                headers  = ["Invoice No.", "Date", "Suppiler Name", "Total", "Paid", "Unpaid", "Paid Status", "Reference No."]
                data = purchase_report(client_name, start_date, end_date)
                column_widths = [17, 17, 17, 17, 17, 17, 17, 20]

            elif report_type == 'Client Payment Reports':
                headers  = ["Date", "Payment Type", "Client Name", "Total Amount", "Payment Mode", "Reference No."]
                data = customer_payment(client_name, start_date, end_date)
                column_widths = [15, 20, 18, 17, 18, 21]

            elif report_type == 'Client Ledger':
                headers  = ["Date", "Description", "Credited", "Debited", "Balance"]
                data = customer_ledger(client_name, start_date, end_date)
                column_widths = [15, 35, 14, 14, 14]

            elif report_type == 'Cash Flow Statement':
                headers  = ["Date", "Client Name", "Payment Category", "Total", "Payment Mode", "Payment Type", "Reference No."]
                data = cashflow_report(start_date, end_date)
                column_widths = [15, 20, 20, 15, 20, 25, 20]

            elif report_type == 'Profit and Loss Statement':
                headers  = ["Sr No.", "Category", " ", "Amount"]
                data = profit_loss_report(start_date, end_date)
                column_widths = [10, 39, 10, 15]

            elif report_type == 'Revenue Reports':
                headers  = ["Payment Date", "Payment Type", "Client Name", "Amount", "Payment Status", "Reference no."]
                data = revenue_report(start_date, end_date)
                column_widths = [16, 25, 20, 16, 19, 20]

            elif report_type == 'Expense Analysis':
                headers  = ["Date", "Expense Type", "Client Name", "Amount", "Payment Mode", "Reference no."]
                data = expense_analysis(start_date, end_date)
                column_widths = [15, 30, 22, 16, 16, 20]

            else:
                headers = []
                data = []
                return


            for col_num, width in enumerate(column_widths, start=1):
                col_letter = get_column_letter(col_num)
                sheet.column_dimensions[col_letter].width = width

            sheet.row_dimensions[1].height = 22
            for col_num, header in enumerate(headers, start=1):
                cell = sheet.cell(row=1, column=col_num, value=header)
                cell.font = Font(bold=True, color="000000", size= 12)
                cell.fill = PatternFill(start_color="CCC0DA", end_color="CCC0DA", fill_type="solid")
                cell.alignment = Alignment(horizontal="center", vertical="center")

            for row_num, row in enumerate(data, start=2):
                for col_num, value in enumerate(row, start=1):
                    cell = sheet.cell(row=row_num, column=col_num, value=value)
                    cell.alignment = Alignment(horizontal="center", vertical="center")

            if report_type == 'Client Ledger':
                sheet.row_dimensions[2].height = 22
                for col_num in range(1, sheet.max_column + 1):
                    cell = sheet.cell(row=2, column=col_num)
                    cell.font = Font(bold=True, size= 12)
                    cell.alignment = Alignment(horizontal="center", vertical="center")

                last_row = sheet.max_row 
                sheet.row_dimensions[last_row].height = 22
                for col_num in range(1, sheet.max_column + 1):
                    cell = sheet.cell(row=last_row, column=col_num)
                    cell.font = Font(bold=True, size= 12)  
                    cell.alignment = Alignment(horizontal="center", vertical="center")

                for row in range(1, sheet.max_row + 1):  
                    cell = sheet.cell(row=row, column=2)  
                    cell.alignment = Alignment(horizontal="left", vertical="center")

            elif report_type == 'Profit and Loss Statement':

                target_rows = [2, 5, 7, 12, 14, 16, 24, 26]
                for row_num in target_rows:
                    sheet.row_dimensions[row_num].height = 30
                    for col_num in range(1, sheet.max_column + 1):
                        cell = sheet.cell(row=row_num, column=col_num)
                        cell.font = Font(bold=True) 

                for row_num in range(2, sheet.max_row + 1):
                    for col_num in range(1, sheet.max_column + 1):  # Loop through all columns
                        cell = sheet.cell(row=row_num, column=col_num)
                        if col_num == 2:  # Column B
                            cell.alignment = Alignment(horizontal="left", vertical="center")
                        elif col_num == 4:  # Column D
                            cell.alignment = Alignment(horizontal="right", vertical="center")
                            cell.number_format = '#,##0.00'
                        elif col_num == 3:  # Column C
                            cell.alignment = Alignment(horizontal="right", vertical="center")
                        else:  # All other columns
                            cell.alignment = Alignment(horizontal="center", vertical="center")



            if report_type not in ['Client Ledger', 'Profit and Loss Statement']:
                total_rows = len(data) + 1
                if total_rows >= 3:
                    target_row = total_rows - 1
                    sheet.row_dimensions[target_row].height = 22
                    for col_num in range(1, len(headers) + 1):
                        cell = sheet.cell(row=target_row, column=col_num)
                        cell.font = Font(bold=True, color="000000", size= 12)
                        cell.fill = PatternFill(start_color="CCC0DA", end_color="CCC0DA", fill_type="solid")
                        cell.alignment = Alignment(horizontal="center", vertical="center") 

            wb.save(file_path)
            response = messagebox.askquestion("Invoice Saved", f"Invoice saved at {file_path} \nDo you want to open the Excel?")
            if response == 'yes':
                os.startfile(file_path)

    except PermissionError:
        messagebox.showerror("Permission Error", f"Permission denied: Unable to save the file. Please close the file")
    except FileNotFoundError:
        messagebox.showerror("File Not Found", f"Invalid file path: Please provide a valid path.")
    except Exception as e:
        messagebox.showerror("Unexpected Error", f"An unexpected error occurred while saving the file:\n{e}")