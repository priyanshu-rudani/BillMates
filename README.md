# BillMates Billing Software

> A modern desktop billing and business analytics application built with Python and Tkinter.

---

## Overview

BillMates is a full-featured desktop billing system designed for small-to-medium businesses. It manages sales invoices, purchase orders, client ledgers, payments, expenses, and cheque books — all backed by a local SQLite database with zero cloud dependency. The application launches with a polished analytics dashboard that gives an at-a-glance view of your business health, and every report can be exported as a PDF.

---

## Key Features

| Area                    | Capabilities                                                                                                                                                                    |
| ----------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Dashboard**           | KPI summary cards (Sales, COGS, Purchases, Expenditure), Revenue vs Expenses line chart, Expense Distribution donut chart, Quick Actions, Recent Activity feed, MoM growth card |
| **Invoicing**           | Create, edit, and print GST-compliant sales invoices with line items, tax rates, and discount support; PDF generation via ReportLab                                             |
| **Purchases**           | Record supplier purchase orders with the same invoice workflow                                                                                                                  |
| **Clients**             | Add, search, and manage customers and suppliers; track opening/closing balances and positions                                                                                   |
| **Payments**            | Record receipts and payments against clients or standalone expenses                                                                                                             |
| **Expenses**            | Categorise and track business expenses (Marketing, Maintenance, Loan Interest, Rent, Utilities, etc.)                                                                           |
| **Cheque Management**   | Maintain cheque books, issue cheques, and track cheque status (Pending / Cleared / Bounced)                                                                                     |
| **Reports**             | Date-ranged PDF reports for sales, purchases, payments, and expense summaries                                                                                                   |
| **Configuration**       | First-run company setup wizard; settings stored in `config.ini` — no manual editing required                                                                                    |
| **PyInstaller Support** | Frozen-binary-safe path resolution (`sys._MEIPASS`) and Matplotlib temp-dir handling                                                                                            |

---

## Project Structure

```
Source Code/
├── main.py                  # Entry point
├── core/
│   ├── environment.py       # First-run flow and app bootstrap
│   ├── database.py          # SQLite connection helpers (query_all, query_one, execute_non_query)
│   ├── db_creater.py        # Schema definitions and CREATE TABLE DDL
│   └── requirements.txt     # Python package dependencies
├── UI/
│   ├── Dashboard.py         # Main App window
│   ├── dashboard/           # Dashboard sub-modules
│   │   ├── theme.py         # Centralised colour palette and fonts
│   │   ├── sidebar.py       # Navigation sidebar
│   │   ├── header.py        # Top header / welcome banner
│   │   ├── widgets.py       # KPI cards, quick-action buttons, activity feed
│   │   ├── charts.py        # Matplotlib charts (line, donut) embedded via FigureCanvasTkAgg
│   │   ├── data_provider.py # All dashboard SQL queries
│   │   ├── graphics.py      # Decorative canvas graphics
│   │   └── loader.py        # Animated splash / loader screen
│   ├── Add_Invoice.py       # Sales invoice form
│   ├── addClient.py         # Add / edit client form
│   ├── add_company.py       # First-run company setup form
│   ├── Manage_Invoices.py   # Invoice list and management
│   ├── Manage_clients.py    # Client list and management
│   ├── Manage_Payments.py   # Payment list and management
│   ├── payment_form.py      # Payment entry form
│   ├── Reports.py           # Report generation UI
│   ├── Manage_Cheques.py    # Cheque management
│   └── ...                  # Other UI modules
├── utilities/
│   ├── path_utils.py        # Cross-platform path helpers, INI read/write
│   ├── GenerateReport.py    # Excel report generation (openpyxl)
│   ├── report_pdf_generator.py  # PDF report generation (ReportLab)
│   └── invoice_generator.py     # PDF invoice generation (ReportLab)
├── services/                # Business-logic services
├── assets/                  # Icons, images, and UI assets
├── db/                      # Local database storage (non-C: drives)
│   └── config.ini           # App configuration (auto-generated on first run)
└── .venv/                   # Virtual environment (not committed)
```

---

## Prerequisites

- **Python 3.11 or newer** (developed and tested on Python 3.14)
- **pip** (bundled with Python)
- **Windows** (Tkinter GUI; macOS/Linux not tested)
- **Git** (for cloning)

---

## Installation

```powershell
# 1. Clone the repository
git clone https://github.com/priyanshu-rudani/BillMates.git
cd "BillMates\Source Code"

# 2. Create and activate a virtual environment
python -m venv .venv
.\.venv\Scripts\activate

# 3. Install dependencies
pip install -r core\requirements.txt

# 4. Launch the application
python main.py
```

