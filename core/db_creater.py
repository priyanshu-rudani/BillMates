import sys
import os
import logging
from pathlib import Path

if getattr(sys, 'frozen', False):  # Running as a PyInstaller EXE
    root_path = Path(sys.executable).parent
else:  # Running as a Python script
    root_path = Path(__file__).parent.parent
sys.path.append(str(root_path))

from utilities.path_utils import _show_error
from core.database import get_database_path
import sqlite3

try:
    from tkinter import messagebox
except ImportError:                  # headless / no Tk available
    messagebox = None

logger = logging.getLogger(__name__)


# =============================================================================
# Errors
# =============================================================================
class DatabaseInitError(Exception):
    """Raised when a database could not be initialized."""


# =============================================================================
# Schema templates (shared by Sales / Purchase, structure unchanged)
# =============================================================================
_INVOICE_DDL = """
    CREATE TABLE IF NOT EXISTS {table} (
        invoice_id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_no INTEGER NOT NULL,
        Invoice_type TEXT,
        date TEXT,
        due_date TEXT,
        client_id INTEGER NOT NULL,
        total REAL,
        paid REAL,
        remaining REAL,
        remarks TEXT,
        reference_no TEXT,
        payment_type TEXT,
        paid_status TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (client_id) REFERENCES Clients(id) ON DELETE CASCADE,
        UNIQUE(invoice_no, client_id)
    )
"""

_INVOICE_ITEMS_DDL = """
    CREATE TABLE IF NOT EXISTS {table} (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_no INTEGER NOT NULL,
        client_id INTEGER NOT NULL,
        item_code TEXT NOT NULL,
        item_name TEXT NOT NULL,
        quantity REAL NOT NULL,
        unit TEXT NOT NULL,
        price REAL NOT NULL,
        subtotal REAL NOT NULL,
        GST_Rate TEXT NOT NULL,
        taxes REAL NOT NULL,
        discount_amount REAL NOT NULL,
        discount_percent REAL NOT NULL,
        Total REAL NOT NULL,
        FOREIGN KEY (invoice_no) REFERENCES {parent}(invoice_no),
        FOREIGN KEY (client_id) REFERENCES Clients(id)
    )
"""

# =============================================================================
# Schema registry: {db_file: {table_name: ddl}}  (order = creation order)
# Add a table / database here only.
# =============================================================================
CLIENTS_SCHEMA = {
    "Clients": """
        CREATE TABLE IF NOT EXISTS Clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            contact_no TEXT NOT NULL,
            gst TEXT,
            city TEXT NOT NULL,
            state TEXT NOT NULL,
            client_type TEXT NOT NULL,
            opening_balance REAL DEFAULT 0,
            closing_bal REAL DEFAULT 0
        )
    """,
    "Payments": """
        CREATE TABLE IF NOT EXISTS Payments (
            payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            entity_id INTEGER,
            entity_type TEXT NOT NULL,
            date DATE NOT NULL,
            total_amount REAL NOT NULL,
            payment_mode TEXT NOT NULL,
            reference_no TEXT,
            Expanse_type TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (entity_id) REFERENCES Clients(id) ON DELETE CASCADE
        )
    """,
    "Invoices":      _INVOICE_DDL.format(table="Invoices"),
    "InvoiceItems":  _INVOICE_ITEMS_DDL.format(table="InvoiceItems", parent="Invoices"),
    "Purchase":      _INVOICE_DDL.format(table="Purchase"),
    "PurchaseItems": _INVOICE_ITEMS_DDL.format(table="PurchaseItems", parent="Purchase"),
}

CHEQUE_SCHEMA = {
    "ChequeBook": """
        CREATE TABLE IF NOT EXISTS ChequeBook (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_name TEXT NOT NULL,
            bank_name TEXT NOT NULL,
            holder_name TEXT NOT NULL,
            account_no TEXT NOT NULL,
            starting_ChequeNo INT NOT NULL,
            Current_ChequeNo INT NOT NULL,
            total_cheques INT NOT NULL,
            issued_date DATE NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """,
    "Cheques": """
        CREATE TABLE IF NOT EXISTS Cheques (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cheque_book_id INTEGER,
            Cheque_No INTEGER,
            Cheque_Date TEXT,
            Cheque_Type TEXT,
            Payee_name TEXT,
            Amount REAL DEFAULT 0,
            Statues TEXT DEFAULT "Pending",
            FOREIGN KEY (cheque_book_id) REFERENCES ChequeBook(id) ON DELETE CASCADE
        );
    """,
}

DATABASES = {
    "clients.db": CLIENTS_SCHEMA,
    "Cheque.db":  CHEQUE_SCHEMA,
}

REPORT_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_invoices_client_isodate ON Invoices (client_id, substr(date, 7, 4) || '-' || substr(date, 4, 2) || '-' || substr(date, 1, 2));",
    "CREATE INDEX IF NOT EXISTS idx_invoices_isodate ON Invoices (substr(date, 7, 4) || '-' || substr(date, 4, 2) || '-' || substr(date, 1, 2));",
    "CREATE INDEX IF NOT EXISTS idx_purchase_client_isodate ON Purchase (client_id, substr(date, 7, 4) || '-' || substr(date, 4, 2) || '-' || substr(date, 1, 2));",
    "CREATE INDEX IF NOT EXISTS idx_purchase_isodate ON Purchase (substr(date, 7, 4) || '-' || substr(date, 4, 2) || '-' || substr(date, 1, 2));",
    "CREATE INDEX IF NOT EXISTS idx_payments_entity_isodate ON Payments (entity_id, substr(date, 7, 4) || '-' || substr(date, 4, 2) || '-' || substr(date, 1, 2));",
    "CREATE INDEX IF NOT EXISTS idx_payments_isodate ON Payments (substr(date, 7, 4) || '-' || substr(date, 4, 2) || '-' || substr(date, 1, 2));",
    "CREATE INDEX IF NOT EXISTS idx_payments_types ON Payments (entity_type, Expanse_type);",
]


# =============================================================================
# Core (reusable)
# =============================================================================
def _init_database(db_file: str, tables: dict) -> None:
    """
    Create all `tables` in `db_file` inside ONE transaction (all-or-nothing).
    Raises DatabaseInitError with db/table context on failure.
    """
    current = "<connect>"
    conn = None
    try:
        db_path = Path(get_database_path(db_file))
        db_path.parent.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(db_path, timeout=30)

        try:
            for current, ddl in tables.items():
                conn.execute(ddl)

            if db_file == "clients.db":
                for idx_sql in REPORT_INDEXES:
                    conn.execute(idx_sql)

            conn.commit()
        except BaseException:
            try:
                if conn.in_transaction:
                    conn.rollback()
            except Exception:
                pass
            raise

    except sqlite3.Error as e:
        raise DatabaseInitError(
            f"[{db_file}] SQLite error while creating '{current}': {e}"
        ) from e
    except OSError as e:
        raise DatabaseInitError(f"[{db_file}] File/folder error: {e}") from e
    except Exception as e:
        raise DatabaseInitError(f"[{db_file}] Unexpected error: {e}") from e
    finally:
        if conn is not None:
            conn.close()


def create_database() -> bool:
    """
    Create every database in DATABASES. Each DB is independent: one failing
    does not block the other. Returns True only if all succeeded.
    """
    errors = []
    for db_file, tables in DATABASES.items():
        try:
            _init_database(db_file, tables)
        except DatabaseInitError as e:
            errors.append(str(e))

    if errors:
        _show_error("DB Connection error", "\n\n".join(errors))
        return False
    return True


if __name__ == "__main__":
    sys.exit(0 if create_database() else 1)