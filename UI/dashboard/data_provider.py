"""
UI/dashboard/data_provider.py
-----------------------------
Live SQLite data access, aggregation, and formatting for the BillMates Dashboard UI.
Operates strictly on real database records via ReportRepository and core.database.
"""


from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from core.database import query_all
from services.report_service import ReportRepository
from utilities.path_utils import get_dates_between, read_ini


def get_financial_year_dates(ref_date: Optional[date] = None) -> Tuple[str, str, str]:
    """Return (start_ddmmyyyy, end_ddmmyyyy, label) for the Indian financial year."""
    today = ref_date or date.today()
    if today.month >= 4:
        start_yr, end_yr = today.year, today.year + 1
    else:
        start_yr, end_yr = today.year - 1, today.year
    return (
        date(start_yr, 4, 1).strftime("%d/%m/%Y"),
        date(end_yr, 3, 31).strftime("%d/%m/%Y"),
        f"{start_yr}-{end_yr}",
    )


def format_compact_currency(value: Any) -> str:
    """Format numeric amounts cleanly with commas."""
    try:
        num = float(value)
    except (TypeError, ValueError):
        return str(value)

    if abs(num - round(num)) < 0.05:
        return f"{int(round(num)):,}"
    return f"{num:,.1f}"


def _relative_time_label(date_str: str, created_at: Optional[str] = None) -> str:
    """Convert created_at timestamp or DD/MM/YYYY date into a human-readable relative label."""
    now = datetime.now()
    dt = None
    if created_at:
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
            try:
                dt = datetime.strptime(str(created_at)[:19], fmt)
                break
            except ValueError:
                pass
    if dt is not None:
        diff = now - dt
        secs = int(diff.total_seconds())
        if 0 <= secs < 3600:
            mins = max(1, secs // 60)
            return f"{mins} min ago"
        if 0 <= secs < 86400:
            hrs = max(1, secs // 3600)
            return f"{hrs} hr{'s' if hrs != 1 else ''} ago"
        days = diff.days
        if days == 1:
            return "Yesterday"
        if 1 < days <= 7:
            return f"{days} days ago"

    if date_str:
        try:
            d = datetime.strptime(date_str.strip(), "%d/%m/%Y").date()
            delta_days = (now.date() - d).days
            if delta_days == 0:
                return "Today"
            if delta_days == 1:
                return "Yesterday"
            if 1 < delta_days <= 30:
                return f"{delta_days} days ago"
            return d.strftime("%d %b %Y")
        except ValueError:
            pass
    return date_str or "Recently"


@dataclass
class DashboardSnapshot:
    company_name: str
    financial_year: str
    metrics: Dict[str, float]
    current_month_sales: float
    sales_trend_pct: Optional[float]
    cogs_trend_pct: Optional[float]
    purchase_trend_pct: Optional[float]
    expense_trend_pct: Optional[float]
    recent_activities: List[Dict[str, Any]]
    notifications: List[str]


class DashboardDataProvider:
    """Encapsulates all live SQLite queries required by the Dashboard UI."""

    def get_company_name(self) -> str:
        name = str(read_ini("PROFILE", "name") or "").strip()
        return name or "My Company"

    def get_snapshot(self) -> DashboardSnapshot:
        start_date, end_date, fy_label = get_financial_year_dates()
        company_name = self.get_company_name()
        metrics = ReportRepository.get_financial_dashboard_metrics(start_date, end_date)

        cur_sales, sales_pct, cogs_pct, pur_pct, exp_pct = self._compute_mom_trends()
        recent = self._fetch_recent_activities(limit=6)
        notifications = self._fetch_notifications(metrics, recent)

        return DashboardSnapshot(
            company_name=company_name,
            financial_year=fy_label,
            metrics=metrics,
            current_month_sales=cur_sales,
            sales_trend_pct=sales_pct,
            cogs_trend_pct=cogs_pct,
            purchase_trend_pct=pur_pct,
            expense_trend_pct=exp_pct,
            recent_activities=recent,
            notifications=notifications,
        )

    @staticmethod
    def _pct_delta(cur: float, prev: float) -> float:
        if prev > 0:
            return round(((cur - prev) / prev) * 100.0, 1)
        if cur > 0:
            return 100.0
        return 0.0

    def _compute_mom_trends(self) -> Tuple[float, Optional[float], Optional[float], Optional[float], Optional[float]]:
        today = date.today()
        cur_start = today.replace(day=1).strftime("%d/%m/%Y")
        cur_end = today.strftime("%d/%m/%Y")

        prev_end_dt = today.replace(day=1) - timedelta(days=1)
        prev_start_dt = prev_end_dt.replace(day=1)
        prev_start = prev_start_dt.strftime("%d/%m/%Y")
        prev_end = prev_end_dt.strftime("%d/%m/%Y")

        cur_m = ReportRepository.get_financial_dashboard_metrics(cur_start, cur_end)
        prev_m = ReportRepository.get_financial_dashboard_metrics(prev_start, prev_end)

        cur_sales = float(cur_m.get("total_sales", 0.0))
        return (
            cur_sales,
            self._pct_delta(cur_sales, float(prev_m.get("total_sales", 0.0))),
            self._pct_delta(float(cur_m.get("total_cogs", 0.0)), float(prev_m.get("total_cogs", 0.0))),
            self._pct_delta(float(cur_m.get("total_purchase", 0.0)), float(prev_m.get("total_purchase", 0.0))),
            self._pct_delta(float(cur_m.get("total_operating_expenses", 0.0)), float(prev_m.get("total_operating_expenses", 0.0))),
        )

    def _fetch_recent_activities(self, limit: int = 6) -> List[Dict[str, Any]]:
        activities: List[Tuple[str, Dict[str, Any]]] = []

        inv_rows = query_all(
            """
            SELECT i.invoice_no, c.name, i.date, i.created_at, i.total
            FROM Invoices i
            LEFT JOIN Clients c ON i.client_id = c.id
            ORDER BY i.invoice_id DESC LIMIT ?
            """,
            (limit,),
        )
        for inv_no, client_name, dt_str, created_at, total in inv_rows:
            sort_key = str(created_at or dt_str or "")
            party = f" — {client_name}" if client_name else ""
            activities.append((
                sort_key,
                {
                    "title": f"Sales Invoice #INV-{inv_no}{party} (Rs. {format_compact_currency(total)})",
                    "time": _relative_time_label(dt_str, created_at),
                    "color": "#16A34A",
                },
            ))

        pur_rows = query_all(
            """
            SELECT p.invoice_no, c.name, p.date, p.created_at, p.total
            FROM Purchase p
            LEFT JOIN Clients c ON p.client_id = c.id
            ORDER BY p.invoice_id DESC LIMIT ?
            """,
            (limit,),
        )
        for pur_no, supplier_name, dt_str, created_at, total in pur_rows:
            sort_key = str(created_at or dt_str or "")
            party = f" — {supplier_name}" if supplier_name else ""
            activities.append((
                sort_key,
                {
                    "title": f"Purchase #PUR-{pur_no}{party} (Rs. {format_compact_currency(total)})",
                    "time": _relative_time_label(dt_str, created_at),
                    "color": "#2563EB",
                },
            ))

        pay_rows = query_all(
            """
            SELECT p.entity_type, p.Expanse_type, COALESCE(c.name, p.Expanse_type, 'Party'),
                   p.date, p.created_at, p.total_amount
            FROM Payments p
            LEFT JOIN Clients c ON p.entity_id = c.id
            ORDER BY p.payment_id DESC LIMIT ?
            """,
            (limit,),
        )
        for etype, exp_type, party, dt_str, created_at, amt in pay_rows:
            sort_key = str(created_at or dt_str or "")
            amt_txt = format_compact_currency(amt)
            if etype == "Income":
                title = f"Payment received from {party} (Rs. {amt_txt})"
                color = "#16A34A"
            elif etype in ("Expense", "Salaries"):
                title = f"Expense: {exp_type or party} (Rs. {amt_txt})"
                color = "#F59E0B"
            else:
                title = f"{exp_type or etype}: {party} (Rs. {amt_txt})"
                color = "#5B5CE6"
            activities.append((
                sort_key,
                {
                    "title": title,
                    "time": _relative_time_label(dt_str, created_at),
                    "color": color,
                },
            ))

        activities.sort(key=lambda x: x[0], reverse=True)
        return [item for _, item in activities[:limit]]

    def _fetch_notifications(self, metrics: Dict[str, float], recent: List[Dict[str, Any]]) -> List[str]:
        notes: List[str] = []
        recv = metrics.get("accounts_receivable", 0.0)
        payb = metrics.get("accounts_payable", 0.0)
        if recv > 0:
            notes.append(f"Accounts receivable pending: Rs. {format_compact_currency(recv)}")
        if payb > 0:
            notes.append(f"Accounts payable due: Rs. {format_compact_currency(payb)}")
        for act in recent[:3]:
            notes.append(f"{act['title']} ({act['time']})")
        if not notes:
            notes.append("All ledgers are up to date. No pending alerts.")
        return notes

    def get_revenue_expense_series(self, days: int = 7) -> Tuple[List[str], List[float], List[float]]:
        """Return (labels, revenue_series, expense_series) from real Payments records."""
        end_dt = datetime.now()
        start_dt = end_dt - timedelta(days=days - 1)
        start_str = start_dt.strftime("%d/%m/%Y")
        end_str = end_dt.strftime("%d/%m/%Y")
        dates = get_dates_between(start_str, end_str) or []
        if not dates:
            return [], [], []

        placeholders = ", ".join(["?"] * len(dates))
        revenue_q = f"""
            SELECT date, COALESCE(SUM(total_amount), 0.0)
            FROM Payments
            WHERE (entity_type = 'Income' OR Expanse_type = 'Adjustment Credit')
              AND date IN ({placeholders})
            GROUP BY date
        """
        expenses_q = f"""
            SELECT date, COALESCE(SUM(total_amount), 0.0)
            FROM Payments
            WHERE (entity_type IN ('Expense', 'Salaries') OR Expanse_type = 'Adjustment Debit')
              AND date IN ({placeholders})
            GROUP BY date
        """
        rev_map = dict(query_all(revenue_q, dates))
        exp_map = dict(query_all(expenses_q, dates))

        rev_vals = [float(rev_map.get(d, 0.0)) for d in dates]
        exp_vals = [float(exp_map.get(d, 0.0)) for d in dates]

        if days <= 7:
            labels = [(end_dt - timedelta(days=i)).strftime("%d") for i in range(days - 1, 1, -1)]
            if days >= 2:
                labels.extend(["Yesterday", "Today"])
            elif days == 1:
                labels = ["Today"]
            return labels, rev_vals, exp_vals

        bucket_size = 5 if days <= 30 else 15
        b_labels: List[str] = []
        b_rev: List[float] = []
        b_exp: List[float] = []
        for idx in range(0, len(dates), bucket_size):
            chunk_d = dates[idx : idx + bucket_size]
            b_labels.append(chunk_d[-1][:5])
            b_rev.append(sum(rev_vals[idx : idx + bucket_size]))
            b_exp.append(sum(exp_vals[idx : idx + bucket_size]))
        return b_labels, b_rev, b_exp

    def get_expense_distribution(self, period: str = "This Month") -> Tuple[List[str], List[float]]:
        """Return (labels, values) for the donut chart filtered by period."""
        today = date.today()
        if period == "This Month":
            start_dt = today.replace(day=1)
        elif period == "This Quarter":
            q_month = ((today.month - 1) // 3) * 3 + 1
            start_dt = today.replace(month=q_month, day=1)
        elif period == "Financial Year":
            fy_start_str, _, _ = get_financial_year_dates(today)
            start_dt = datetime.strptime(fy_start_str, "%d/%m/%Y").date()
        else:
            start_dt = date(2000, 1, 1)

        iso_start = start_dt.strftime("%Y-%m-%d")
        iso_end = today.strftime("%Y-%m-%d")

        query = """
            SELECT
                CASE WHEN Expanse_type = 'Other Expances' THEN 'Other Expenses' ELSE Expanse_type END AS category,
                COALESCE(SUM(total_amount), 0.0) AS total_expense
            FROM Payments
            WHERE Expanse_type IN ('Rent', 'Utilities', 'Maintenance', 'Marketing', 'Loan Interest', 'Taxes', 'Other Expances', 'Other Expenses')
              AND entity_type = 'Expense'
              AND (substr(date, 7, 4) || '-' || substr(date, 4, 2) || '-' || substr(date, 1, 2)) BETWEEN ? AND ?
            GROUP BY category
            ORDER BY total_expense DESC
        """
        rows = query_all(query, (iso_start, iso_end))
        labels = [str(r[0]) for r in rows if r[1] and float(r[1]) > 0]
        values = [float(r[1]) for r in rows if r[1] and float(r[1]) > 0]
        return labels, values

    def search_entities(self, query_text: str, limit: int = 8) -> List[Dict[str, str]]:
        """Search live clients, invoices, and purchases for the top search bar."""
        q = query_text.strip()
        if not q:
            return []
        like = f"%{q}%"
        results: List[Dict[str, str]] = []

        for name, ctype, city in query_all(
            "SELECT name, client_type, city FROM Clients WHERE name LIKE ? OR city LIKE ? LIMIT ?",
            (like, like, limit),
        ):
            results.append({"kind": ctype or "Client", "label": f"{name} ({city})", "action": "clients"})

        for inv_no, cname, total in query_all(
            """
            SELECT i.invoice_no, COALESCE(c.name, ''), COALESCE(i.total, 0.0)
            FROM Invoices i LEFT JOIN Clients c ON i.client_id = c.id
            WHERE CAST(i.invoice_no AS TEXT) LIKE ? OR c.name LIKE ?
            LIMIT ?
            """,
            (like, like, limit),
        ):
            results.append({"kind": "Invoice", "label": f"INV-{inv_no} • {cname} (Rs. {format_compact_currency(total)})", "action": "invoices"})

        for pur_no, sname, total in query_all(
            """
            SELECT p.invoice_no, COALESCE(c.name, ''), COALESCE(p.total, 0.0)
            FROM Purchase p LEFT JOIN Clients c ON p.client_id = c.id
            WHERE CAST(p.invoice_no AS TEXT) LIKE ? OR c.name LIKE ?
            LIMIT ?
            """,
            (like, like, limit),
        ):
            results.append({"kind": "Purchase", "label": f"PUR-{pur_no} • {sname} (Rs. {format_compact_currency(total)})", "action": "invoices"})

        return results[:limit]
