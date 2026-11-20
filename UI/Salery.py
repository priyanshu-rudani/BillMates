"""
UI/Salery.py
------------
Staff / Salary Payment entry window.
Delegates to UI/payment_form.py for unified form layout and services/payment_service.py for business logic.
"""
from __future__ import annotations

import sys
from pathlib import Path

if getattr(sys, 'frozen', False):
    root_path = Path(sys.executable).parent
else:
    root_path = Path(__file__).parent.parent
sys.path.append(str(root_path))

from services.payment_service import SALARY_PAYMENT_CONFIG
from UI.payment_form import open_payment_window


def pay_salery_ui(parent=None):
    open_payment_window(SALARY_PAYMENT_CONFIG, parent=parent)


if __name__ == "__main__":
    pay_salery_ui()
