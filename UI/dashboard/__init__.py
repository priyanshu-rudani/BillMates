"""
UI/dashboard/__init__.py
------------------------
Modular desktop billing & analytics dashboard components.
Charts (matplotlib) are lazily exposed via __getattr__ so splash loaders
appear instantaneously during frozen PyInstaller startup.
"""

from UI.dashboard.theme import THEME, get_font, load_bundled_fonts
from UI.dashboard.data_provider import (
    DashboardDataProvider,
    get_financial_year_dates,
    format_compact_currency,
)
from UI.dashboard.sidebar import DashboardSidebar
from UI.dashboard.header import TopHeaderBar
from UI.dashboard.widgets import (
    WelcomeBanner,
    KpiSummaryCard,
    QuickActionsCard,
    RecentActivitiesCard,
    GrowthPromoCard,
)
from UI.dashboard.loader import DashboardLoader


def __getattr__(name: str):
    if name in ("RevenueExpensesChartCard", "ExpenseDistributionCard"):
        from UI.dashboard import charts
        return getattr(charts, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "THEME",
    "get_font",
    "load_bundled_fonts",
    "DashboardDataProvider",
    "get_financial_year_dates",
    "format_compact_currency",
    "DashboardSidebar",
    "TopHeaderBar",
    "WelcomeBanner",
    "KpiSummaryCard",
    "QuickActionsCard",
    "RecentActivitiesCard",
    "GrowthPromoCard",
    "RevenueExpensesChartCard",
    "ExpenseDistributionCard",
    "DashboardLoader",
]
