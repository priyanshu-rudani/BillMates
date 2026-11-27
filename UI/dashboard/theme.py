"""
UI/dashboard/theme.py
---------------------
Centralized theme palette, typography, spacing, and font registration
for the BillMates Billing & Analytics Dashboard.
"""

import ctypes
import logging
import sys
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)

_FONTS_LOADED = False


def load_bundled_fonts() -> None:
    """Register bundled TTF fonts privately for the current process on Windows."""
    global _FONTS_LOADED
    if _FONTS_LOADED:
        return
    _FONTS_LOADED = True

    if sys.platform != "win32":
        return

    try:
        from utilities.path_utils import generate_path
        font_dir = Path(generate_path("utilities", "assets", "Font"))
    except Exception:
        font_dir = Path(__file__).resolve().parents[2] / "utilities" / "assets" / "Font"

    if not font_dir.exists():
        return

    FR_PRIVATE = 0x10
    gdi32 = ctypes.windll.gdi32
    for ttf in font_dir.glob("*.ttf"):
        try:
            gdi32.AddFontResourceExW(str(ttf), FR_PRIVATE, 0)
        except Exception as exc:
            logger.debug("Could not load font %s: %s", ttf, exc)


THEME: Dict[str, Any] = {
    "colors": {
        # App surfaces
        "app_bg": "#F3F5FB",
        "header_bg": "#FFFFFF",
        "header_border": "#E8ECF4",
        "card_bg": "#FFFFFF",
        "card_border": "#E8ECF4",
        "card_shadow": "#E2E7F5",
        "tile_bg": "#F4F6FC",
        "tile_hover": "#E6EBFA",

        # Sidebar
        "sidebar_bg": "#232263",
        "sidebar_hover": "#32317E",
        "sidebar_active": "#4E52B8",
        "sidebar_active_border": "#7377E2",
        "sidebar_text": "#E2E6FF",
        "sidebar_muted": "#B8BDE4",

        # Brand & Accents
        "primary": "#5856D6",
        "primary_dark": "#4341B8",
        "primary_light": "#EAE9FE",
        "primary_soft": "#EEF0FF",
        "banner_start": "#EEF0FF",
        "banner_end": "#BDB5F7",
        "growth_start": "#473FD6",
        "growth_end": "#6E5EF5",

        # Typography
        "text_primary": "#151D48",
        "text_secondary": "#4B5563",
        "text_muted": "#737791",
        "text_light": "#9CA3AF",
        "white": "#FFFFFF",

        # Search input
        "search_bg": "#F4F6FA",
        "search_border": "#E5E9F2",

        # Semantic / KPI Colors
        "success": "#15803D",
        "success_bright": "#16A34A",
        "success_bg": "#DCFCE7",
        "danger": "#DC2626",
        "danger_bg": "#FEE2E2",
        "info": "#2563EB",
        "info_bg": "#DBEAFE",
        "warning": "#D97706",
        "warning_bg": "#FFEDD5",
        "purple_icon": "#5B5CE6",
        "purple_bg": "#EAE9FE",

        # Charts
        "chart_revenue": "#1D4ED8",
        "chart_revenue_fill": "#3B82F6",
        "chart_expense": "#F97316",
        "chart_expense_fill": "#FB923C",
        "chart_grid": "#EEF2F7",
        "chart_axis": "#64748B",
        "donut_palette": [
            "#6246EA",
            "#22A947",
            "#F59E0B",
            "#2563EB",
            "#5B47A6",
            "#2A9D8F",
            "#EC4899",
        ],
    },
    "fonts": {
        "brand": ("Poppins SemiBold", 14),
        "banner_greet": ("Inter", 13),
        "banner_title": ("Poppins Bold", 20),
        "banner_sub": ("Inter", 10),
        "section_title": ("Poppins SemiBold", 12),
        "card_label": ("Inter", 10),
        "kpi_value": ("Poppins Bold", 15),
        "badge": ("Inter Bold", 9),
        "nav": ("Inter Medium", 11),
        "nav_active": ("Inter Bold", 11),
        "body": ("Inter", 10),
        "body_bold": ("Inter Bold", 10),
        "small": ("Inter", 9),
        "small_bold": ("Inter Bold", 9),
    },
    "radii": {
        "card": 14,
        "banner": 16,
        "pill": 18,
        "tile": 12,
        "button": 10,
    },
    "spacing": {
        "sidebar_width": 220,
        "header_height": 64,
        "outer_pad_x": 24,
        "outer_pad_y": 18,
        "card_gap": 16,
        "card_pad_x": 18,
        "card_pad_y": 14,
    },
}


def get_font(key: str, size_delta: int = 0) -> tuple:
    """Return a font tuple from THEME['fonts'] with optional size adjustment."""
    family, size = THEME["fonts"].get(key, ("Segoe UI", 10))
    return (family, max(7, size + size_delta))
