"""
UI/Dashboard.py
---------------
Main Billing & Analytics Dashboard application orchestrator (Overview only).
Operates exclusively on real SQLite database records and provides a clean,
spacious layout with conditional vertical scrolling for smaller viewports.
Preserves full compatibility with core.environment.EnvironmentSetup and
utilities.path_utils.Top_Close.
"""

import sys
import threading
import time
import tkinter as tk
from datetime import datetime, timedelta
from tkinter import ttk
from typing import Any, Dict, List, Optional

from UI.dashboard import (
    THEME,
    DashboardDataProvider,
    DashboardLoader,
    DashboardSidebar,
    ExpenseDistributionCard,
    GrowthPromoCard,
    KpiSummaryCard,
    QuickActionsCard,
    RecentActivitiesCard,
    RevenueExpensesChartCard,
    TopHeaderBar,
    WelcomeBanner,
    format_compact_currency,
    get_financial_year_dates,
    get_font,
    load_bundled_fonts,
)
from UI.gui import (
    Backup_ui,
    Manage_Cheques_ui,
    Manage_chequeBook_ui,
    PrintCheque_ui,
    Reports_ui,
    Restore_ui,
    addChequeBook_ui,
    company_info,
    customer_payment_in,
    expense_payments_out,
    manage_clients,
    manage_invoice_ui,
    manage_payments,
    new_adjustment_ui,
    new_client_ui,
    new_invoice_ui,
    new_purchase_ui,
    pay_salary_ui,
    payment_getway,
    supplier_payments_out,
    terms_conditions,
)
from utilities.path_utils import _show_error, center_window, generate_path, read_ini
from utilities.report_pdf_generator import export_pdf_report


def export_year_report(report_type: str, parent: tk.Misc = None) -> None:
    try:
        if report_type not in [
            "Revenue Reports",
            "Expense Analysis",
            "Cash Flow Statement",
            "Profit and Loss Statement",
        ]:
            return
        start_date, end_date, _ = get_financial_year_dates()
        export_pdf_report(
            report_type=report_type,
            start_date=start_date,
            end_date=end_date,
            parent_window=parent,
        )
    except Exception as exc:
        _show_error("Report Error", "An unexpected error occurred while generating the annual PDF report.", exc=exc)


def ask_backup_exit_choice(parent, title: str, message: str) -> str:
    """
    Shows a custom modal dialog on exit prompting for backup:
    Returns:
        "backup": User selected 'Backup Now'
        "exit": User selected 'Backup Later / Exit'
        "cancel": User closed or cancelled the prompt (stay in app)
    """
    choice = {"action": "cancel"}

    dialog = tk.Toplevel(parent)
    dialog.title(title)
    dialog.iconbitmap(generate_path("UI", "assets", "BillMates.ico"))
    dialog.transient(parent)
    dialog.configure(bg="#FBF6FF")
    center_window(dialog, 460, 220)
    dialog.resizable(False, False)

    # Header / Title area
    header_frame = tk.Frame(dialog, bg="#E7EBFF", height=50)
    header_frame.pack(fill="x", side="top")
    header_frame.pack_propagate(False)

    header_label = tk.Label(
        header_frame,
        text=f"  {message}",
        bg="#E7EBFF",
        fg="#151D48",
        font=("Poppins SemiBold", 13 * -1),
        anchor="w"
    )
    header_label.pack(side="left", padx=16, fill="both", expand=True)

    # Message Content
    body_frame = tk.Frame(dialog, bg="#FBF6FF")
    body_frame.pack(fill="both", expand=True, padx=22, pady=(15, 10))

    sub_label = tk.Label(
        body_frame,
        text="Would you like to backup your company data before closing?",
        bg="#FBF6FF",
        fg="#5E6366",
        font=("VarelaRound Regular", 11 * -1),
        wraplength=410,
        justify="left"
    )
    sub_label.pack(anchor="w", pady=(8, 0))

    # Action Buttons
    button_frame = tk.Frame(dialog, bg="#FBF6FF")
    button_frame.pack(fill="x", side="bottom", padx=20, pady=15)

    def select(action):
        choice["action"] = action
        try:
            dialog.grab_release()
        except Exception:
            pass
        dialog.destroy()

    # Cancel (Stay in App)
    btn_cancel = tk.Button(
        button_frame,
        text="Cancel",
        bg="#E2E8F0",
        fg="#334155",
        activebackground="#CBD5E1",
        activeforeground="#1E293B",
        font=("VarelaRound Regular", 11 * -1),
        bd=0,
        relief="flat",
        cursor="hand2",
        command=lambda: select("cancel"),
        padx=12,
        pady=6
    )
    btn_cancel.pack(side="left")

    # Backup Later & Exit
    btn_later = tk.Button(
        button_frame,
        text="Backup Later / Exit",
        bg="#F1F5F9",
        fg="#475569",
        activebackground="#E2E8F0",
        activeforeground="#1E293B",
        font=("VarelaRound Regular", 11 * -1),
        bd=1,
        relief="solid",
        cursor="hand2",
        command=lambda: select("exit"),
        padx=12,
        pady=6
    )
    btn_later.pack(side="right", padx=(8, 0))

    # Backup Now
    btn_backup = tk.Button(
        button_frame,
        text="Backup Now",
        bg="#4F59C1",
        fg="#FFFFFF",
        activebackground="#3F48A6",
        activeforeground="#FFFFFF",
        font=("VarelaRound Regular", 11 * -1),
        bd=0,
        relief="flat",
        cursor="hand2",
        command=lambda: select("backup"),
        padx=14,
        pady=6
    )
    btn_backup.pack(side="right")

    # Make strictly modal and take absolute focus
    dialog.update_idletasks()
    dialog.deiconify()
    dialog.lift()
    dialog.focus_force()
    btn_backup.focus_set()

    try:
        dialog.grab_set()
    except Exception:
        pass

    # Stop propagation of <Escape> so it only closes this dialog and doesn't re-trigger App's <Escape>
    def on_dialog_escape(event):
        select("cancel")
        return "break"

    dialog.bind("<Escape>", on_dialog_escape)
    dialog.protocol("WM_DELETE_WINDOW", lambda: select("cancel"))
    dialog.wait_window()

    return choice["action"]


