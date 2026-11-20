"""
UI/paymentOut.py
----------------
Company / Overhead Expense Payment Out entry window.
Delegates to UI/payment_form.py for unified form layout and services/payment_service.py for business logic.
"""

import sys
from pathlib import Path

if getattr(sys, 'frozen', False):
    root_path = Path(sys.executable).parent
else:
    root_path = Path(__file__).parent.parent
sys.path.append(str(root_path))

from services.payment_service import EXPENSE_PAYMENT_CONFIG
from UI.payment_form import open_payment_window


def expense_payments_out(parent=None):
    open_payment_window(EXPENSE_PAYMENT_CONFIG, parent=parent)


if __name__ == "__main__":
    expense_payments_out()
