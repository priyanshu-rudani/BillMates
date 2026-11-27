"""
services/payment_service.py
---------------------------
Unified payment business logic for Client, Supplier, and Expense payments.

Separates business logic and database updates from Tkinter GUI:
* Pure Python data structures (PaymentInput, PaymentConfig)
* Safe transaction management (auto rollback on failure)
* Reusable across Sales/Client payments, Purchase/Supplier payments, and Expense payments
* Uses centralized database functions (query_one, query_all, execute_non_query)
"""

from dataclasses import dataclass
from typing import Optional
from core.database import get_db_connection, execute_non_query, execute_query


class PaymentError(Exception):
    """Business rule or validation violation during payment processing."""
    def __init__(self, message: str, title: str = "Error", level: str = "error"):
        super().__init__(message)
        self.message = message
        self.title = title
        self.level = level  # "error" | "warning" | "info"


@dataclass(frozen=True)
class PaymentConfig:
    """Configures the behavior and database targets for different payment flows."""
    name: str                       # 'client', 'supplier', or 'expense'
    entity_type: str                # Value stored in Payments.entity_type ('Income' or 'Expense')
    client_type: str                # Value in Clients.client_type ('Client' or 'Supplier' or '')
    window_title: str
    target_label: str               # 'Client Name', 'Supplier Name', or 'Expense Type'
    expense_type_name: str          # Value stored in Payments.Expanse_type column
    invoice_table: Optional[str]    # 'Invoices' for client, 'Purchase' for supplier, None for expense
    balance_sign: int               # +1: closing_bal += amount, -1: closing_bal -= amount


CLIENT_PAYMENT_CONFIG = PaymentConfig(
    name="client",
    entity_type="Income",
    client_type="Client",
    window_title="Add Customer Payments",
    target_label="Client Name",
    expense_type_name="Invoice Payment",
    invoice_table="Invoices",
    balance_sign=1,
)

SUPPLIER_PAYMENT_CONFIG = PaymentConfig(
    name="supplier",
    entity_type="Expense",
    client_type="Supplier",
    window_title="Add Supplier Payments",
    target_label="Supplier Name",
    expense_type_name="Payment For Purchase",
    invoice_table="Purchase",
    balance_sign=1,
)

SALARY_PAYMENT_CONFIG = PaymentConfig(
    name="salary",
    entity_type="Salaries",
    client_type="Staff",
    window_title="Add Salary Payment",
    target_label="Staff Name",
    expense_type_name="Salary",
    invoice_table=None,
    balance_sign=1,
)

EXPENSE_PAYMENT_CONFIG = PaymentConfig(
    name="expense",
    entity_type="Expense",
    client_type="",
    window_title="Add Expense Payments",
    target_label="Expense Type",
    expense_type_name="Expense",
    invoice_table=None,
    balance_sign=0,
)


@dataclass
class PaymentInput:
    target_name: str          # Client/Supplier name or expense type
    date: str                 # e.g., "DD/MM/YYYY"
    total_amount: str | float
    payment_mode: str         # e.g., "Cash", "UPI", "Bank Transfer", "Cheque"
    reference_no: str = ""


class PaymentService:
    def __init__(self, config: PaymentConfig):
        self.config = config

    def validate_and_record_payment(self, form: PaymentInput) -> None:
        """
        Validates form inputs, settles outstanding invoices FIFO (if applicable),
        updates client/supplier balance, and records the payment record in the DB atomically.
        """
        target = form.target_name.strip()
        if not target:
            raise PaymentError(f"{self.config.target_label} is required!", level="warning")

        date_val = str(form.date).strip()
        if not date_val:
            raise PaymentError("Date is required!", level="warning")

        try:
            amount = round(float(form.total_amount), 2)
            if amount <= 0:
                raise ValueError
        except (ValueError, TypeError):
            raise PaymentError("Total amount must be a valid positive number!", level="warning")

        payment_mode = form.payment_mode.strip()
        if not payment_mode:
            raise PaymentError("Payment mode is required!", level="warning")

        reference_no = (form.reference_no or "").strip()

        with get_db_connection() as conn:
            if self.config.name == "expense":
                # Company expenses are recorded with entity_id = None (not tied to any client or supplier)
                execute_non_query(
                    """
                    INSERT INTO Payments (entity_id, entity_type, date, total_amount, payment_mode, reference_no, Expanse_type)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (None, self.config.entity_type, date_val, amount, payment_mode, reference_no, target),
                    conn=conn,
                )
                return

            # Client or Supplier payment
            rows = execute_query(
                "SELECT id, closing_bal FROM Clients WHERE name = ? AND client_type = ?",
                (target, self.config.client_type),
                conn=conn,
            )
            if not rows:
                raise PaymentError(
                    f"No {self.config.client_type.lower()} found with name '{target}'.",
                    title="Party Not Found",
                    level="error",
                )

            entity_id, current_closing_bal = rows[0]
            current_closing_bal = float(current_closing_bal or 0.0)

            # Settle invoices FIFO if invoice table is configured
            if self.config.invoice_table:
                open_invoices = execute_query(
                    f"""
                    SELECT invoice_id, total, paid, remaining
                    FROM {self.config.invoice_table}
                    WHERE client_id = ? AND remaining > 0 AND paid_status != 'Paid'
                    ORDER BY created_at ASC
                    """,
                    (entity_id,),
                    conn=conn,
                )
                remaining_payment = amount

                for inv in open_invoices:
                    if remaining_payment <= 0:
                        break
                    inv_id, inv_total, inv_paid, inv_remaining = inv
                    if remaining_payment >= inv_remaining:
                        execute_non_query(
                            f"UPDATE {self.config.invoice_table} SET paid = ?, remaining = 0, paid_status = 'Paid' WHERE invoice_id = ?",
                            (inv_total, inv_id),
                            conn=conn,
                        )
                        remaining_payment -= inv_remaining
                    else:
                        execute_non_query(
                            f"UPDATE {self.config.invoice_table} SET paid = ?, remaining = ?, paid_status = 'Partially Paid' WHERE invoice_id = ?",
                            (inv_paid + remaining_payment, inv_remaining - remaining_payment, inv_id),
                            conn=conn,
                        )
                        remaining_payment = 0
                        break

            # Update client/supplier balance
            new_closing_bal = current_closing_bal + (self.config.balance_sign * amount)
            execute_non_query(
                "UPDATE Clients SET closing_bal = ? WHERE id = ?",
                (round(new_closing_bal, 2), entity_id),
                conn=conn,
            )

            # Record Payment
            execute_non_query(
                """
                INSERT INTO Payments (entity_id, entity_type, date, total_amount, payment_mode, reference_no, Expanse_type)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    entity_id,
                    self.config.entity_type,
                    date_val,
                    amount,
                    payment_mode,
                    reference_no,
                    self.config.expense_type_name,
                ),
                conn=conn,
            )