---

## Dependencies

Listed in [`core/requirements.txt`](core/requirements.txt):

| Package        | Version | Purpose                           |
| -------------- | ------- | --------------------------------- |
| `pillow`       | ≥ 12.0  | Image loading and rendering       |
| `matplotlib`   | ≥ 3.10  | Embedded charts (line, donut)     |
| `reportlab`    | ≥ 4.4   | PDF invoice and report generation |
| `openpyxl`     | ≥ 3.1   | Excel report export               |
| `tkcalendar`   | ≥ 1.6   | Date picker widgets               |
| `qrcode`       | ≥ 8.2   | QR code generation on invoices    |
| `num2words`    | ≥ 0.5   | Amount in words on invoices       |
| `PyCryptodome` | ≥ 3.24  | Data encryption utilities         |

> **Note:** `tkinter` and `sqlite3` are part of the Python standard library and do not need to be installed separately.

---

## First-Run Setup

On the **very first launch**, BillMates detects that no company has been configured and automatically opens a **Company Setup** wizard. Fill in your business details (name, address, GST number, etc.) and click **Save**. This action:

1. Creates `config.ini` with your `[PROFILE]`, `[BACKUP]`, and `[POLICY]` settings.
2. Initialises two SQLite databases:
   - `clients.db` — Clients, Invoices, InvoiceItems, Purchase, PurchaseItems, Payments tables.
   - `Cheque.db` — ChequeBook and Cheques tables.
3. Opens the main application dashboard.

Subsequent launches skip the wizard and go straight to the dashboard.

---

## Configuration

BillMates does **not** use a `.env` file. All configuration is stored in `config.ini`, which is written automatically by the app. You should not need to edit it manually.

**Database / config file location:**

| Scenario                         | Location               |
| -------------------------------- | ---------------------- |
| Running from a **C: drive**      | `%APPDATA%\BillMates\` |
| Running from **any other drive** | `<project-root>\db\`   |

**`config.ini` sections:**

```ini
[PROFILE]
# Company name, address, GST, financial year, etc.

[BACKUP]
# Backup path and schedule settings

[POLICY]
# Invoice numbering, discount, and payment policy settings
```

---

## Usage

After setup, the application opens in **full-screen** mode.

### Navigation

Use the **sidebar** on the left to switch between modules:

| Sidebar Item | Function                               |
| ------------ | -------------------------------------- |
| Dashboard    | Business analytics overview            |
| Invoice      | Create and manage sales invoices       |
| Clients      | Manage customers and suppliers         |
| Payments     | Record payments and receipts           |
| Expense      | Record and categorise expenses         |
| Reports      | Generate and export PDF reports        |
| Cheques      | Manage cheque books and issued cheques |
| Settings     | Company profile and app settings       |

### Quick Actions (Dashboard)

| Button             | Action                           |
| ------------------ | -------------------------------- |
| **Create Invoice** | Opens the new sales invoice form |
| **Add Client**     | Opens the add client form        |
| **Record Payment** | Opens the payment entry form     |
| **View Reports**   | Opens the reports module         |

---

## Database Schema (Summary)

```
clients.db
├── Clients          (id, name, contact_no, gst, city, state, client_type, opening_balance, closing_bal, position)
├── Invoices         (invoice_id, invoice_no, date, due_date, client_id, total, paid, remaining, payment_type, paid_status, …)
├── InvoiceItems     (id, invoice_no, client_id, item_code, item_name, quantity, unit, price, subtotal, GST_Rate, taxes, discount, …)
├── Purchase         (same structure as Invoices)
├── PurchaseItems    (same structure as InvoiceItems)
└── Payments         (payment_id, entity_id, entity_type, date, total_amount, payment_mode, reference_no, Expanse_type, …)

Cheque.db
├── ChequeBook       (id, book_name, bank_name, holder_name, account_no, starting_ChequeNo, Current_ChequeNo, total_cheques, …)
└── Cheques          (id, cheque_book_id, Cheque_No, Cheque_Date, Cheque_Type, Payee_name, Amount, Statues)
```

---

## Contributing

1. Fork the repository and create a feature branch off `code-improvement`.
2. Follow the existing module structure — keep UI, data access, and business logic in separate layers.
3. Test on a fresh virtual environment before submitting a pull request.

---

## Acknowledgements

Built with [Python](https://python.org), [Tkinter](https://docs.python.org/3/library/tkinter.html), [Matplotlib](https://matplotlib.org), [ReportLab](https://www.reportlab.com), and [Pillow](https://python-pillow.org).
