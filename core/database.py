"""
core/database.py
----------------
Centralized SQLite database connection handling and query helpers.
Separates data access from UI and path manipulation.
"""

import logging
import os
import sqlite3
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Generator, List, Optional, Sequence, Tuple

logger = logging.getLogger(__name__)


def get_root_path() -> Path:
    """Returns the application root path."""
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    return Path(__file__).parent.parent


def get_database_path(*path_parts: str) -> str:
    """Resolves cross-platform SQLite database path."""
    current_drive = os.path.splitdrive(os.getcwd())[0]
    if current_drive == "C:":
        appdata_dir = os.path.join(os.getenv('APPDATA', ''), 'BillMates')
        return os.path.join(appdata_dir, *path_parts)
    return str(get_root_path().joinpath("db", *path_parts))




REPORT_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_invoices_client_isodate ON Invoices (client_id, substr(date, 7, 4) || '-' || substr(date, 4, 2) || '-' || substr(date, 1, 2));",
    "CREATE INDEX IF NOT EXISTS idx_invoices_isodate ON Invoices (substr(date, 7, 4) || '-' || substr(date, 4, 2) || '-' || substr(date, 1, 2));",
    "CREATE INDEX IF NOT EXISTS idx_purchase_client_isodate ON Purchase (client_id, substr(date, 7, 4) || '-' || substr(date, 4, 2) || '-' || substr(date, 1, 2));",
    "CREATE INDEX IF NOT EXISTS idx_purchase_isodate ON Purchase (substr(date, 7, 4) || '-' || substr(date, 4, 2) || '-' || substr(date, 1, 2));",
    "CREATE INDEX IF NOT EXISTS idx_payments_entity_isodate ON Payments (entity_id, substr(date, 7, 4) || '-' || substr(date, 4, 2) || '-' || substr(date, 1, 2));",
    "CREATE INDEX IF NOT EXISTS idx_payments_isodate ON Payments (substr(date, 7, 4) || '-' || substr(date, 4, 2) || '-' || substr(date, 1, 2));",
    "CREATE INDEX IF NOT EXISTS idx_payments_types ON Payments (entity_type, Expanse_type);",
]

_indexes_verified = False

def _ensure_report_indexes(conn: sqlite3.Connection, db_name: str) -> None:
    global _indexes_verified
    if _indexes_verified or db_name != "clients.db":
        return
    try:
        for idx in REPORT_INDEXES:
            conn.execute(idx)
        _indexes_verified = True
    except Exception as exc:
        logger.warning("Could not create/verify report indexes: %s", exc)


@contextmanager
def get_db_connection(db_name: str = "clients.db") -> Generator[sqlite3.Connection, None, None]:
    """Context manager for SQLite connections with transaction management."""
    db_file = get_database_path(db_name)
    Path(db_file).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_file, timeout=30)
    _ensure_report_indexes(conn, db_name)
    try:
        yield conn
        conn.commit()
    except Exception as exc:
        conn.rollback()
        logger.exception("Database error occurred: %s", exc)
        raise exc
    finally:
        conn.close()


def query_all(
    sql: str,
    params: Sequence[Any] = (),
    db_name: str = "clients.db",
) -> List[Tuple]:
    """Executes a SELECT query and returns all matching rows."""
    if not sql or not sql.strip():
        return []
    with get_db_connection(db_name) as conn:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        return cursor.fetchall()


def query_one(
    sql: str,
    params: Sequence[Any] = (),
    db_name: str = "clients.db",
) -> Optional[Tuple]:
    """Executes a SELECT query and returns a single row (or None)."""
    if not sql or not sql.strip():
        return None
    with get_db_connection(db_name) as conn:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        return cursor.fetchone()


def execute_non_query(
    sql: str,
    params: Sequence[Any] = (),
    db_name: str = "clients.db",
    conn: Optional[sqlite3.Connection] = None,
) -> int:
    """
    Executes an INSERT, UPDATE, or DELETE query and returns the lastrowid or affected count.
    If an existing connection `conn` is provided, executes within that transaction.
    """
    if not sql or not sql.strip():
        return 0

    if conn is not None:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        return cursor.lastrowid or cursor.rowcount

    with get_db_connection(db_name) as connection:
        cursor = connection.cursor()
        cursor.execute(sql, params)
        return cursor.lastrowid or cursor.rowcount


def execute_query(
    sql: str,
    params: Sequence[Any] = (),
    db_name: str = "clients.db",
    conn: Optional[sqlite3.Connection] = None,
) -> List[Tuple]:
    """Executes a SELECT query within an optional existing transaction `conn`."""
    if not sql or not sql.strip():
        return []

    if conn is not None:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        return cursor.fetchall()

    return query_all(sql, params, db_name=db_name)
