"""
UI/paymentIn.py
---------------
Customer / Client Payment In entry window.
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

from services.payment_service import CLIENT_PAYMENT_CONFIG
from UI.payment_form import open_payment_window


def customer_payment_in(parent=None):
    open_payment_window(CLIENT_PAYMENT_CONFIG, parent=parent)


if __name__ == "__main__":
    customer_payment_in()
