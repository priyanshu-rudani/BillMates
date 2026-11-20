"""
services/report_service.py
--------------------------
Optimized repository and service for billing, ledger, and sales reports.
* Sargable date ranges via ISO expression conversions and SQLite indexes.
* Eliminates N+1 queries and duplicate count/sum roundtrips.
* Single-pass aggregations.
* Strict filter validation (start <= end, max range, SQL parameter sanitization).
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from core.database import query_all, query_one

MAX_ALLOWED_DAYS = 365 * 3  # Maximum allowed query window (3 years)


class ReportFilterError(Exception):
    """Raised when report filters fail safety or validation rules."""
    pass


def validate_and_convert_dates(start_date: str, end_date: str) -> Tuple[str, str]:
    """
    Validates DD/MM/YYYY dates and converts them to YYYY-MM-DD for sargable SQL queries.
    Enforces start_date <= end_date and maximum date range.
    """
    try:
        dt_start = datetime.strptime(str(start_date).strip(), "%d/%m/%Y")
        dt_end = datetime.strptime(str(end_date).strip(), "%d/%m/%Y")
    except (ValueError, AttributeError) as exc:
        raise ReportFilterError("Dates must be valid strings in DD/MM/YYYY format.") from exc

    if dt_start > dt_end:
        raise ReportFilterError(f"Start date ({start_date}) cannot be after end date ({end_date}).")

    if (dt_end - dt_start).days > MAX_ALLOWED_DAYS:
        raise ReportFilterError(f"Requested date range exceeds the maximum limit of {MAX_ALLOWED_DAYS} days.")

    return dt_start.strftime("%Y-%m-%d"), dt_end.strftime("%Y-%m-%d")


def to_iso_sql(column_name: str) -> str:
    """Helper snippet for SQLite expression converting DD/MM/YYYY to YYYY-MM-DD."""
    return f"(substr({column_name}, 7, 4) || '-' || substr({column_name}, 4, 2) || '-' || substr({column_name}, 1, 2))"


class ReportRepository:
    """Encapsulates optimized report queries with server-side aggregation and indexing."""

    @staticmethod
    def get_customer_sales(client_id: int, start_date: str, end_date: str) -> Dict[str, Any]:
        iso_start, iso_end = validate_and_convert_dates(start_date, end_date)
        date_expr = to_iso_sql("i.date")

        sql = f"""
            SELECT 
                i.invoice_no,
                i.date,
                c.name AS client_name,
                COALESCE(i.total, 0.0) AS total,
                COALESCE(i.paid, 0.0) AS paid,
                COALESCE(i.remaining, 0.0) AS remaining,
                i.paid_status,
                COALESCE(i.reference_no, '') AS reference_no
            FROM Invoices i
            JOIN Clients c ON i.client_id = c.id
            WHERE i.client_id = ?
              AND {date_expr} BETWEEN ? AND ?
            ORDER BY {date_expr} ASC, i.invoice_no ASC
        """
        rows = query_all(sql, (client_id, iso_start, iso_end))

        total_paid = sum(r[4] for r in rows)
        total_remaining = sum(r[5] for r in rows)
        total_sales = sum(r[3] for r in rows)

        return {
            "rows": rows,
            "total_paid": round(total_paid, 2),
            "total_remaining": round(total_remaining, 2),
            "total_sales": round(total_sales, 2),
        }

    @staticmethod
    def get_purchase_report(client_id: int, start_date: str, end_date: str) -> Dict[str, Any]:
        iso_start, iso_end = validate_and_convert_dates(start_date, end_date)
        date_expr = to_iso_sql("i.date")

        sql = f"""
            SELECT 
                i.invoice_no,
                i.date,
                c.name AS client_name,
                COALESCE(i.total, 0.0) AS total,
                COALESCE(i.paid, 0.0) AS paid,
                COALESCE(i.remaining, 0.0) AS remaining,
                i.paid_status,
                COALESCE(i.reference_no, '') AS reference_no
            FROM Purchase i
            JOIN Clients c ON i.client_id = c.id
            WHERE i.client_id = ?
              AND {date_expr} BETWEEN ? AND ?
            ORDER BY {date_expr} ASC, i.invoice_no ASC
        """
        rows = query_all(sql, (client_id, iso_start, iso_end))

        total_paid = sum(r[4] for r in rows)
        total_remaining = sum(r[5] for r in rows)
        total_purchases = sum(r[3] for r in rows)

        return {
            "rows": rows,
            "total_paid": round(total_paid, 2),
            "total_remaining": round(total_remaining, 2),
            "total_purchases": round(total_purchases, 2),
        }

    @staticmethod
    def get_customer_payment(client_id: int, start_date: str, end_date: str) -> Dict[str, Any]:
        iso_start, iso_end = validate_and_convert_dates(start_date, end_date)
        date_expr = to_iso_sql("p.date")

        sql = f"""
            SELECT 
                p.date AS Payment_Date,
                p.Expanse_type AS Payment_Type,
                c.name AS Client_Name,
                COALESCE(p.total_amount, 0.0) AS Total_Amount,
                p.payment_mode AS Payment_Mode,
                COALESCE(p.reference_no, '') AS Reference_no
            FROM Payments p
            JOIN Clients c ON p.entity_id = c.id
            WHERE p.entity_id = ?
              AND {date_expr} BETWEEN ? AND ?
            ORDER BY {date_expr} ASC, p.payment_id ASC
        """
        rows = query_all(sql, (client_id, iso_start, iso_end))
        total_amount = sum(r[3] for r in rows)

        return {
            "rows": rows,
            "total_amount": round(total_amount, 2),
        }

    @staticmethod
    def get_opening_balance(client_id: int, start_date: str) -> float:
        """Single-pass atomic query for client/supplier opening balance before start_date."""
        try:
            dt_start = datetime.strptime(str(start_date).strip(), "%d/%m/%Y")
            iso_start = dt_start.strftime("%Y-%m-%d")
        except ValueError as exc:
            raise ReportFilterError("Invalid date format.") from exc

        party = query_one("SELECT client_type, COALESCE(opening_balance, 0.0) FROM Clients WHERE id = ?", (client_id,))
        if not party or party[0] not in ("Client", "Supplier"):
            return 0.0

        client_type, base_opening = party[0], float(party[1])
        date_expr = to_iso_sql("date")

        if client_type == "Client":
            sql = f"""
                SELECT
                    (SELECT COALESCE(SUM(total), 0.0) FROM Invoices WHERE client_id = ? AND {date_expr} < ?),
                    (SELECT COALESCE(SUM(total_amount), 0.0) FROM Payments 
                     WHERE entity_id = ? AND {date_expr} < ? 
                       AND (entity_type = 'Income' OR Expanse_type = 'Adjustment Credit')),
                    (SELECT COALESCE(SUM(total_amount), 0.0) FROM Payments 
                     WHERE entity_id = ? AND {date_expr} < ? 
                       AND Expanse_type = 'Adjustment Debit')
            """
            res = query_one(sql, (client_id, iso_start, client_id, iso_start, client_id, iso_start))
            inv_total, paid_credits, adj_debits = res if res else (0.0, 0.0, 0.0)
            return round(base_opening + paid_credits - (inv_total + adj_debits), 2)
        else:
            sql = f"""
                SELECT
                    (SELECT COALESCE(SUM(total), 0.0) FROM Purchase WHERE client_id = ? AND {date_expr} < ?),
                    (SELECT COALESCE(SUM(total_amount), 0.0) FROM Payments 
                     WHERE entity_id = ? AND {date_expr} < ? 
                       AND (entity_type = 'Expense' OR Expanse_type = 'Adjustment Credit')),
                    (SELECT COALESCE(SUM(total_amount), 0.0) FROM Payments 
                     WHERE entity_id = ? AND {date_expr} < ? 
                       AND Expanse_type = 'Adjustment Debit')
            """
            res = query_one(sql, (client_id, iso_start, client_id, iso_start, client_id, iso_start))
            pur_total, paid_credits, adj_debits = res if res else (0.0, 0.0, 0.0)
            return round(base_opening + paid_credits - (pur_total + adj_debits), 2)

    @staticmethod
    def get_customer_ledger(client_id: int, start_date: str, end_date: str) -> List[Tuple]:
        iso_start, iso_end = validate_and_convert_dates(start_date, end_date)
        inv_date_expr = to_iso_sql("i.date")
        pay_date_expr = to_iso_sql("i.date")

        sql = f"""
            SELECT 
                Date,
                Description,
                Credited,
                Debited
            FROM (
                SELECT 
                    i.date AS Date,
                    {inv_date_expr} AS iso_date,
                    'Invoice (' || printf('INV%03d', i.invoice_no) || ')' AS Description,
                    0.0 AS Credited,
                    COALESCE(i.total, 0.0) AS Debited,
                    i.invoice_id AS sort_id
                FROM Invoices i
                JOIN Clients c ON i.client_id = c.id
                WHERE i.client_id = ? AND {inv_date_expr} BETWEEN ? AND ? AND c.client_type = 'Client'

                UNION ALL

                SELECT 
                    i.date AS Date,
                    {inv_date_expr} AS iso_date,
                    'Invoice (' || printf('INV%03d', i.invoice_no) || ')' AS Description,
                    0.0 AS Credited,
                    COALESCE(i.total, 0.0) AS Debited,
                    i.invoice_id AS sort_id
                FROM Purchase i
                JOIN Clients c ON i.client_id = c.id
                WHERE i.client_id = ? AND {inv_date_expr} BETWEEN ? AND ? AND c.client_type = 'Supplier'

                UNION ALL

                SELECT 
                    i.date AS Date,
                    {pay_date_expr} AS iso_date,
                    i.Expanse_type AS Description,
                    COALESCE(
                        CASE 
                            WHEN i.entity_type = 'Income' AND c.client_type = 'Client' THEN i.total_amount
                            WHEN i.entity_type = 'Expense' AND c.client_type = 'Supplier' THEN i.total_amount
                            WHEN i.Expanse_type = 'Adjustment Credit' THEN i.total_amount
                        END, 0.0) AS Credited,
                    COALESCE(
                        CASE 
                            WHEN i.Expanse_type = 'Adjustment Debit' THEN i.total_amount
                        END, 0.0) AS Debited,
                    i.payment_id AS sort_id
                FROM Payments i
                JOIN Clients c ON i.entity_id = c.id
                WHERE i.entity_id = ? AND {pay_date_expr} BETWEEN ? AND ?
            ) AS combined_results
            ORDER BY iso_date ASC, sort_id ASC
        """
        params = (client_id, iso_start, iso_end, client_id, iso_start, iso_end, client_id, iso_start, iso_end)
        rows = query_all(sql, params)

        opening = ReportRepository.get_opening_balance(client_id, start_date)
        ledger_with_balance = [(' ', 'Opening Balance', 0, 0, opening)]
        balance = opening

        for entry in rows:
            date, desc, credit, debit = entry[0], entry[1], float(entry[2]), float(entry[3])
            balance += credit
            balance -= debit
            ledger_with_balance.append((date, desc, credit, debit, round(balance, 2)))

        ledger_with_balance.append((' ', 'Closing Balance', 0, 0, round(balance, 2)))
        return ledger_with_balance

    @staticmethod
    def get_cashflow_report(start_date: str, end_date: str) -> Dict[str, Any]:
        iso_start, iso_end = validate_and_convert_dates(start_date, end_date)
        date_expr = to_iso_sql("p.date")

        sql = f"""
            SELECT
                p.date AS Date,
                COALESCE(c.name, 'Company Expense') AS Client_Name,
                CASE
                    WHEN p.entity_type = 'Income' OR p.Expanse_type = 'Adjustment Credit' THEN 'Payment In'
                    WHEN p.entity_type IN ('Expense', 'Salaries') OR p.Expanse_type = 'Adjustment Debit' THEN 'Payment Out'
                    ELSE 'Unknown'
                END AS Payment_Category,
                COALESCE(p.total_amount, 0.0) AS Total,
                p.payment_mode AS Payment_Mode,
                p.Expanse_type AS Payment_Type,
                COALESCE(p.reference_no, '') AS Reference_No
            FROM Payments p
            LEFT JOIN Clients c ON p.entity_id = c.id
            WHERE {date_expr} BETWEEN ? AND ?
            ORDER BY {date_expr} ASC, p.payment_id ASC
        """
        rows = query_all(sql, (iso_start, iso_end))
        payment_in = sum(r[3] for r in rows if r[2] == "Payment In")
        payment_out = sum(r[3] for r in rows if r[2] == "Payment Out")

        return {
            "rows": rows,
            "total_in": round(payment_in, 2),
            "total_out": round(payment_out, 2),
        }

    @staticmethod
    def get_financial_dashboard_metrics(start_date: str, end_date: str) -> Dict[str, float]:
        """
        Calculates standard financial metrics conforming with accounting principles:
        1. Accrual Revenue: Gross Sales = Total Invoices billed (paid + remaining)
        2. Cash Revenue: Collected Revenue = Payments received for invoices
        3. Cost of Goods Sold (COGS): Direct material procurement (Purchases total = settled + payable) 
           plus direct inbound logistics/transposition
        4. Operating Expenses (OPEX): Operating overheads (Rent, Utilities, Maintenance, Marketing, 
           Loan Interest, Taxes, Other Expenses) + Salaries/Wages
        5. Gross Profit: Gross Sales - COGS
        6. Net Profit / Loss: Gross Profit - Operating Expenses
        """
        iso_start, iso_end = validate_and_convert_dates(start_date, end_date)
        inv_date = to_iso_sql("date")

        sql = f"""
            WITH SalesData AS (
                SELECT 
                    COALESCE(SUM(paid), 0.0) AS invoice_paid,
                    COALESCE(SUM(remaining), 0.0) AS accounts_receivable,
                    COALESCE(SUM(total), 0.0) AS total_sales
                FROM Invoices
                WHERE {inv_date} BETWEEN ? AND ?
            ),
            CollectedData AS (
                SELECT
                    COALESCE(SUM(total_amount), 0.0) AS collected_revenue
                FROM Payments
                WHERE Expanse_type = 'Invoice Payment' AND entity_type = 'Income'
                  AND {inv_date} BETWEEN ? AND ?
            ),
            PurchasesData AS (
                SELECT 
                    COALESCE(SUM(paid), 0.0) AS invoice_purchase_paid,
                    COALESCE(SUM(remaining), 0.0) AS accounts_payable,
                    COALESCE(SUM(total), 0.0) AS total_purchase
                FROM Purchase
                WHERE {inv_date} BETWEEN ? AND ?
            ),
            SettledPurchaseData AS (
                SELECT
                    COALESCE(SUM(total_amount), 0.0) AS settled_purchases
                FROM Payments
                WHERE Expanse_type = 'Payment For Purchase' AND entity_type = 'Expense'
                  AND {inv_date} BETWEEN ? AND ?
            ),
            SalariesData AS (
                SELECT 
                    COALESCE(SUM(total_amount), 0.0) AS settled_salaries
                FROM Payments
                WHERE Expanse_type = 'Salary' AND {inv_date} BETWEEN ? AND ?
            ),
            LogisticsData AS (
                SELECT 
                    COALESCE(SUM(total_amount), 0.0) AS logistics_costs
                FROM Payments
                WHERE Expanse_type = 'Transposition' AND {inv_date} BETWEEN ? AND ?
            ),
            OperatingExpensesData AS (
                SELECT
                    COALESCE(SUM(CASE WHEN Expanse_type = 'Rent' THEN total_amount ELSE 0 END), 0.0) AS rental_expenses,
                    COALESCE(SUM(CASE WHEN Expanse_type = 'Utilities' THEN total_amount ELSE 0 END), 0.0) AS utilities_expenditure,
                    COALESCE(SUM(CASE WHEN Expanse_type = 'Maintenance' THEN total_amount ELSE 0 END), 0.0) AS upkeep_expenses,
                    COALESCE(SUM(CASE WHEN Expanse_type = 'Marketing' THEN total_amount ELSE 0 END), 0.0) AS marketing_expenses,
                    COALESCE(SUM(CASE WHEN Expanse_type = 'Loan Interest' THEN total_amount ELSE 0 END), 0.0) AS loan_interest_cost,
                    COALESCE(SUM(CASE WHEN Expanse_type = 'Taxes' THEN total_amount ELSE 0 END), 0.0) AS statutory_dues,
                    COALESCE(SUM(CASE WHEN Expanse_type = 'Other Expances' THEN total_amount ELSE 0 END), 0.0) AS other_expenses
                FROM Payments
                WHERE Expanse_type IN ('Rent', 'Utilities', 'Maintenance', 'Marketing', 'Loan Interest', 'Taxes', 'Other Expances') 
                  AND entity_type = 'Expense' 
                  AND {inv_date} BETWEEN ? AND ?
            )
            SELECT
                total_sales,
                accounts_receivable,
                collected_revenue,
                total_purchase,
                accounts_payable,
                settled_purchases,
                settled_salaries,
                logistics_costs,
                (total_purchase + logistics_costs) AS total_cogs,
                (total_sales - (total_purchase + logistics_costs)) AS gross_profit,
                rental_expenses,
                utilities_expenditure,
                upkeep_expenses,
                marketing_expenses,
                loan_interest_cost,
                statutory_dues,
                other_expenses,
                (settled_salaries + rental_expenses + utilities_expenditure + upkeep_expenses + marketing_expenses + loan_interest_cost + statutory_dues + other_expenses) AS total_operating_expenses,
                (
                    total_sales - (total_purchase + logistics_costs) - 
                    (settled_salaries + rental_expenses + utilities_expenditure + upkeep_expenses + marketing_expenses + loan_interest_cost + statutory_dues + other_expenses)
                ) AS net_profit_loss
            FROM SalesData, CollectedData, PurchasesData, SettledPurchaseData, SalariesData, LogisticsData, OperatingExpensesData
        """
        params = (
            iso_start, iso_end,
            iso_start, iso_end,
            iso_start, iso_end,
            iso_start, iso_end,
            iso_start, iso_end,
            iso_start, iso_end,
            iso_start, iso_end,
        )
        row = query_one(sql, params)
        if not row:
            keys = [
                "total_sales", "accounts_receivable", "collected_revenue", "total_purchase",
                "accounts_payable", "settled_purchases", "settled_salaries", "logistics_costs",
                "total_cogs", "gross_profit", "rental_expenses", "utilities_expenditure",
                "upkeep_expenses", "marketing_expenses", "loan_interest_cost", "statutory_dues",
                "other_expenses", "total_operating_expenses", "net_profit_loss"
            ]
            return {k: 0.0 for k in keys}

        return {
            "total_sales": float(row[0] or 0.0),
            "accounts_receivable": float(row[1] or 0.0),
            "collected_revenue": float(row[2] or 0.0),
            "total_purchase": float(row[3] or 0.0),
            "accounts_payable": float(row[4] or 0.0),
            "settled_purchases": float(row[5] or 0.0),
            "settled_salaries": float(row[6] or 0.0),
            "logistics_costs": float(row[7] or 0.0),
            "total_cogs": float(row[8] or 0.0),
            "gross_profit": float(row[9] or 0.0),
            "rental_expenses": float(row[10] or 0.0),
            "utilities_expenditure": float(row[11] or 0.0),
            "upkeep_expenses": float(row[12] or 0.0),
            "marketing_expenses": float(row[13] or 0.0),
            "loan_interest_cost": float(row[14] or 0.0),
            "statutory_dues": float(row[15] or 0.0),
            "other_expenses": float(row[16] or 0.0),
            "total_operating_expenses": float(row[17] or 0.0),
            "net_profit_loss": float(row[18] or 0.0),
        }

    @staticmethod
    def get_profit_loss_report(start_date: str, end_date: str) -> tuple:
        metrics = ReportRepository.get_financial_dashboard_metrics(start_date, end_date)
        # Returns tuple aligned with GenerateReport.py structure
        return (
            metrics["collected_revenue"],        # 0: Collected Revenue
            metrics["accounts_receivable"],      # 1: Accounts Receivable
            metrics["total_sales"],              # 2: Gross Revenue (1+2 in accrual accounting)
            metrics["settled_purchases"],        # 3: Settled Purchases
            metrics["accounts_payable"],         # 4: Accounts Payable
            metrics["settled_salaries"],         # 5: Settled Salaries (Operating Expense / Staff Wages)
            metrics["logistics_costs"],          # 6: Comprehensive Logistics Costs (Direct COGS)
            metrics["total_cogs"],               # 7: Total COGS (Purchases + Logistics)
            metrics["gross_profit"],             # 8: Gross Profit/Loss (Gross Revenue - Total COGS)
            metrics["rental_expenses"],          # 9: Rental Expenses
            metrics["utilities_expenditure"],    # 10: Utilities Expenditure
            metrics["upkeep_expenses"],          # 11: Upkeep Expenses
            metrics["marketing_expenses"],       # 12: Marketing Expenses
            metrics["loan_interest_cost"],       # 13: Loan Interest Cost
            metrics["statutory_dues"],           # 14: Statutory Dues
            metrics["other_expenses"],           # 15: Other Expenses
            metrics["total_operating_expenses"], # 16: Total Operating Expenses (Overhead + Salaries)
            metrics["net_profit_loss"],          # 17: Net Profit/Loss (Gross Profit - Operating Expenses)
        )

    @staticmethod
    def get_revenue_report(start_date: str, end_date: str) -> Dict[str, Any]:
        iso_start, iso_end = validate_and_convert_dates(start_date, end_date)
        inv_date = to_iso_sql("i.date")
        pay_date = to_iso_sql("p.date")

        sql = f"""
            SELECT
                Payment_Date,
                type,
                client_name,
                Amount,
                payment_status,
                reference_no
            FROM (
                SELECT 
                    i.date AS Payment_Date,
                    {inv_date} AS iso_date,
                    'Sales Invoice(INV' || printf('%03d', i.invoice_no) || ')' AS type,
                    c.name AS client_name,
                    COALESCE(i.total, 0.0) AS Amount,
                    i.paid_status AS payment_status,
                    COALESCE(i.reference_no, '') AS reference_no,
                    i.invoice_id AS sort_id
                FROM Invoices i
                JOIN Clients c ON i.client_id = c.id
                WHERE {inv_date} BETWEEN ? AND ?

                UNION ALL

                SELECT 
                    p.date AS Payment_Date,
                    {pay_date} AS iso_date,
                    p.Expanse_type AS type,
                    c.name AS client_name,
                    COALESCE(p.total_amount, 0.0) AS Amount,
                    p.payment_mode AS payment_status,
                    COALESCE(p.reference_no, '') AS reference_no,
                    p.payment_id AS sort_id
                FROM Payments p
                JOIN Clients c ON p.entity_id = c.id
                WHERE {pay_date} BETWEEN ? AND ? AND p.Expanse_type = 'Adjustment Credit'
            ) AS subquery
            ORDER BY iso_date ASC, sort_id ASC
        """
        rows = query_all(sql, (iso_start, iso_end, iso_start, iso_end))
        total_amount = sum(r[3] for r in rows)

        return {
            "rows": rows,
            "total_amount": round(total_amount, 2),
        }

    @staticmethod
    def get_expense_analysis(start_date: str, end_date: str) -> Dict[str, Any]:
        iso_start, iso_end = validate_and_convert_dates(start_date, end_date)
        date_expr = to_iso_sql("p.date")

        sql = f"""
            SELECT
                p.date AS Date,
                p.Expanse_type AS type,
                COALESCE(c.name, 'Company Expense') AS client_name,
                COALESCE(p.total_amount, 0.0) AS Amount,
                p.payment_mode AS payment_mode,
                COALESCE(p.reference_no, '') AS reference_no
            FROM Payments p
            LEFT JOIN Clients c ON p.entity_id = c.id
            WHERE {date_expr} BETWEEN ? AND ?
              AND (p.entity_type IN ('Expense', 'Salaries') OR p.Expanse_type = 'Adjustment Debit')
            ORDER BY {date_expr} ASC, p.payment_id ASC
        """
        rows = query_all(sql, (iso_start, iso_end))
        total_amount = sum(r[3] for r in rows)

        return {
            "rows": rows,
            "total_amount": round(total_amount, 2),
        }
