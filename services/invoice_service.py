"""
services/invoice_service.py
---------------------------
Shared invoice business logic for the Sales AND Purchase invoice windows.

"""

import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Callable, List, Optional, Union

from utilities.path_utils import get_client_id, read_ini
from core.database import get_db_connection, query_all
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
    window_title="Add New Invoice",
    price_label="Sale Price",
    invoice_types=("GST Sales", "Non-GST Sales"),
    default_invoice_type="GST Sales",
    gst_invoice_type="GST Sales",
    balance_sign=-1,
    payment_entity_type="Income",
    payment_category="Invoice Payment",
    invoices_table="Invoices",
    items_table="InvoiceItems",
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
            qty = float(self.qty)
            price = float(self.price)
            gst_rate = float(self.gst_rate or 0)
            discount = float(self.discount or 0)
        except ValueError:
            raise InvoiceError("Please enter valid quantity and price.", "Invalid Input")
        if qty <= 0:
            raise InvoiceError("Quantity must be greater than 0.", "Invalid Input")
        if price < 0:
            raise InvoiceError("Price cannot be negative.", "Invalid Input")
        if discount < 0 or discount > 100:
            raise InvoiceError("Discount must be between 0% and 100%.", "Invalid Input")
        if gst_rate < 0:
            raise InvoiceError("GST rate cannot be negative.", "Invalid Input")
        return calc_item(qty, price, gst_rate, discount)


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
class InvoiceRecord:
    """Loaded invoice record used to pre-populate edit form."""
    invoice_id: int
    invoice_no: int
    invoice_type: str
    date: str
    due_date: str
    client_id: int
    client_name: str
    client_contact: str
    client_gst: str
    total: float
    paid: float
    remaining: float
    remarks: str
    reference_no: str
    payment_type: str
    paid_status: str
    items: List[DraftItem] = field(default_factory=list)


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
        rows = query_all("SELECT name FROM Clients WHERE client_type = ?", (self.cfg.client_type,))
        return [r[0] for r in rows]

    def client_id(self, client_name: str) -> int:
        return get_client_id(str(client_name))

    def client_profile(self, client_name: str) -> ClientProfile:
        cid = self.client_id(client_name)
        rows = query_all("SELECT * FROM Clients WHERE client_type = ? AND name = ?",
                          (self.cfg.client_type, client_name))
        if not rows:
            raise InvoiceError(f"{self.cfg.client_label} not found.", "Error", "info")
        row = rows[0]
        # Column order: id, name, contact_no, gst, city, state, client_type
        contact = str(row[2] or "")
        contact_display = f"91+ {contact[:5]} {contact[5:]}" if len(contact) == 10 else "00+ 00000 00000"

        next_no = None
        if self.cfg.auto_invoice_no:
            res = query_all(f"SELECT MAX(invoice_no) FROM {self.cfg.invoices_table} WHERE client_id = ?", (cid,))
            last = res[0][0] if res and res[0] else None
            next_no = 1 if last is None else int(last) + 1
        return ClientProfile(cid, contact_display, row[3] or "", next_no)

    # ---- item search / lookup ----------------------------------------------
    def _suggest(self, col: str) -> List[str]:
        """Master + history + items already in the current draft (fresh on every call)."""
        c = self.cfg
        tables = tuple(c.item_history_tables)
        union = " UNION ".join(f"SELECT {col} AS v FROM {table}" for table in tables)
        values = {str(r[0]).strip() for r in query_all(f"SELECT DISTINCT v FROM ({union})")
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
        
        for table in c.item_history_tables:
            rows = query_all(f"SELECT item_code, item_name FROM {table} WHERE {by} = ? LIMIT 1", (value,))
            if rows:
                return ItemMaster(rows[0][0] or "", rows[0][1] or "", None)
        for item in self.draft.items:
            if getattr(item, by) == value:
                return ItemMaster(item.item_code, item.item_name, None)
        return None

    def item_by_code(self, code: str) -> Optional[ItemMaster]:
        return self._lookup("item_code", code)

    def item_by_name(self, name: str) -> Optional[ItemMaster]:
        return self._lookup("item_name", name)

    def invoice_exists(self, invoice_no: str, client_name: str, exclude_invoice_id: Optional[int] = None) -> bool:
        cid = self.client_id(client_name)
        if not invoice_no or not cid:
            return False
        if exclude_invoice_id is not None:
            res = query_all(f"SELECT COUNT(*) FROM {self.cfg.invoices_table} WHERE invoice_no = ? AND client_id = ? AND invoice_id != ?",
                             (invoice_no, cid, exclude_invoice_id))
        else:
            res = query_all(f"SELECT COUNT(*) FROM {self.cfg.invoices_table} WHERE invoice_no = ? AND client_id = ?",
                             (invoice_no, cid))
        return bool(res and res[0][0] > 0)

    def load_invoice(self, invoice_id_or_obj: Union[int, str, dict]) -> InvoiceRecord:
        """
        Loads an existing invoice and its line items, pre-populating self.draft.
        Accepts integer invoice_id, string invoice_id, or a dict containing:
          - {'invoice_id': id} OR
          - {'invoice_no': no, 'client_id': cid} OR
          - {'invoice_no': no, 'client_name': name}
        """
        c = self.cfg
        inv_id: Optional[int] = None
        inv_no: Optional[int] = None
        cid: Optional[int] = None

        if isinstance(invoice_id_or_obj, dict):
            if "invoice_id" in invoice_id_or_obj and invoice_id_or_obj["invoice_id"]:
                inv_id = int(invoice_id_or_obj["invoice_id"])
            elif "invoice_no" in invoice_id_or_obj:
                inv_no = int(invoice_id_or_obj["invoice_no"])
                if "client_id" in invoice_id_or_obj and invoice_id_or_obj["client_id"]:
                    cid = int(invoice_id_or_obj["client_id"])
                elif "client_name" in invoice_id_or_obj and invoice_id_or_obj["client_name"]:
                    cid = self.client_id(invoice_id_or_obj["client_name"])
        elif isinstance(invoice_id_or_obj, (int, str)):
            try:
                inv_id = int(str(invoice_id_or_obj).strip())
            except ValueError:
                raise InvoiceError("Invalid invoice identifier.", "Load Error")
        else:
            raise InvoiceError("Unsupported invoice identifier type.", "Load Error")

        if inv_id is not None:
            sql_header = f"""
                SELECT 
                    i.invoice_id, i.invoice_no, i.Invoice_type, i.date, i.due_date,
                    i.client_id, c.name, c.contact_no, c.gst,
                    COALESCE(i.total, 0.0), COALESCE(i.paid, 0.0), COALESCE(i.remaining, 0.0),
                    COALESCE(i.remarks, ''), COALESCE(i.reference_no, ''),
                    COALESCE(i.payment_type, 'Cash'), COALESCE(i.paid_status, 'Unpaid')
                FROM {c.invoices_table} i
                JOIN Clients c ON i.client_id = c.id
                WHERE i.invoice_id = ?
            """
            rows = query_all(sql_header, (inv_id,))
        elif inv_no is not None and cid is not None:
            sql_header = f"""
                SELECT 
                    i.invoice_id, i.invoice_no, i.Invoice_type, i.date, i.due_date,
                    i.client_id, c.name, c.contact_no, c.gst,
                    COALESCE(i.total, 0.0), COALESCE(i.paid, 0.0), COALESCE(i.remaining, 0.0),
                    COALESCE(i.remarks, ''), COALESCE(i.reference_no, ''),
                    COALESCE(i.payment_type, 'Cash'), COALESCE(i.paid_status, 'Unpaid')
                FROM {c.invoices_table} i
                JOIN Clients c ON i.client_id = c.id
                WHERE i.invoice_no = ? AND i.client_id = ?
            """
            rows = query_all(sql_header, (inv_no, cid))
        else:
            raise InvoiceError("Insufficient parameters to locate invoice.", "Load Error")

        if not rows:
            raise InvoiceError(f"Invoice not found in {c.invoices_table}.", "Not Found", "info")

        r = rows[0]
        rec_inv_id = int(r[0])
        rec_inv_no = str(r[1]) if r[1] is not None else ""
        rec_inv_type = r[2] or c.default_invoice_type
        rec_date = r[3] or ""
        rec_due_date = r[4] or ""
        rec_cid = int(r[5])
        rec_cname = r[6] or ""
        rec_contact = str(r[7] or "")
        rec_gst = r[8] or ""
        rec_total = float(r[9] or 0.0)
        rec_paid = float(r[10] or 0.0)
        rec_remaining = float(r[11] or 0.0)
        rec_remarks = r[12] or ""
        rec_ref = r[13] or ""
        rec_pay_type = r[14] or "Cash"
        rec_paid_status = r[15] or "Unpaid"

        contact_display = f"91+ {rec_contact[:5]} {rec_contact[5:]}" if len(rec_contact) == 10 else rec_contact

        sql_items = f"""
            SELECT 
                id, invoice_no, client_id, item_code, item_name, quantity,
                unit, price, subtotal, GST_Rate, taxes, discount_amount,
                discount_percent, Total
            FROM {c.items_table}
            WHERE invoice_no = ? AND client_id = ?
            ORDER BY id ASC
        """
        item_rows = query_all(sql_items, (rec_inv_no, rec_cid))

        self.draft.clear()
        self.draft._next_id = 1
        loaded_items = []
        for it in item_rows:
            code = str(it[3] or "")
            name = str(it[4] or "")
            qty = float(it[5] or 0.0)
            unit = str(it[6] or "QTY")
            price = float(it[7] or 0.0)
            subtotal = float(it[8] or 0.0)
            gst_rate = float(it[9] or 0.0)
            taxes = float(it[10] or 0.0)
            disc_amt = float(it[11] or 0.0)
            disc_pct = float(it[12] or 0.0)
            item_total = float(it[13] or 0.0)

            d = DraftItem(
                row_id=self.draft._next_id,
                item_code=code,
                item_name=name,
                qty=qty,
                unit=unit,
                price=price,
                subtotal=subtotal,
                gst_rate=gst_rate,
                taxes=taxes,
                discount_percent=disc_pct,
                discount_amount=disc_amt,
                total=item_total,
            )
            self.draft._next_id += 1
            self.draft.items.append(d)
            loaded_items.append(d)

        return InvoiceRecord(
            invoice_id=rec_inv_id,
            invoice_no=rec_inv_no,
            invoice_type=rec_inv_type,
            date=rec_date,
            due_date=rec_due_date,
            client_id=rec_cid,
            client_name=rec_cname,
            client_contact=contact_display,
            client_gst=rec_gst,
            total=rec_total,
            paid=rec_paid,
            remaining=rec_remaining,
            remarks=rec_remarks,
            reference_no=rec_ref,
            payment_type=rec_pay_type,
            paid_status=rec_paid_status,
            items=loaded_items,
        )

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
        return float(round(self.draft.total))

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
        st = query_all("SELECT state FROM Clients WHERE id = ?", (cid,))
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
    def save_invoice(self, f: InvoiceForm, invoice_id: Optional[int] = None) -> SaveResult:
        c = self.cfg
        inv_no = (f.invoice_no or "").strip()
        self._validate_header(inv_no, f.client_name, f.date)

        try:
            inv_date = datetime.strptime(f.date, DATE_FMT)
        except ValueError:
            raise InvoiceError(f"Date must be {DATE_FMT}.", "Invalid Date")
        due_date = (inv_date + timedelta(days=c.due_days)).strftime(DATE_FMT)

        cid = self.client_id(f.client_name)
        if not cid:
            raise InvoiceError(f"{c.client_label} '{f.client_name}' not found.", "Client Error")
        total = self.total()
        try:
            paid = float(f.amount_paid) if f.amount_paid else 0.0
        except ValueError:
            raise InvoiceError("Please enter valid paid amount.", "Invalid Input")
        if paid < 0:
            raise InvoiceError("Paid amount cannot be negative.", "Invalid Input")

        if len(self.draft) == 0:
            raise InvoiceError("Enter at least 1 Item to save the Invoice", "Save Error", "info")

        if self.invoice_exists(inv_no, f.client_name, exclude_invoice_id=invoice_id):
            return SaveResult("exists", "Invoice Exists", f"Invoice number {inv_no} already exists.")

        remarks = (f.remarks or "").strip() or " "
        reference = f.reference_no or " "
        remaining = round(total - paid, 2)
        status = payment_status(total, paid)

        with get_db_connection() as conn:
            cursor = conn.cursor()
            if invoice_id is not None:
                # Update mode: reverse previous impact and apply new
                cursor.execute(f"SELECT invoice_no, client_id, total, paid FROM {c.invoices_table} WHERE invoice_id = ?", (invoice_id,))
                old_row = cursor.fetchone()
                if not old_row:
                    raise InvoiceError(f"Invoice ID {invoice_id} not found.", "Not Found")
                old_inv_no, old_cid, old_total, old_paid = old_row
                old_total = float(old_total or 0.0)
                old_paid = float(old_paid or 0.0)
                old_net = old_total - old_paid
                new_net = total - paid

                # Reconcile client closing balance
                if old_cid == cid:
                    delta = new_net - old_net
                    if delta != 0.0:
                        cursor.execute("UPDATE Clients SET closing_bal = COALESCE(closing_bal, 0) + ? WHERE id = ?",
                                       (round(float(c.balance_sign * delta), 2), cid))
                else:
                    if old_net != 0.0:
                        cursor.execute("UPDATE Clients SET closing_bal = COALESCE(closing_bal, 0) - ? WHERE id = ?",
                                       (round(float(c.balance_sign * old_net), 2), old_cid))
                    if new_net != 0.0:
                        cursor.execute("UPDATE Clients SET closing_bal = COALESCE(closing_bal, 0) + ? WHERE id = ?",
                                       (round(float(c.balance_sign * new_net), 2), cid))

                # Update invoice header
                cursor.execute(f"""UPDATE {c.invoices_table}
                                  SET invoice_no = ?, Invoice_type = ?, date = ?, due_date = ?,
                                      client_id = ?, total = ?, paid = ?, remaining = ?,
                                      remarks = ?, reference_no = ?, payment_type = ?, paid_status = ?
                                  WHERE invoice_id = ?""",
                               (inv_no, f.invoice_type, f.date, due_date, cid, total, paid, remaining,
                                remarks, reference, f.payment_type, status, invoice_id))

                # Replace line items
                cursor.execute(f"DELETE FROM {c.items_table} WHERE invoice_no = ? AND client_id = ?",
                               (old_inv_no, old_cid))
                for d in self.draft.items:
                    cursor.execute(f"INSERT INTO {c.items_table} ({self._ITEM_COLS}) VALUES ({', '.join('?' * 13)})",
                                   self._row_values(inv_no, cid, d))

                # Synchronize initial payment entry in Payments table
                cursor.execute("""SELECT payment_id FROM Payments
                                  WHERE reference_no = ? AND entity_id = ? AND Expanse_type = ?""",
                               (str(old_inv_no), old_cid, c.payment_category))
                p_row = cursor.fetchone()
                if paid > 0:
                    if p_row:
                        cursor.execute("""UPDATE Payments
                                          SET entity_id = ?, entity_type = ?, date = ?, total_amount = ?,
                                              payment_mode = ?, reference_no = ?, Expanse_type = ?
                                          WHERE payment_id = ?""",
                                       (cid, c.payment_entity_type, f.date, paid, f.payment_type, str(inv_no), c.payment_category, p_row[0]))
                    else:
                        cursor.execute("""INSERT INTO Payments
                                          (entity_id, entity_type, date, total_amount, payment_mode, reference_no, Expanse_type)
                                          VALUES (?, ?, ?, ?, ?, ?, ?)""",
                                       (cid, c.payment_entity_type, f.date, paid, f.payment_type, str(inv_no), c.payment_category))
                else:
                    if p_row:
                        cursor.execute("DELETE FROM Payments WHERE payment_id = ?", (p_row[0],))

                self.draft.clear()
                return SaveResult("saved", "Invoice Updated", f"Invoice {inv_no} has been updated successfully.")

            else:
                # Creation mode
                cursor.execute(f"""INSERT INTO {c.invoices_table}
                              (invoice_no, Invoice_type, date, due_date, client_id, total, paid, remaining,
                               remarks, reference_no, payment_type, paid_status)
                              VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                          (inv_no, f.invoice_type, f.date, due_date, cid, total, paid, remaining,
                           remarks, reference, f.payment_type, status))

                for d in self.draft.items:
                    cursor.execute(f"INSERT INTO {c.items_table} ({self._ITEM_COLS}) VALUES ({', '.join('?' * 13)})",
                                  self._row_values(inv_no, cid, d))

                net_delta = total - paid
                if net_delta != 0.0:
                    cursor.execute("UPDATE Clients SET closing_bal = COALESCE(closing_bal, 0) + ? WHERE id = ?",
                                  (round(float(c.balance_sign * net_delta), 2), cid))

                if paid > 0:
                    cursor.execute("""INSERT INTO Payments
                                 (entity_id, entity_type, date, total_amount, payment_mode, reference_no, Expanse_type)
                                 VALUES (?, ?, ?, ?, ?, ?, ?)""",
                              (cid, c.payment_entity_type, f.date, paid, f.payment_type, str(inv_no), c.payment_category))

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