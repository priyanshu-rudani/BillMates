import sys
import os
from pathlib import Path

if getattr(sys, 'frozen', False):  # Running as a PyInstaller EXE
    root_path = Path(sys.executable).parent
else:  # Running as a Python script
    root_path = Path(__file__).parent.parent
sys.path.append(str(root_path))
 
from utilities.path_utils import *
import sqlite3

def create_database():
    try:
        db_path = database_path("clients.db")
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        connection = sqlite3.connect(db_path)  
        cursor = connection.cursor()

        cursor.execute("""
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
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,    
                item_code TEXT, 
                item_name TEXT NOT NULL, 
                price REAL DEFAULT 0, 
                mrp REAL DEFAULT 0, 
                discount REAL DEFAULT 0,
                gst INTEGER DEFAULT 0
            )
        """)   
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Payments (
                payment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_id INTEGER NOT NULL,
                entity_type TEXT NOT NULL,
                date DATE NOT NULL,
                total_amount REAL NOT NULL,
                payment_mode TEXT NOT NULL,
                reference_no TEXT,
                Expanse_type TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (entity_id) REFERENCES Clients(id) ON DELETE CASCADE
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Invoices (
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
        """)

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS DummyInvoiceItems (
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
                discount REAL NOT NULL,
                Total REAL NOT NULL,
                FOREIGN KEY (invoice_no) REFERENCES Invoices(invoice_no),
                FOREIGN KEY (client_id) REFERENCES Clients(id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS InvoiceItems (
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
                discount REAL NOT NULL,
                Total REAL NOT NULL,
                FOREIGN KEY (invoice_no) REFERENCES Invoices(invoice_no),
                FOREIGN KEY (client_id) REFERENCES Clients(id)
            )
            ''')
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS Purchase (
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
        """)

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS PurchaseItems (
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
                discount REAL NOT NULL,
                Total REAL NOT NULL,
                FOREIGN KEY (invoice_no) REFERENCES Purchase(invoice_no),
                FOREIGN KEY (client_id) REFERENCES Clients(id)
            )
            ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS DummyPurchaseItems (
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
                discount REAL NOT NULL,
                Total REAL NOT NULL,
                FOREIGN KEY (invoice_no) REFERENCES Purchase(invoice_no),
                FOREIGN KEY (client_id) REFERENCES Clients(id)
            )
        ''')
        
        connection.commit()
        connection.close()

    except sqlite3.Error as e:
        # Handle SQLite-related errors
        messagebox.showerror("DB Connection error", f"SQLite error occurred: {e}")
        
    except Exception as e:
        # Handle any other general errors
        messagebox.showerror("Unexpected Error", f"Unexpected error: {e}")

# ================
# Cheque database
# ================

    try:
        db_path = database_path("Cheque.db")
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        connection = sqlite3.connect(db_path)  
        cursor = connection.cursor()

        cursor.execute("""
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
        """)

        cursor.execute("""
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
        """)
        
        connection.commit()
        connection.close()

    except sqlite3.Error as e:
        # Handle SQLite-related errors
        messagebox.showerror("DB Connection error", f"SQLite error occurred: {e}")
        
    except Exception as e:
        # Handle any other general errors
        messagebox.showerror("Unexpected Error", f"Unexpected error: {e}")

if __name__ == "__main__":
    create_database()