def on_closing(root: tk.Misc) -> None:
    """Check backup status and exit the application cleanly."""
    try:
        root.config(cursor="watch")
        root.update_idletasks()

        last_backup_str = read_ini("BACKUP", "lastbackup")
        reminder_title = None
        reminder_msg = None

        if last_backup_str:
            try:
                last_backup_datetime = datetime.strptime(last_backup_str, "%d/%m/%Y : %H:%M:%S")
                if (datetime.now() - last_backup_datetime) > timedelta(days=30):
                    reminder_title = "Backup Reminder"
                    reminder_msg = f"It has been more than 30 days since your last backup ({last_backup_str})."
            except ValueError:
                reminder_title = "Backup Information Invalid"
                reminder_msg = "The recorded backup information is invalid or corrupted."
        else:
            reminder_title = "No Backup Found"
            reminder_msg = "No previous database backup was found for this system."

        if reminder_title:
            root.config(cursor="")
            action = ask_backup_exit_choice(root, reminder_title, reminder_msg)
            if action == "backup":
                Backup_ui(parent=root)
                return
            if action == "cancel":
                return

        root.config(cursor="")
        root.quit()
        sys.exit()
    finally:
        try:
            root.config(cursor="")
        except Exception:
            pass


class MainFrame(tk.Frame):
    """
    Scroll-aware responsive dashboard Overview workspace containing:
    - Welcome Banner
    - 5 KPI Summary Cards
    - Revenue & Expenses Overview + Expense Distribution Charts
    - Quick Actions, Recent Activities, and Sales Growth Card
    Preserves `Card_data()` and `reload_Charts()` for Top_Close compatibility.
    """

    def __init__(
        self,
        master: tk.Misc,
        app_root: tk.Misc,
        data_provider: DashboardDataProvider,
        preloaded: Optional[Dict[str, Any]] = None,
        **options,
    ):
        c = THEME["colors"]
        super().__init__(master, bg=c["app_bg"], **options)
        self.app_root = app_root
        self.data_provider = data_provider
        self._latest_snapshot = None
        self._scrollbar_visible = False

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)

        self._configure_scrollbar_style()

        self._scroll_canvas = tk.Canvas(self, bg=c["app_bg"], highlightthickness=0, bd=0)
        self._scroll_canvas.grid(row=0, column=0, sticky="nsew")

        self._v_scroll = ttk.Scrollbar(
            self,
            orient="vertical",
            command=self._scroll_canvas.yview,
            style="Dashboard.Vertical.TScrollbar",
        )
        self._scroll_canvas.configure(yscrollcommand=self._v_scroll.set)

        pad_x = THEME["spacing"]["outer_pad_x"]
        pad_y = THEME["spacing"]["outer_pad_y"]

        self._viewport = tk.Frame(self._scroll_canvas, bg=c["app_bg"])
        self._viewport.grid_rowconfigure(0, weight=1)
        self._viewport.grid_columnconfigure(0, weight=1)
        self._win_id = self._scroll_canvas.create_window(0, 0, anchor="nw", window=self._viewport)

        self._content_host = tk.Frame(self._viewport, bg=c["app_bg"])
        self._content_host.grid(row=0, column=0, sticky="nsew", padx=pad_x, pady=pad_y)
        self._content_host.grid_rowconfigure(0, weight=1)
        self._content_host.grid_columnconfigure(0, weight=1)

        self._build_overview_page()

        self._scroll_canvas.bind("<Configure>", self._sync_scroll_region)
        self._viewport.bind("<Configure>", self._sync_scroll_region)
        self.app_root.bind_all("<MouseWheel>", self._on_mousewheel, add="+")

        if preloaded:
            self.Card_data(snapshot=preloaded.get("snapshot"))
            self.reload_Charts(
                series=preloaded.get("series"),
                distribution=preloaded.get("distribution"),
            )
        else:
            self.Card_data()
            self.reload_Charts()
        self.after_idle(self._sync_scroll_region)

    def _configure_scrollbar_style(self) -> None:
        c = THEME["colors"]
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure(
            "Dashboard.Vertical.TScrollbar",
            background="#CBD5E1",
            troughcolor=c["app_bg"],
            bordercolor=c["app_bg"],
            arrowcolor=c["text_muted"],
            relief="flat",
            width=10,
        )
        style.map(
            "Dashboard.Vertical.TScrollbar",
            background=[("active", "#94A3B8")],
        )

    def _sync_scroll_region(self, _event=None) -> None:
        cw = self._scroll_canvas.winfo_width()
        ch = self._scroll_canvas.winfo_height()
        if cw < 50 or ch < 50:
            return

        req_h = self._viewport.winfo_reqheight()
        needs_scroll = req_h > ch + 2
        target_h = req_h if needs_scroll else ch

        self._scroll_canvas.itemconfigure(self._win_id, width=cw, height=target_h)
        self._scroll_canvas.configure(scrollregion=(0, 0, cw, target_h))

        if needs_scroll and not self._scrollbar_visible:
            self._v_scroll.grid(row=0, column=1, sticky="ns")
            self._scrollbar_visible = True
        elif not needs_scroll and self._scrollbar_visible:
            self._v_scroll.grid_remove()
            self._scroll_canvas.yview_moveto(0)
            self._scrollbar_visible = False

    def _on_mousewheel(self, event: tk.Event) -> None:
        if not self._scrollbar_visible:
            return
        try:
            if event.widget.winfo_toplevel() != self.app_root:
                return
        except Exception:
            return
        delta = -1 * (event.delta // 120) if event.delta else 0
        if delta != 0:
            self._scroll_canvas.yview_scroll(delta, "units")

    def _build_overview_page(self) -> None:
        c = THEME["colors"]
        gap = THEME["spacing"]["card_gap"]

        self.overview_page = tk.Frame(self._content_host, bg=c["app_bg"])
        self.overview_page.grid(row=0, column=0, sticky="nsew")

        self.overview_page.grid_rowconfigure(0, weight=0)
        self.overview_page.grid_rowconfigure(1, weight=0)
        self.overview_page.grid_rowconfigure(2, weight=1, minsize=310)
        self.overview_page.grid_rowconfigure(3, weight=0)
        self.overview_page.grid_columnconfigure(0, weight=1)

        # Row 0: Welcome Banner
        self.welcome_banner = WelcomeBanner(
            self.overview_page,
            company_name=self.data_provider.get_company_name(),
            fy_label=get_financial_year_dates()[2],
            height=118,
        )
        self.welcome_banner.grid(row=0, column=0, sticky="ew", pady=(0, gap))

        # Row 1: 5 Equal KPI Summary Cards
        kpi_row = tk.Frame(self.overview_page, bg=c["app_bg"])
        kpi_row.grid(row=1, column=0, sticky="ew", pady=(0, gap))
        for i in range(5):
            kpi_row.grid_columnconfigure(i, weight=1, uniform="kpi_col")
        kpi_row.grid_rowconfigure(0, weight=1)

        self.financial_year_card = KpiSummaryCard(
            kpi_row,
            title="Financial Year",
            value=get_financial_year_dates()[2],
            icon_name="trend_up",
            icon_fg=c["purple_icon"],
            icon_bg=c["purple_bg"],
            value_color=c["text_primary"],
            wave_color="#E3E1FD",
            show_calendar=True,
        )
        self.financial_year_card.grid(row=0, column=0, sticky="nsew", padx=(0, gap // 2))

        self.total_sales_card = KpiSummaryCard(
            kpi_row,
            title="Total Sales Revenue",
            value="0",
            icon_name="reports",
            icon_fg=c["success_bright"],
            icon_bg=c["success_bg"],
            value_color=c["success"],
            wave_color="#DCFCE7",
        )
        self.total_sales_card.grid(row=0, column=1, sticky="nsew", padx=gap // 2)

        self.total_cogs_card = KpiSummaryCard(
            kpi_row,
            title="Total COGS Amount",
            value="0",
            icon_name="wallet",
            icon_fg=c["danger"],
            icon_bg=c["danger_bg"],
            value_color=c["danger"],
            wave_color="#FEE2E2",
        )
        self.total_cogs_card.grid(row=0, column=2, sticky="nsew", padx=gap // 2)

        self.total_purchase_card = KpiSummaryCard(
            kpi_row,
            title="Total Purchases",
            value="0",
            icon_name="cart",
            icon_fg=c["info"],
            icon_bg=c["info_bg"],
            value_color=c["info"],
            wave_color="#DBEAFE",
        )
        self.total_purchase_card.grid(row=0, column=3, sticky="nsew", padx=gap // 2)

        self.total_expense_card = KpiSummaryCard(
            kpi_row,
            title="Total Expenditure",
            value="0",
            icon_name="expense",
            icon_fg=c["warning"],
            icon_bg=c["warning_bg"],
            value_color=c["warning"],
            wave_color="#FFEDD5",
        )
        self.total_expense_card.grid(row=0, column=4, sticky="nsew", padx=(gap // 2, 0))

        # Row 2: Charts Row (62% Left Line/Area Chart, 38% Right Donut Chart)
        charts_row = tk.Frame(self.overview_page, bg=c["app_bg"])
        charts_row.grid(row=2, column=0, sticky="nsew", pady=(0, gap))
        charts_row.grid_rowconfigure(0, weight=1)
        charts_row.grid_columnconfigure(0, weight=62, uniform="chart_col")
        charts_row.grid_columnconfigure(1, weight=38, uniform="chart_col")

        self.line_chart = RevenueExpensesChartCard(
            charts_row,
            fetch_series=self.data_provider.get_revenue_expense_series,
            on_open_reports=lambda: Reports_ui(parent=self.app_root),
        )
        self.line_chart.grid(row=0, column=0, sticky="nsew", padx=(0, gap // 2))

        self.pie_chart = ExpenseDistributionCard(
            charts_row,
            fetch_distribution=self.data_provider.get_expense_distribution,
        )
        self.pie_chart.grid(row=0, column=1, sticky="nsew", padx=(gap // 2, 0))

        # Row 3: Bottom 3 Cards (Quick Actions | Recent Activities | Sales Growth Card)
        bottom_row = tk.Frame(self.overview_page, bg=c["app_bg"])
        bottom_row.grid(row=3, column=0, sticky="ew")
        bottom_row.grid_rowconfigure(0, weight=1)
        bottom_row.grid_columnconfigure(0, weight=33, uniform="bot_col")
        bottom_row.grid_columnconfigure(1, weight=35, uniform="bot_col")
        bottom_row.grid_columnconfigure(2, weight=32, uniform="bot_col")

        self.quick_actions_card = QuickActionsCard(
            bottom_row,
            actions=[
                ("Create\nInvoice", "invoice", lambda: new_invoice_ui(parent=self.app_root)),
                ("Add Client", "users", lambda: new_client_ui(parent=self.app_root)),
                ("Record\nPayment", "payments", lambda: customer_payment_in(parent=self.app_root)),
                ("View Reports", "reports", lambda: Reports_ui(parent=self.app_root)),
            ],
        )
        self.quick_actions_card.grid(row=0, column=0, sticky="nsew", padx=(0, gap // 2))

        self.recent_activities_card = RecentActivitiesCard(
            bottom_row,
        )
        self.recent_activities_card.grid(row=0, column=1, sticky="nsew", padx=gap // 2)

        self.growth_card = GrowthPromoCard(bottom_row)
        self.growth_card.grid(row=0, column=2, sticky="nsew", padx=(gap // 2, 0))

    def refresh_all(self) -> None:
        self.Card_data()
        self.reload_Charts()

    def Card_data(self, snapshot=None) -> None:
        """Refresh all KPI cards, welcome banner, recent activities, and growth card."""
        snap = snapshot or self.data_provider.get_snapshot()
        self._latest_snapshot = snap
        c = THEME["colors"]
        m = snap.metrics

        self.welcome_banner.set_context(snap.company_name, snap.financial_year)
        if hasattr(self.app_root, "header"):
            self.app_root.header.set_company_name(snap.company_name)

        self.financial_year_card.update_metric(snap.financial_year)

        sales_val = m.get("total_sales", 0.0)
        self.total_sales_card.update_metric(
            format_compact_currency(sales_val),
            value_color=c["success"] if sales_val >= 0 else c["danger"],
            trend_pct=snap.sales_trend_pct,
        )

        cogs_val = m.get("total_cogs", 0.0)
        self.total_cogs_card.update_metric(
            format_compact_currency(cogs_val),
            value_color=c["danger"] if cogs_val != 0 else c["text_primary"],
            trend_pct=snap.cogs_trend_pct,
        )

        pur_val = m.get("total_purchase", 0.0)
        self.total_purchase_card.update_metric(
            format_compact_currency(pur_val),
            value_color=c["info"] if pur_val != 0 else c["text_primary"],
            trend_pct=snap.purchase_trend_pct,
        )

        exp_val = m.get("total_operating_expenses", 0.0)
        self.total_expense_card.update_metric(
            format_compact_currency(exp_val),
            value_color=c["warning"] if exp_val != 0 else c["text_primary"],
            trend_pct=snap.expense_trend_pct,
        )

        self.recent_activities_card.set_activities(snap.recent_activities)
        self.growth_card.update_sales_growth(snap.sales_trend_pct)

    def reload_Charts(self, series=None, distribution=None) -> None:
        """Re-query and re-render both matplotlib charts."""
        self.line_chart.refresh(preloaded=series)
        self.pie_chart.refresh(preloaded=distribution)


class App(tk.Tk):
    """Main desktop application window with animated startup loader."""

    def __init__(self, start_mainloop: bool = True, show_loader: bool = True):
        super().__init__()
        self.withdraw()
        load_bundled_fonts()

        c = THEME["colors"]
        self.geometry("1380x840")
        self.minsize(1160, 680)
        try:
            self.iconbitmap(generate_path("UI", "assets", "BillMates.ico"))
        except Exception:
            pass

        self.data_provider = DashboardDataProvider()
        company_name = self.data_provider.get_company_name()
        self.title(f"Dashboard - {company_name} (Admin) - BillMates")
        self.configure(bg=c["app_bg"])

        loader: Optional[DashboardLoader] = None
        if show_loader:
            loader = DashboardLoader(self)
            loader.set_progress(18, animate_ms=70)

        preloaded: Dict[str, Any] = {}
        fetch_errors: List[Exception] = []

        def _fetch_worker() -> None:
            try:
                preloaded["snapshot"] = self.data_provider.get_snapshot()
                preloaded["series"] = self.data_provider.get_revenue_expense_series(7)
                preloaded["distribution"] = self.data_provider.get_expense_distribution("This Month")
            except Exception as exc:
                fetch_errors.append(exc)

        try:
            if loader is not None:
                worker = threading.Thread(target=_fetch_worker, daemon=True)
                worker.start()
                deadline = time.monotonic() + 12.0
                while worker.is_alive():
                    if time.monotonic() > deadline:
                        raise TimeoutError("Timed out while loading database records.")
                    loader._progress = min(58.0, loader._progress + 1.5)
                    loader.tick()
                    time.sleep(0.02)
                worker.join()
                if fetch_errors:
                    raise fetch_errors[0]
                loader.set_progress(66, animate_ms=65)
            else:
                _fetch_worker()
                if fetch_errors:
                    raise fetch_errors[0]


            menu_data = self._build_menu_data()

            self.grid_rowconfigure(0, weight=1)
            self.grid_columnconfigure(0, weight=0)
            self.grid_columnconfigure(1, weight=1)

            self.sidebar = DashboardSidebar(
                self,
                menu_data=menu_data,
                on_dashboard=lambda: self.mainframe.refresh_all(),
            )
            self.sidebar.grid(row=0, column=0, sticky="ns")

            right_col = tk.Frame(self, bg=c["app_bg"])
            right_col.grid(row=0, column=1, sticky="nsew")
            right_col.grid_rowconfigure(0, weight=0)
            right_col.grid_rowconfigure(1, weight=1)
            right_col.grid_columnconfigure(0, weight=1)

            self.header = TopHeaderBar(
                right_col,
                company_name=company_name,
                on_search=self._handle_search,
                on_search_select=self._handle_search_select,
                on_edit_company=lambda: company_info("edit", parent=self),
                on_backup=lambda: Backup_ui(parent=self),
                on_refresh=lambda: self.mainframe.refresh_all(),
                get_notifications=self._get_notifications,
            )
            self.header.grid(row=0, column=0, sticky="ew")

            if loader is not None:
                loader.set_progress(86, animate_ms=65)

            self.mainframe = MainFrame(
                right_col,
                app_root=self,
                data_provider=self.data_provider,
                preloaded=preloaded,
            )
            self.mainframe.grid(row=1, column=0, sticky="nsew")

            self._bind_shortcuts()
            self.resizable(True, True)
            self.update_idletasks()
            self.mainframe._sync_scroll_region()

            if loader is not None:
                loader.set_progress(100, animate_ms=55)
        except Exception as exc:
            if loader is not None:
                loader.close()
                loader = None
            _show_error(
                "Startup Error",
                "Failed to load the dashboard. Please check the logs or database.",
                parent=self,
                exc=exc,
            )
            try:
                self.destroy()
            except Exception:
                pass
            raise
        finally:
            if loader is not None:
                loader.close()

        self.deiconify()
        if start_mainloop:
            self.attributes("-fullscreen", True)
        self.lift()
        self.update()

        if start_mainloop:
            self.mainloop()

    def _build_menu_data(self) -> List[Dict[str, Any]]:
        return [
            {
                "text": "Invoice",
                "commands": [
                    {"label": "Add Invoice (F1)", "command": lambda: new_invoice_ui(parent=self)},
                    {"label": "Add Purchase (F2)", "command": lambda: new_purchase_ui(parent=self)},
                    {"label": "Manage Invoices (F8)", "command": lambda: manage_invoice_ui(parent=self)},
                ],
            },
            {
                "text": "Clients",
                "commands": [
                    {"label": "Add Clients (F3)", "command": lambda: new_client_ui(parent=self)},
                    {"label": "Manage Clients (F9)", "command": lambda: manage_clients(parent=self)},
                ],
            },
            {
                "text": "Payments",
                "commands": [
                    {"label": "Add Invoice Payments (F4)", "command": lambda: customer_payment_in(parent=self)},
                    {"label": "Add Adjustment", "command": lambda: new_adjustment_ui(parent=self)},
                    {"label": "Payment Gateway", "command": lambda: payment_getway(parent=self)},
                    {"label": "Manage Payments (F7)", "command": lambda: manage_payments(parent=self)},
                ],
            },
            {
                "text": "Expense",
                "commands": [
                    {"label": "Add Purchase Payments (F5)", "command": lambda: supplier_payments_out(parent=self)},
                    {"label": "Add Expense Payments (F6)", "command": lambda: expense_payments_out(parent=self)},
                    {"label": "Add Salary Payments", "command": lambda: pay_salary_ui(parent=self)},
                    {"label": "Manage Payments (F7)", "command": lambda: manage_payments(parent=self)},
                ],
            },
            {
                "text": "Reports",
                "commands": [
                    {"label": "Manage Reports (F10)", "command": lambda: Reports_ui(parent=self)},
                    {"type": "separator"},
                    {"label": "Revenue Reports (PDF)", "command": lambda: export_year_report("Revenue Reports", parent=self)},
                    {"label": "Expense Analysis (PDF)", "command": lambda: export_year_report("Expense Analysis", parent=self)},
                    {"label": "Cash Flow Statement (PDF)", "command": lambda: export_year_report("Cash Flow Statement", parent=self)},
                    {"label": "Profit and Loss Statement (PDF)", "command": lambda: export_year_report("Profit and Loss Statement", parent=self)},
                ],
            },
            {
                "text": "Cheques",
                "commands": [
                    {"label": "Add/Print Cheque (F11)", "command": lambda: PrintCheque_ui(parent=self)},
                    {"label": "Manage Cheques", "command": lambda: Manage_Cheques_ui(parent=self)},
                    {"type": "separator"},
                    {"label": "Add Cheque Book", "command": lambda: addChequeBook_ui(parent=self)},
                    {"label": "Manage ChequeBooks", "command": lambda: Manage_chequeBook_ui(parent=self)},
                ],
            },
            {
                "text": "Settings",
                "commands": [
                    {"label": "Edit Company", "command": lambda: company_info("edit", parent=self)},
                    {"label": "Add Terms & Conditions", "command": lambda: terms_conditions(parent=self)},
                    {"label": "Backup Management", "command": lambda: Backup_ui(parent=self)},
                    {"label": "Restore Management", "command": lambda: Restore_ui()},
                ],
            },
            {
                "text": "Logout",
                "pack_side": "bottom",
                "single_command": lambda: on_closing(self),
            },
        ]

    def _handle_search(self, query: str) -> List[Dict[str, str]]:
        quick_commands = [
            {"kind": "Action", "label": "Create New Invoice (F1)", "action": "new_invoice"},
            {"kind": "Action", "label": "Add New Client (F3)", "action": "new_client"},
            {"kind": "Action", "label": "Record Payment In (F4)", "action": "payment_in"},
            {"kind": "Action", "label": "Manage Payments (F7)", "action": "payments"},
            {"kind": "Action", "label": "View Financial Reports (F10)", "action": "reports"},
        ]
        q = query.lower()
        matches = [cmd for cmd in quick_commands if q in cmd["label"].lower()]
        matches.extend(self.data_provider.search_entities(query))
        return matches[:8]

    def _handle_search_select(self, payload: Dict[str, str]) -> None:
        act = payload.get("action")
        if act == "new_invoice":
            new_invoice_ui(parent=self)
        elif act == "new_client":
            new_client_ui(parent=self)
        elif act == "payment_in":
            customer_payment_in(parent=self)
        elif act == "payments":
            manage_payments(parent=self)
        elif act == "reports":
            Reports_ui(parent=self)
        elif act == "clients":
            manage_clients(parent=self)
        elif act == "invoices":
            manage_invoice_ui(parent=self)

    def _get_notifications(self) -> List[str]:
        snap = self.mainframe._latest_snapshot or self.data_provider.get_snapshot()
        return snap.notifications

    def _bind_shortcuts(self) -> None:
        self.bind("<F1>", lambda _e: new_invoice_ui(parent=self))
        self.bind("<F2>", lambda _e: new_purchase_ui(parent=self))
        self.bind("<F3>", lambda _e: new_client_ui(parent=self))
        self.bind("<F4>", lambda _e: customer_payment_in(parent=self))
        self.bind("<F5>", lambda _e: supplier_payments_out(parent=self))
        self.bind("<F6>", lambda _e: expense_payments_out(parent=self))
        self.bind("<F7>", lambda _e: manage_payments(parent=self))
        self.bind("<F8>", lambda _e: manage_invoice_ui(parent=self))
        self.bind("<F9>", lambda _e: manage_clients(parent=self))
        self.bind("<F10>", lambda _e: Reports_ui(parent=self))
        self.bind("<F11>", lambda _e: PrintCheque_ui(parent=self))
        self.bind("<Escape>", lambda event: on_closing(self))
        self.protocol("WM_DELETE_WINDOW", lambda: on_closing(self))


if __name__ == "__main__":
    App()
