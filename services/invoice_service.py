"""
services/invoice_service.py
---------------------------
Shared invoice business logic for the Sales AND Purchase invoice windows.

* No tkinter imports -> UI-independent, unit-testable.
* Everything that differs between Sales and Purchase lives in `InvoiceConfig`.
* UI talks to `InvoiceService`; failures surface as `InvoiceError`
  (the UI decides how to display them).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Callable, List, Optional

from utilities.path_utils import fetch_data, run_query, get_client_id, read_ini
from utilities.invoice_generator import create_invoice

DATE_FMT = "%d/%m/%Y"


# =============================================================================
#  Configuration  (the ONLY place Sales and Purchase differ)
# =============================================================================
@dataclass(frozen=True)
class InvoiceConfig:
    """Every field without a default MUST be set by each config (no hidden sales defaults)."""
    name: str
    # --- party / labels ------------------------------------------------------
    client_label: str                 # "Client" / "Supplier"  (UI labels)
    client_type: str                  # value in Clients.client_type
    window_title: str
    price_label: str
    # --- invoice types -------------------------------------------------------
    invoice_types: tuple
    default_invoice_type: str
    gst_invoice_type: str             # the type that enables GST fields
    # --- accounting ----------------------------------------------------------
    balance_sign: int                 # -1: closing_bal -= total | +1: closing_bal += total
    payment_entity_type: str          # Payments.entity_type      ("Income"/"Expense")
    payment_category: str             # Payments.Expanse_type
    # --- storage (declared per config) ---------------------------------------
    invoices_table: str               # header table
    items_table: str                  # saved line items (needs discount_percent + discount_amount)
    items_master_table: str           # product master used for search / auto-fill
    item_history_tables: tuple        # extra tables mined for search suggestions
    price_column: Optional[str]       # master column used to auto-fill price (None -> don't fill)
    pdf_prefix: str
    # --- behaviour (generic defaults) ----------------------------------------
    max_items: int = 15
    due_days: int = 30
    auto_invoice_no: bool = True
    pdf_generator: Optional[Callable] = None   # fn(client_id, invoice_no, path)


SALES_CONFIG = InvoiceConfig(
    name="sales",
    client_label="Client",
    client_type="Client",
    window_title="Invoice",
    price_label="Sale Price",
    invoice_types=("GST Sales", "Non-GST Sales"),
    default_invoice_type="GST Sales",
    gst_invoice_type="GST Sales",
    balance_sign=-1,
    payment_entity_type="Income",
    payment_category="Invoice Payment",
    invoices_table="Invoices",
    items_table="InvoiceItems",
    items_master_table="Items",
    item_history_tables=("InvoiceItems",),
    price_column="price",
    pdf_prefix="INV",
)

PURCHASE_CONFIG = InvoiceConfig(
    name="purchase",
    client_label="Supplier",
    client_type="Supplier",
    window_title="Add New Purchase",
    price_label="Purchase Price",
    invoice_types=("GST Purchase", "Non-GST Purchase"),
    default_invoice_type="GST Purchase",
    gst_invoice_type="GST Purchase",
    balance_sign=-1,
    payment_entity_type="Expense",
    payment_category="Payment For Purchase",
    invoices_table="Purchase",
    items_table="PurchaseItems",
    items_master_table="Items",
    item_history_tables=("InvoiceItems", "PurchaseItems"),
    price_column=None,                # don't pre-fill the SALE price as a purchase price
    pdf_prefix="PUR",
)


# =============================================================================
#  Errors / DTOs
# =============================================================================
class InvoiceError(Exception):
    """Raised for validation / business-rule failures. UI shows it."""

    def __init__(self, message: str, title: str = "Error",
                 level: str = "error", clear_field: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.title = title
        self.level = level              # "error" | "info" | "warning"
        self.clear_field = clear_field  # e.g. "invoice_no" -> UI clears that field


@dataclass
class ItemAmounts:
    qty: float
    price: float
    gst_rate: float
    discount_percent: float
    subtotal: float
    discount_amount: float
    taxable: float
    gst_amount: float
    total: float


@dataclass
class ItemInput:
    """Raw (string) values straight from the UI entries."""
    item_code: str = ""
    item_name: str = ""
    unit: str = "QTY"
    qty: str = ""
    price: str = ""
    gst_rate: str = ""
    discount: str = ""              # percent

    def amounts(self) -> ItemAmounts:
        try:
            return calc_item(float(self.qty), float(self.price),
                             float(self.gst_rate or 0), float(self.discount or 0))
        except ValueError:
            raise InvoiceError("Please enter valid quantity and price.", "Invalid Input")


@dataclass
class DraftItem:
    """One unsaved line item (lives in memory until the invoice is saved)."""
    row_id: int
    item_code: str
    item_name: str
    qty: float
    unit: str
    price: float
    subtotal: float
    gst_rate: float
    taxes: float
    discount_percent: float
    discount_amount: float
    total: float

    @classmethod
    def build(cls, row_id: int, item: "ItemInput", a: "ItemAmounts") -> "DraftItem":
        return cls(row_id, item.item_code, item.item_name, a.qty, item.unit, a.price, a.subtotal,
                   a.gst_rate, a.gst_amount, a.discount_percent, a.discount_amount, a.total)


@dataclass
class InvoiceDraft:
    """In-memory replacement for the Dummy*Items tables."""
    items: List[DraftItem] = field(default_factory=list)
    _next_id: int = 1

    def add(self, item: "ItemInput", a: "ItemAmounts") -> DraftItem:
        d = DraftItem.build(self._next_id, item, a)
        self._next_id += 1
        self.items.append(d)
        return d

    def get(self, row_id) -> Optional[DraftItem]:
        row_id = int(row_id)
        return next((d for d in self.items if d.row_id == row_id), None)

    def replace(self, row_id, item: "ItemInput", a: "ItemAmounts") -> bool:
        row_id = int(row_id)
        for i, d in enumerate(self.items):
            if d.row_id == row_id:
                self.items[i] = DraftItem.build(row_id, item, a)
                return True
        return False

    def remove(self, row_id) -> None:
        row_id = int(row_id)
        self.items = [d for d in self.items if d.row_id != row_id]

    def clear(self) -> None:
        self.items.clear()

    def __len__(self) -> int:
        return len(self.items)

    @property
    def total(self) -> float:
        return sum(d.total for d in self.items)


@dataclass
class InvoiceSummary:
    sub_total: float = 0.0
    total: float = 0.0            # taxable + taxes, before round-off
    taxable: float = 0.0
    cgst: float = 0.0
    sgst: float = 0.0
    igst: float = 0.0
    round_off: float = 0.0
    grand_total: float = 0.0


@dataclass
class ClientProfile:
    client_id: int
    contact_display: str
    gst_no: str
    next_invoice_no: Optional[int]


@dataclass
class ItemMaster:
    item_code: str
    item_name: str
    price: Optional[float]


@dataclass
class InvoiceForm:
    invoice_no: str
    client_name: str
    invoice_type: str
    payment_type: str
    date: str
    amount_paid: str = ""
    remarks: str = ""
    reference_no: str = ""


@dataclass
class SaveResult:
    status: str        # "saved" | "exists"
    title: str
    message: str

    @property
    def ok(self) -> bool:
        return True    # both "saved" and "exists" are non-failures


@dataclass
class ExportTarget:
    client_id: int
    invoice_no: str
    filename: str


# =============================================================================
#  Pure helpers
# =============================================================================
def calc_item(qty: float, price: float, gst_rate: float, discount_percent: float) -> ItemAmounts:
    """Discount is a percentage; GST is charged on the discounted value."""
    qty, price = round(qty, 2), round(price, 2)
    gst_rate, discount_percent = round(gst_rate, 2), round(discount_percent, 2)
    subtotal = round(qty * price, 2)
    discount_amount = round(subtotal * discount_percent / 100, 2)
    taxable = round(subtotal - discount_amount, 2)
    gst_amount = round(taxable * gst_rate / 100, 2)
    total = round(taxable + gst_amount, 2)
    return ItemAmounts(qty, price, gst_rate, discount_percent,
                       subtotal, discount_amount, taxable, gst_amount, total)


def payment_status(total: float, paid: float) -> str:
    remaining = round(total - paid, 2)
    if remaining <= 0:
        return "Paid"
    if paid <= 0:
        return "Unpaid"
    return "Partially Paid"


# =============================================================================
#  Service
# =============================================================================
class InvoiceService:
    def __init__(self, config: InvoiceConfig):
        self.cfg = config
        self.draft = InvoiceDraft()   # one draft per window -> create one service per window

    # ---- lookups ------------------------------------------------------------
    def client_names(self) -> List[str]:
        rows = fetch_data("SELECT name FROM Clients WHERE client_type = ?", (self.cfg.client_type,))
        return [r[0] for r in rows]

    def client_id(self, client_name: str) -> int:
        return get_client_id(str(client_name))

    def client_profile(self, client_name: str) -> ClientProfile:
        cid = self.client_id(client_name)
        rows = fetch_data("SELECT * FROM Clients WHERE client_type = ? AND name = ?",
                          (self.cfg.client_type, client_name))
        if not rows:
            raise InvoiceError(f"{self.cfg.client_label} not found.", "Error", "info")
        row = rows[0]
        # Column order: id, name, contact_no, gst, city, state, client_type
        contact = str(row[2] or "")
        contact_display = f"91+ {contact[:5]} {contact[5:]}" if len(contact) == 10 else "00+ 00000 00000"

        next_no = None
        if self.cfg.auto_invoice_no:
            res = fetch_data(f"SELECT MAX(invoice_no) FROM {self.cfg.invoices_table} WHERE client_id = ?", (cid,))
            last = res[0][0] if res and res[0] else None
            next_no = 1 if last is None else int(last) + 1
        return ClientProfile(cid, contact_display, row[3] or "", next_no)

    # ---- item search / lookup ----------------------------------------------
    def _suggest(self, col: str) -> List[str]:
        """Master + history + items already in the current draft (fresh on every call)."""
        c = self.cfg
        tables = (c.items_master_table,) + tuple(c.item_history_tables)
        union = " UNION ".join(f"SELECT {col} AS v FROM {t}" for t in tables)
        values = {str(r[0]).strip() for r in fetch_data(f"SELECT DISTINCT v FROM ({union})")
                  if r[0] is not None and str(r[0]).strip()}
        values |= {getattr(d, col).strip() for d in self.draft.items if (getattr(d, col) or "").strip()}
        return sorted(values, key=str.lower)

    def item_codes(self) -> List[str]:
        return self._suggest("item_code")

    def item_names(self) -> List[str]:
        return self._suggest("item_name")

    def _lookup(self, by: str, value: str) -> Optional[ItemMaster]:
        """by: 'item_code' | 'item_name' (internal constants only)."""
        c = self.cfg
        value = (value or "").strip()
        if not value:
            return None
        price = c.price_column or "NULL"
        rows = fetch_data(f"SELECT item_code, item_name, {price} FROM {c.items_master_table} "
                          f"WHERE {by} = ? LIMIT 1", (value,))
        if rows:
            return ItemMaster(rows[0][0] or "", rows[0][1] or "", rows[0][2])
        for t in c.item_history_tables:
            rows = fetch_data(f"SELECT item_code, item_name FROM {t} WHERE {by} = ? LIMIT 1", (value,))
            if rows:
                return ItemMaster(rows[0][0] or "", rows[0][1] or "", None)
        for d in self.draft.items:
            if getattr(d, by) == value:
                return ItemMaster(d.item_code, d.item_name, None)
        return None

    def item_by_code(self, code: str) -> Optional[ItemMaster]:
        return self._lookup("item_code", code)

    def item_by_name(self, name: str) -> Optional[ItemMaster]:
        return self._lookup("item_name", name)

    def invoice_exists(self, invoice_no: str, client_name: str) -> bool:
        cid = self.client_id(client_name)
        if not invoice_no or not cid:
            return False
        res = fetch_data(f"SELECT COUNT(*) FROM {self.cfg.invoices_table} WHERE invoice_no = ? AND client_id = ?",
                         (invoice_no, cid))
        return res[0][0] > 0

    # ---- validation ---------------------------------------------------------
    def _validate_header(self, invoice_no: str, client_name: str, date_str: str) -> None:
        if not invoice_no:
            raise InvoiceError("Invoice Number cannot be empty.", "Error")
        if invoice_no == "0":
            raise InvoiceError("Invoice number Can not be 0", "Invoice No Error", "info", clear_field="invoice_no")
        if not client_name:
            raise InvoiceError(f"{self.cfg.client_label} Name cannot be empty.", "Error")
        if not date_str:
            raise InvoiceError("Date is required.", "Missing Data")

    # ---- draft (unsaved) items - held in memory, one draft per service instance ----
    def draft_items(self) -> List[DraftItem]:
        return list(self.draft.items)

    def get_draft_item(self, row_id) -> Optional[DraftItem]:
        return self.draft.get(row_id)

    def delete_item(self, row_id) -> None:
        self.draft.remove(row_id)

    def discard_draft(self) -> None:
        self.draft.clear()

    def save_item(self, invoice_no: str, client_name: str, date_str: str,
                  item: ItemInput, edit_row_id=None) -> str:
        """Add a new draft item or replace `edit_row_id`. Returns 'added' | 'updated'."""
        invoice_no = (invoice_no or "").strip()
        self._validate_header(invoice_no, client_name, date_str)
        a = item.amounts()

        if edit_row_id:
            if not self.draft.replace(edit_row_id, item, a):
                raise InvoiceError("Item no longer exists.", "Error")
            return "updated"

        if len(self.draft) >= self.cfg.max_items:
            raise InvoiceError(f"You can't add more then {self.cfg.max_items} items per invoice",
                               "Max Limit Reached", "info")
        self.draft.add(item, a)
        return "added"

    _ITEM_COLS = ("invoice_no, client_id, item_code, item_name, quantity, unit, price, subtotal, "
                  "discount_percent, discount_amount, GST_Rate, taxes, Total")

    @staticmethod
    def _row_values(invoice_no: str, cid: int, d: DraftItem) -> tuple:
        """Values in the same order as _ITEM_COLS."""
        return (invoice_no, cid, d.item_code, d.item_name, d.qty, d.unit, d.price, d.subtotal,
                d.discount_percent, d.discount_amount, d.gst_rate, d.taxes, d.total)

    # ---- totals -------------------------------------------------------------
    def total(self) -> float:
        return self.draft.total

    def remaining(self, paid_text: str) -> float:
        """total - paid. Raises ValueError if `paid_text` is not a number."""
        paid = float(paid_text) if paid_text else 0.0
        return self.total() - paid

    def summary(self, client_name: str) -> InvoiceSummary:
        cid = self.client_id(client_name)
        items = self.draft.items
        sub_total = sum(d.subtotal for d in items)
        discount = sum(d.discount_amount for d in items)
        taxes = sum(d.taxes for d in items)
        gross = sum(d.total for d in items)

        company_state = read_ini("PROFILE", "state")
        st = fetch_data("SELECT state FROM Clients WHERE id = ?", (cid,))
        client_state = st[0][0] if st else None

        taxable = sub_total - discount
        total = taxable + taxes
        if company_state == client_state:
            cgst = sgst = taxes / 2
            igst = 0.0
        else:
            igst = taxes
            cgst = sgst = 0.0
        round_off = round(total) - gross
        grand_total = total + round_off

        return InvoiceSummary(sub_total=sub_total, total=round(total, 2), taxable=round(taxable, 2),
                              cgst=round(cgst, 2), sgst=round(sgst, 2), igst=round(igst, 2),
                              round_off=round(round_off, 2), grand_total=round(grand_total, 2))

    # ---- save -----------------------------------------------------
    def save_invoice(self, f: InvoiceForm) -> SaveResult:
        c = self.cfg
        inv_no = (f.invoice_no or "").strip()
        self._validate_header(inv_no, f.client_name, f.date)

        try:
            inv_date = datetime.strptime(f.date, DATE_FMT)
        except ValueError:
            raise InvoiceError(f"Date must be {DATE_FMT}.", "Invalid Date")
        due_date = (inv_date + timedelta(days=c.due_days)).strftime(DATE_FMT)

        cid = self.client_id(f.client_name)
        total = self.total()
        try:
            paid = float(f.amount_paid) if f.amount_paid else 0.0
        except ValueError:
            raise InvoiceError("Please enter valid paid amount.", "Invalid Input")

        if len(self.draft) == 0:
            raise InvoiceError("Enter at least 1 Item to save the Invoice", "Save Error", "info")

        if self.invoice_exists(inv_no, f.client_name):
            return SaveResult("exists", "Invoice Exists", f"Invoice number {inv_no} already exists.")

        remarks = (f.remarks or "").strip() or " "
        reference = f.reference_no or " "
        remaining = total - paid

        run_query(f"""INSERT INTO {c.invoices_table}
                      (invoice_no, Invoice_type, date, due_date, client_id, total, paid, remaining,
                       remarks, reference_no, payment_type, paid_status)
                      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                  (inv_no, f.invoice_type, f.date, due_date, cid, total, paid, remaining,
                   remarks, reference, f.payment_type, payment_status(total, paid)))

        for d in self.draft.items:
            run_query(f"INSERT INTO {c.items_table} ({self._ITEM_COLS}) VALUES ({', '.join('?' * 13)})",
                      self._row_values(inv_no, cid, d))

        run_query("UPDATE Clients SET closing_bal = COALESCE(closing_bal, 0) + ? WHERE id = ?",
                  (float(c.balance_sign * total), cid))

        if paid > 0:
            run_query("""INSERT INTO Payments
                         (entity_id, entity_type, date, total_amount, payment_mode, reference_no, Expanse_type)
                         VALUES (?, ?, ?, ?, ?, ?, ?)""",
                      (cid, c.payment_entity_type, f.date, paid, f.payment_type, inv_no, c.payment_category))

        self.draft.clear()
        return SaveResult("saved", "Invoice Saved", f"Invoice {inv_no} has been saved successfully.")

    # ---- export -------------------------------------------------------------
    def prepare_export(self, invoice_no: str, client_name: str, date_str: str) -> ExportTarget:
        invoice_no = (invoice_no or "").strip()
        self._validate_header(invoice_no, client_name, date_str)
        cid = self.client_id(client_name)
        if cid == 0:
            raise InvoiceError("Client Id not found from name", "Missing Data")
        try:
            safe_date = datetime.strptime(date_str, DATE_FMT).strftime("%d-%m-%Y")
        except ValueError:
            raise InvoiceError(f"Date must be {DATE_FMT}.", "Invalid Date")
        safe_name = re.sub(r'[\\/:*?"<>|]', "_", client_name)
        filename = f"{self.cfg.pdf_prefix}{invoice_no.zfill(3)}_{safe_date}_{safe_name}.pdf"
        return ExportTarget(cid, invoice_no, filename)

    def generate_pdf(self, client_id: int, invoice_no: str, path: str) -> None:
        (self.cfg.pdf_generator or create_invoice)(client_id, invoice_no, path)