"""
utilities/report_pdf_generator.py
---------------------------------
High-performance, scalable, and reusable PDF Report Generation module using ReportLab.
"""

import os
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

# Tkinter dialogs
import tkinter as tk
from tkinter import filedialog, messagebox

# ReportLab imports
from reportlab.lib.pagesizes import A4, landscape, portrait
from reportlab.lib import colors
from reportlab.lib.units import inch, cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    KeepTogether,
    HRFlowable,
)
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from utilities.path_utils import generate_path, read_ini, get_client_id, get_client_type, _show_error, logger
from core.database import query_all
from services.report_service import ReportRepository, ReportFilterError, validate_and_convert_dates, to_iso_sql


# ==============================================================================
# THEME CONFIGURATION (Matches BillMates Dashboard)
# ==============================================================================

class Theme:
    """Dashboard-aligned color palette and typography constants."""
    PRIMARY = colors.HexColor("#4F59C1")         # Dashboard primary purple/blue
    PRIMARY_DARK = colors.HexColor("#151D48")    # Dashboard primary dark headings
    PRIMARY_LIGHT = colors.HexColor("#E7EBFF")   # Dashboard light accent tint
    TEXT_MUTED = colors.HexColor("#737791")      # Dashboard secondary/muted text
    TEXT_DARK = colors.HexColor("#151D48")       # Main text color
    BG_CARD = colors.HexColor("#F4F6FD")         # Light card background
    BG_ALT = colors.HexColor("#F8F9FE")          # Alternating table row
    BG_WHITE = colors.HexColor("#FFFFFF")        # Pure white
    BORDER = colors.HexColor("#E0E5F2")          # Subtle border color
    BORDER_DARK = colors.HexColor("#CBD5E1")     # Slightly darker border
    SUCCESS = colors.HexColor("#00892A")         # Positive / Credit / Profit
    DANGER = colors.HexColor("#DC2626")          # Negative / Debit / Loss
    WARNING = colors.HexColor("#D97706")         # Pending / Notice


# ==============================================================================
# FONT REGISTRATION & MANAGEMENT
# ==============================================================================

_FONTS_INITIALIZED = False
FONT_BOLD = "Helvetica-Bold"
FONT_SEMI = "Helvetica"
FONT_REGULAR = "Helvetica"


def init_fonts() -> Tuple[str, str, str]:
    """
    Registers Poppins / Inter TTF fonts if present in assets/Font.
    Falls back gracefully to Helvetica if TTF files are unavailable.
    """
    global _FONTS_INITIALIZED, FONT_BOLD, FONT_SEMI, FONT_REGULAR
    if _FONTS_INITIALIZED:
        return FONT_BOLD, FONT_SEMI, FONT_REGULAR

    font_dir = Path(generate_path("utilities", "assets", "Font"))

    # Try registering Poppins (matches Dashboard UI)
    poppins_bold = font_dir / "Poppins-Bold.ttf"
    poppins_semi = font_dir / "Poppins-SemiBold.ttf"

    if poppins_bold.exists() and poppins_semi.exists():
        try:
            pdfmetrics.registerFont(TTFont("Poppins-Bold", str(poppins_bold)))
            pdfmetrics.registerFont(TTFont("Poppins-SemiBold", str(poppins_semi)))
            FONT_BOLD = "Poppins-Bold"
            FONT_SEMI = "Poppins-SemiBold"
            FONT_REGULAR = "Poppins-SemiBold"
            _FONTS_INITIALIZED = True
            return FONT_BOLD, FONT_SEMI, FONT_REGULAR
        except Exception:
            pass

    # Try registering Inter (from invoice generator)
    inter_bold = font_dir / "Inter-Bold.ttf"
    inter_regular = font_dir / "Inter-Regular.ttf"
    if inter_bold.exists() and inter_regular.exists():
        try:
            pdfmetrics.registerFont(TTFont("Inter-Bold", str(inter_bold)))
            pdfmetrics.registerFont(TTFont("Inter-Regular", str(inter_regular)))
            FONT_BOLD = "Inter-Bold"
            FONT_SEMI = "Inter-Bold"
            FONT_REGULAR = "Inter-Regular"
            _FONTS_INITIALIZED = True
            return FONT_BOLD, FONT_SEMI, FONT_REGULAR
        except Exception:
            pass

    # Standard PDF fallback
    FONT_BOLD = "Helvetica-Bold"
    FONT_SEMI = "Helvetica-Bold"
    FONT_REGULAR = "Helvetica"
    _FONTS_INITIALIZED = True
    return FONT_BOLD, FONT_SEMI, FONT_REGULAR


# ==============================================================================
# NUMBERED CANVAS (2-Pass Dynamic Page Numbers & Running Headers/Footers)
# ==============================================================================

class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas that accumulates page states and renders exact 'Page X of Y'
    along with running header and footer on every page during the save step.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states: List[Dict[str, Any]] = []
        self.report_title: str = kwargs.get("report_title", "Report")
        self.company_name: str = kwargs.get("company_name", "BillMates")

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self._draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def _draw_page_decorations(self, total_pages: int):
        self.saveState()
        init_fonts()
        font_regular = FONT_REGULAR
        font_bold = FONT_BOLD

        page_w, page_h = self._pagesize
        margin_x = 36.0  # 0.5 in

        # ----------------------------------------------------------------------
        # Running Top Header on Later Pages (Pages > 1)
        # ----------------------------------------------------------------------
        if self._pageNumber > 1:
            self.setFont(font_regular, 8)
            self.setFillColor(Theme.TEXT_MUTED)
            self.drawString(margin_x, page_h - 26, f"{self.company_name}  |  {self.report_title}")

            self.setFont(font_regular, 8)
            self.drawRightString(page_w - margin_x, page_h - 26, f"Page {self._pageNumber} of {total_pages}")

            # Top thin accent line
            self.setStrokeColor(Theme.BORDER)
            self.setLineWidth(0.6)
            self.line(margin_x, page_h - 30, page_w - margin_x, page_h - 30)

        # ----------------------------------------------------------------------
        # Running Bottom Footer (On All Pages)
        # ----------------------------------------------------------------------
        footer_y = 24.0

        # Divider line
        self.setStrokeColor(Theme.BORDER)
        self.setLineWidth(0.6)
        self.line(margin_x, footer_y + 12, page_w - margin_x, footer_y + 12)

        # Footer Left: Application branding & company
        self.setFont(font_regular, 7.5)
        self.setFillColor(Theme.TEXT_MUTED)
        self.drawString(margin_x, footer_y, f"Generated via BillMates • {self.company_name}")

        # Footer Center: Timestamp
        timestamp_str = datetime.now().strftime("%d/%m/%Y %I:%M %p")
        self.drawCentredString(page_w / 2.0, footer_y, f"Generated: {timestamp_str}")

        # Footer Right: Page Count
        self.setFont(font_bold, 8)
        self.setFillColor(Theme.PRIMARY_DARK)
        self.drawRightString(page_w - margin_x, footer_y, f"Page {self._pageNumber} of {total_pages}")

        self.restoreState()


# ==============================================================================
# DATA MODELS FOR REPORTS
# ==============================================================================

@dataclass
class ReportKPI:
    """Summary metric shown in the report footer/summary section."""
    label: str
    value: Union[str, float, int]
    variant: str = "default"  # 'default', 'highlight', 'success', 'danger'

    def formatted_value(self) -> str:
        if isinstance(self.value, (int, float)):
            return f"Rs. {self.value:,.2f}"
        return str(self.value)


@dataclass
class CompanyProfile:
    """Company details extracted from INI config."""
    name: str = ""
    address: str = ""
    city: str = ""
    state: str = ""
    pin_code: str = ""
    email: str = ""
    phone: str = ""
    gstin: str = ""
    pan_no: str = ""

    @classmethod
    def load(cls) -> "CompanyProfile":
        try:
            return cls(
                name=read_ini("PROFILE", "name") or "BillMates Business",
                address=read_ini("PROFILE", "address") or "",
                city=read_ini("PROFILE", "city") or "",
                state=read_ini("PROFILE", "state") or "",
                pin_code=read_ini("PROFILE", "pin_code") or "",
                email=read_ini("PROFILE", "email") or "",
                phone=read_ini("PROFILE", "phone") or "",
                gstin=read_ini("PROFILE", "gstin") or "",
                pan_no=read_ini("PROFILE", "pan_no") or "",
            )
        except Exception:
            return cls(name="BillMates Business")


@dataclass
class ReportData:
    """Encapsulates all data required to generate a standardized PDF report."""
    report_title: str
    start_date: str
    end_date: str
    client_name: Optional[str] = None
    filter_tags: Dict[str, str] = field(default_factory=dict)
    headers: List[str] = field(default_factory=list)
    rows: List[List[Any]] = field(default_factory=list)
    col_widths: Optional[List[float]] = None
    col_alignments: Optional[List[str]] = None
    kpis: List[ReportKPI] = field(default_factory=list)
    orientation: str = "portrait"  # 'portrait' or 'landscape'
    company: CompanyProfile = field(default_factory=CompanyProfile.load)
    row_types: Optional[List[str]] = None


# ==============================================================================
# PDF REPORT BUILDER ENGINE (Scalable, Reusable, Performance-Optimized)
# ==============================================================================

class PDFReportBuilder:
    """
    Constructs high-aesthetic, scalable PDF documents adhering to the dashboard theme.
    Handles dynamic column sizing, cell text wrapping, pagebreaks, and footer summaries.
    """

    def __init__(self, data: ReportData):
        self.data = data
        self.font_bold, self.font_semi, self.font_regular = init_fonts()
        self.styles = getSampleStyleSheet()
        self._init_custom_styles()

    def _init_custom_styles(self):
        """Pre-creates reusable ParagraphStyles to avoid repeated dictionary allocation."""
        self.style_company_name = ParagraphStyle(
            name="CompanyName",
            fontName=self.font_bold,
            fontSize=15,
            leading=18,
            textColor=Theme.PRIMARY_DARK,
        )
        self.style_company_sub = ParagraphStyle(
            name="CompanySub",
            fontName=self.font_regular,
            fontSize=8,
            leading=11,
            textColor=Theme.TEXT_MUTED,
        )
        self.style_report_title = ParagraphStyle(
            name="ReportTitle",
            fontName=self.font_bold,
            fontSize=14,
            leading=17,
            textColor=Theme.PRIMARY,
            alignment=TA_RIGHT,
        )
        self.style_meta_label = ParagraphStyle(
            name="MetaLabel",
            fontName=self.font_semi,
            fontSize=8,
            leading=11,
            textColor=Theme.TEXT_MUTED,
            alignment=TA_RIGHT,
        )
        self.style_meta_value = ParagraphStyle(
            name="MetaValue",
            fontName=self.font_bold,
            fontSize=8.5,
            leading=11,
            textColor=Theme.PRIMARY_DARK,
            alignment=TA_RIGHT,
        )
        self.style_th = ParagraphStyle(
            name="TableHeader",
            fontName=self.font_bold,
            fontSize=8.5,
            leading=11,
            textColor=Theme.BG_WHITE,
            alignment=TA_CENTER,
        )
        self.style_td_left = ParagraphStyle(
            name="TableCellLeft",
            fontName=self.font_regular,
            fontSize=8,
            leading=10.5,
            textColor=Theme.TEXT_DARK,
            alignment=TA_LEFT,
        )
        self.style_td_center = ParagraphStyle(
            name="TableCellCenter",
            fontName=self.font_regular,
            fontSize=8,
            leading=10.5,
            textColor=Theme.TEXT_DARK,
            alignment=TA_CENTER,
        )
        self.style_td_right = ParagraphStyle(
            name="TableCellRight",
            fontName=self.font_regular,
            fontSize=8,
            leading=10.5,
            textColor=Theme.TEXT_DARK,
            alignment=TA_RIGHT,
        )
        self.style_td_right_bold = ParagraphStyle(
            name="TableCellRightBold",
            fontName=self.font_bold,
            fontSize=8.5,
            leading=11,
            textColor=Theme.PRIMARY_DARK,
            alignment=TA_RIGHT,
        )
        self.style_td_center_bold = ParagraphStyle(
            name="TableCellCenterBold",
            fontName=self.font_bold,
            fontSize=8.5,
            leading=11,
            textColor=Theme.PRIMARY_DARK,
            alignment=TA_CENTER,
        )
        self.style_pnl_section = ParagraphStyle(
            name="PnLSection",
            fontName=self.font_bold,
            fontSize=9,
            leading=11.5,
            textColor=Theme.PRIMARY_DARK,
            alignment=TA_LEFT,
        )
        self.style_pnl_subtotal = ParagraphStyle(
            name="PnLSubtotal",
            fontName=self.font_bold,
            fontSize=8.5,
            leading=11,
            textColor=Theme.PRIMARY_DARK,
            alignment=TA_LEFT,
        )
        self.style_pnl_milestone = ParagraphStyle(
            name="PnLMilestone",
            fontName=self.font_bold,
            fontSize=9,
            leading=11.5,
            textColor=Theme.PRIMARY_DARK,
            alignment=TA_LEFT,
        )
        self.style_pnl_grand_total = ParagraphStyle(
            name="PnLGrandTotal",
            fontName=self.font_bold,
            fontSize=9.5,
            leading=12,
            textColor=Theme.PRIMARY_DARK,
            alignment=TA_LEFT,
        )
        self.style_pnl_formula = ParagraphStyle(
            name="PnLFormula",
            fontName=self.font_regular,
            fontSize=8,
            leading=10.5,
            textColor=Theme.TEXT_MUTED,
            alignment=TA_CENTER,
        )
        self.style_pnl_amount_green = ParagraphStyle(
            name="PnLAmountGreen",
            fontName=self.font_bold,
            fontSize=9,
            leading=11,
            textColor=Theme.SUCCESS,
            alignment=TA_RIGHT,
        )
        self.style_pnl_amount_red = ParagraphStyle(
            name="PnLAmountRed",
            fontName=self.font_bold,
            fontSize=9,
            leading=11,
            textColor=Theme.DANGER,
            alignment=TA_RIGHT,
        )
        self.style_pnl_grand_amount_green = ParagraphStyle(
            name="PnLGrandAmountGreen",
            fontName=self.font_bold,
            fontSize=9.5,
            leading=12,
            textColor=Theme.SUCCESS,
            alignment=TA_RIGHT,
        )
        self.style_pnl_grand_amount_red = ParagraphStyle(
            name="PnLGrandAmountRed",
            fontName=self.font_bold,
            fontSize=9.5,
            leading=12,
            textColor=Theme.DANGER,
            alignment=TA_RIGHT,
        )
        self.style_kpi_label = ParagraphStyle(
            name="KPILabel",
            fontName=self.font_regular,
            fontSize=7.5,
            leading=9.5,
            textColor=Theme.TEXT_MUTED,
            alignment=TA_CENTER,
        )
        self.style_kpi_val = ParagraphStyle(
            name="KPIVal",
            fontName=self.font_bold,
            fontSize=11,
            leading=13,
            textColor=Theme.PRIMARY_DARK,
            alignment=TA_CENTER,
        )

    def _build_header_flowable(self, printable_width: float) -> Table:
        """
        Builds a modern 2-column header:
        - Left column: Company identity and contact info.
        - Right column: Report type, date range, client/supplier info, and filter pills.
        """
        c = self.data.company

        # ---------------- Left Column: Company Info ----------------
        company_lines = [
            Paragraph(f"<b>{c.name or 'BillMates Business'}</b>", self.style_company_name)
        ]
        addr_parts = [p for p in [c.address, c.city, c.state, c.pin_code] if p]
        if addr_parts:
            company_lines.append(Paragraph(", ".join(addr_parts), self.style_company_sub))

        contact_parts = []
        if c.phone:
            contact_parts.append(f"Phone: {c.phone}")
        if c.email:
            contact_parts.append(f"Email: {c.email}")
        if contact_parts:
            company_lines.append(Paragraph(" • ".join(contact_parts), self.style_company_sub))

        tax_parts = []
        if c.gstin:
            tax_parts.append(f"GSTIN: <b>{c.gstin}</b>")
        if c.pan_no:
            tax_parts.append(f"PAN: <b>{c.pan_no}</b>")
        if tax_parts:
            company_lines.append(Paragraph(" | ".join(tax_parts), self.style_company_sub))

        # ---------------- Right Column: Report Details Card ----------------
        report_meta = [
            Paragraph(f"<b>{self.data.report_title.upper()}</b>", self.style_report_title),
            Spacer(1, 3),
            Paragraph(
                f"Period: <b>{self.data.start_date}</b> to <b>{self.data.end_date}</b>",
                self.style_meta_value
            )
        ]

        if self.data.client_name and self.data.client_name not in ("Select", "All", ""):
            client_t = self.data.filter_tags.get("Client Type", "Party Name")
            report_meta.append(
                Paragraph(f"{client_t}: <b>{self.data.client_name}</b>", self.style_meta_value)
            )

        for k, v in self.data.filter_tags.items():
            if k not in ("Client Type", "Period", "Party Name") and v:
                report_meta.append(Paragraph(f"{k}: <b>{v}</b>", self.style_meta_value))

        header_table = Table(
            [[company_lines, report_meta]],
            colWidths=[printable_width * 0.55, printable_width * 0.45],
        )
        header_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        return header_table

    def _build_table_flowable(self, printable_width: float) -> Table:
        """
        Constructs the main data table:
        - Auto-calculates column widths based on printable page width.
        - Wraps every cell in a Paragraph for clean line breaking.
        - Sets repeatRows=1 so the header repeats across page breaks.
        - Formats alternating row colors and alignment according to data types.
        """
        num_cols = len(self.data.headers)
        if num_cols == 0:
            return Table([["No data available"]])

        # Calculate column widths
        if self.data.col_widths and len(self.data.col_widths) == num_cols:
            total_ratio = sum(self.data.col_widths)
            col_widths = [(w / total_ratio) * printable_width for w in self.data.col_widths]
        else:
            col_widths = [printable_width / num_cols] * num_cols

        # Determine alignments per column
        alignments = self.data.col_alignments or []
        while len(alignments) < num_cols:
            alignments.append("left")

        # Build Header Row
        table_data = []
        header_row = [Paragraph(f"<b>{h}</b>", self.style_th) for h in self.data.headers]
        table_data.append(header_row)

        # Build Body Rows
        has_row_types = bool(self.data.row_types and len(self.data.row_types) == len(self.data.rows))

        # Build TableStyle base rules
        t_style = [
            ("BACKGROUND", (0, 0), (-1, 0), Theme.PRIMARY),
            ("TEXTCOLOR", (0, 0), (-1, 0), Theme.BG_WHITE),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, 0), 6),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("LINEBELOW", (0, 0), (-1, 0), 1.2, Theme.PRIMARY_DARK),
            ("INNERGRID", (0, 0), (-1, -1), 0.4, Theme.BORDER),
            ("BOX", (0, 0), (-1, -1), 0.8, Theme.PRIMARY),
        ]

        if not self.data.rows:
            empty_row = [Paragraph("<i>No records found matching the selected criteria.</i>", self.style_td_center)]
            empty_row.extend([Paragraph("", self.style_td_center) for _ in range(num_cols - 1)])
            table_data.append(empty_row)
            t_style.append(("SPAN", (0, 1), (-1, 1)))
            t_style.append(("ALIGN", (0, 1), (-1, 1), "CENTER"))
            t_style.append(("TOPPADDING", (0, 1), (-1, 1), 12))
            t_style.append(("BOTTOMPADDING", (0, 1), (-1, 1), 12))
        
        else:
            # Custom hierarchical formatting (e.g. Profit and Loss Statement)
            for r_idx_raw, row in enumerate(self.data.rows):
                r_idx = r_idx_raw + 1

                # Regular item
                amt = row[3]
                amt_str = f"{float(amt):,.2f}" if isinstance(amt, (int, float)) or (amt and str(amt).replace('.', '', 1).replace('-', '', 1).isdigit()) else str(amt or "")
                item_row = [
                    Paragraph(str(row[0] or ""), self.style_td_center),
                    Paragraph(f"&nbsp;&nbsp;&nbsp;&nbsp;{row[1]}", self.style_td_left),
                    Paragraph(str(row[2] or ""), self.style_pnl_formula),
                    Paragraph(amt_str, self.style_td_right),
                ]
                table_data.append(item_row)
                bg_col = Theme.BG_ALT if r_idx % 2 == 0 else Theme.BG_WHITE
                t_style.append(("BACKGROUND", (0, r_idx), (-1, r_idx), bg_col))
                t_style.append(("TOPPADDING", (0, r_idx), (-1, r_idx), 3.5))
                t_style.append(("BOTTOMPADDING", (0, r_idx), (-1, r_idx), 3.5))


        report_table = Table(
            table_data,
            colWidths=col_widths,
            repeatRows=1  # Repeats header on every split page
        )
        report_table.setStyle(TableStyle(t_style))
        return report_table

    def _build_summary_flowables(self, printable_width: float) -> Optional[KeepTogether]:
        """
        Builds the summary footer card containing totals, wrapped in KeepTogether
        to ensure it never splits awkwardly over a pagebreak.
        """
        if not self.data.kpis:
            return None

        kpi_count = len(self.data.kpis)
        card_width = printable_width / max(1, kpi_count)

        kpi_cells = []
        for kpi in self.data.kpis:
            # Color coding for variants
            if kpi.variant == "success":
                val_color = Theme.SUCCESS
            elif kpi.variant == "danger":
                val_color = Theme.DANGER
            elif kpi.variant == "highlight":
                val_color = Theme.PRIMARY
            else:
                val_color = Theme.PRIMARY_DARK

            val_style = ParagraphStyle(
                name=f"KPI_{kpi.label}",
                fontName=self.font_bold,
                fontSize=11,
                leading=14,
                textColor=val_color,
                alignment=TA_CENTER,
            )

            cell_content = [
                Paragraph(kpi.label.upper(), self.style_kpi_label),
                Spacer(1, 2),
                Paragraph(kpi.formatted_value(), val_style),
            ]
            kpi_cells.append(cell_content)

        summary_table = Table([kpi_cells], colWidths=[card_width] * kpi_count)
        summary_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), Theme.BG_CARD),
            ("BOX", (0, 0), (-1, -1), 1.0, Theme.PRIMARY),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, Theme.BORDER),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))

        return KeepTogether([
            Spacer(1, 8),
            Paragraph("<b>SUMMARY & TOTALS</b>", ParagraphStyle(
                "SummaryH", fontName=self.font_bold, fontSize=9, textColor=Theme.PRIMARY_DARK
            )),
            Spacer(1, 4),
            summary_table,
        ])

    def build_pdf(self, file_path: str) -> str:
        """
        Compiles the complete document using ReportLab Platypus and NumberedCanvas.
        """
        # Determine orientation
        if self.data.orientation == "landscape":
            pagesize = landscape(A4)
        else:
            pagesize = portrait(A4)

        page_w, page_h = pagesize
        margin_x = 36.0  # 0.5 in
        margin_y = 36.0
        printable_width = page_w - (2 * margin_x)

        # Initialize document
        doc = SimpleDocTemplate(
            file_path,
            pagesize=pagesize,
            leftMargin=margin_x,
            rightMargin=margin_x,
            topMargin=margin_y,
            bottomMargin=margin_y + 12,  # Extra space for footer
        )

        story = []

        # 1. Header Block
        story.append(self._build_header_flowable(printable_width))
        story.append(Spacer(1, 6))

        # Thin Accent Divider
        story.append(HRFlowable(
            width="100%", thickness=1.2, color=Theme.PRIMARY, spaceAfter=8, spaceBefore=2
        ))

        # 2. Main Data Table
        story.append(self._build_table_flowable(printable_width))

        # 3. Footer Summary Block (KeepTogether ensures no orphan breaks)
        summary_block = self._build_summary_flowables(printable_width)
        if summary_block:
            story.append(summary_block)

        # Factory function for canvasmaker with custom properties
        def canvas_maker(*args, **kwargs):
            canvas_obj = NumberedCanvas(*args, **kwargs)
            canvas_obj.report_title = self.data.report_title
            canvas_obj.company_name = self.data.company.name or "BillMates"
            return canvas_obj

        doc.build(story, canvasmaker=canvas_maker)
        return file_path


# ==============================================================================
# REPORT DATA ADAPTERS (Delegated to ReportRepository)
# ==============================================================================

class ReportDataAdapter:
    """Prepares structured ReportData instances from the underlying database services."""

    @staticmethod
    def get_sales_report(start_date: str, end_date: str, client_name: Optional[str] = None) -> ReportData:
        has_client = bool(client_name and client_name not in ("Select", "All", ""))
        client_id = get_client_id(client_name) if has_client else 0

        if has_client and client_id:
            res = ReportRepository.get_customer_sales(client_id, start_date, end_date)
            rows = res.get("rows", [])
            total_sales = res.get("total_sales", 0.0)
            total_paid = res.get("total_paid", 0.0)
            total_remaining = res.get("total_remaining", 0.0)
            filter_tags = {"Client Type": "Client"}
        else:
            iso_start, iso_end = validate_and_convert_dates(start_date, end_date)
            date_expr = to_iso_sql("i.date")
            sql = f"""
                SELECT 
                    i.invoice_no,
                    i.date,
                    c.name AS client_name,
                    COALESCE(i.total, 0.0) AS total,
                    COALESCE(i.paid, 0.0) AS paid,
                    COALESCE(i.remaining, 0.0) AS remaining,
                    i.paid_status,
                    COALESCE(i.reference_no, '') AS reference_no
                FROM Invoices i
                JOIN Clients c ON i.client_id = c.id
                WHERE {date_expr} BETWEEN ? AND ?
                ORDER BY {date_expr} ASC, i.invoice_no ASC
            """
            rows = query_all(sql, (iso_start, iso_end))
            total_paid = round(sum(r[4] for r in rows), 2)
            total_remaining = round(sum(r[5] for r in rows), 2)
            total_sales = round(sum(r[3] for r in rows), 2)
            filter_tags = {"Client Type": "Client"}

        headers = ["Inv No.", "Date", "Client Name", "Total", "Paid", "Remaining", "Status", "Ref No."]
        col_widths = [11, 12, 22, 13, 13, 13, 12, 14]
        col_alignments = ["center", "center", "left", "right", "right", "right", "center", "center"]

        kpis = [
            ReportKPI("Total Sales", total_sales, "highlight"),
            ReportKPI("Paid Amount", total_paid, "success"),
            ReportKPI("Remaining Credit", total_remaining, "danger"),
        ]

        return ReportData(
            report_title="Sales Report",
            start_date=start_date,
            end_date=end_date,
            client_name=client_name if has_client else "All Clients",
            filter_tags=filter_tags,
            headers=headers,
            rows=rows,
            col_widths=col_widths,
            col_alignments=col_alignments,
            kpis=kpis,
            orientation="landscape",  # Wide 8-column layout fits best in landscape
        )

    @staticmethod
    def get_purchase_report(start_date: str, end_date: str, client_name: Optional[str] = None) -> ReportData:
        has_client = bool(client_name and client_name not in ("Select", "All", ""))
        client_id = get_client_id(client_name) if has_client else 0

        if has_client and client_id:
            res = ReportRepository.get_purchase_report(client_id, start_date, end_date)
            rows = res.get("rows", [])
            total_purchases = res.get("total_purchases", 0.0)
            total_paid = res.get("total_paid", 0.0)
            total_remaining = res.get("total_remaining", 0.0)
            filter_tags = {"Client Type": "Supplier"}
        else:
            iso_start, iso_end = validate_and_convert_dates(start_date, end_date)
            date_expr = to_iso_sql("p.date")
            sql = f"""
                SELECT 
                    p.invoice_no,
                    p.date,
                    c.name AS client_name,
                    COALESCE(p.total, 0.0) AS total,
                    COALESCE(p.paid, 0.0) AS paid,
                    COALESCE(p.remaining, 0.0) AS remaining,
                    p.paid_status,
                    COALESCE(p.reference_no, '') AS reference_no
                FROM Purchase p
                JOIN Clients c ON p.client_id = c.id
                WHERE {date_expr} BETWEEN ? AND ?
                ORDER BY {date_expr} ASC, p.invoice_no ASC
            """
            rows = query_all(sql, (iso_start, iso_end))
            total_paid = round(sum(r[4] for r in rows), 2)
            total_remaining = round(sum(r[5] for r in rows), 2)
            total_purchases = round(sum(r[3] for r in rows), 2)
            filter_tags = {"Client Type": "Supplier"}

        headers = ["PO No.", "Date", "Supplier Name", "Total", "Paid", "Remaining", "Status", "Ref No."]
        col_widths = [11, 12, 22, 13, 13, 13, 12, 14]
        col_alignments = ["center", "center", "left", "right", "right", "right", "center", "center"]

        kpis = [
            ReportKPI("Total Purchases", total_purchases, "highlight"),
            ReportKPI("Paid Purchases", total_paid, "success"),
            ReportKPI("Accounts Payable", total_remaining, "danger"),
        ]

        return ReportData(
            report_title="Purchase Report",
            start_date=start_date,
            end_date=end_date,
            client_name=client_name if has_client else "All Suppliers",
            filter_tags=filter_tags,
            headers=headers,
            rows=rows,
            col_widths=col_widths,
            col_alignments=col_alignments,
            kpis=kpis,
            orientation="landscape",
        )

    @staticmethod
    def get_customer_payment_report(start_date: str, end_date: str, client_name: Optional[str] = None) -> ReportData:
        client_id = get_client_id(client_name) if client_name else 0
        res = ReportRepository.get_customer_payment(client_id, start_date, end_date)
        rows = res.get("rows", [])

        headers = ["Date", "Payment Type", "Party Name", "Amount", "Mode", "Reference No."]
        col_widths = [13, 20, 22, 15, 15, 15]
        col_alignments = ["center", "left", "left", "right", "center", "center"]

        kpis = [
            ReportKPI("Total Payments Settled", res.get("total_amount", 0.0), "highlight")
        ]

        return ReportData(
            report_title="Client Payment Report",
            start_date=start_date,
            end_date=end_date,
            client_name=client_name,
            filter_tags={"Client Type": get_client_type(client_name) if client_name else "Client"},
            headers=headers,
            rows=rows,
            col_widths=col_widths,
            col_alignments=col_alignments,
            kpis=kpis,
            orientation="portrait",
        )

    @staticmethod
    def get_customer_ledger(start_date: str, end_date: str, client_name: Optional[str] = None) -> ReportData:
        client_id = get_client_id(client_name) if client_name else 0
        raw_ledger = ReportRepository.get_customer_ledger(client_id, start_date, end_date)

        headers = ["Date", "Description", "Credited (In)", "Debited (Out)", "Running Balance"]
        col_widths = [14, 38, 16, 16, 16]
        col_alignments = ["center", "left", "right", "right", "right"]

        # Extract opening and closing balance
        opening_bal = 0.0
        closing_bal = 0.0
        tot_credit = 0.0
        tot_debit = 0.0

        clean_rows = []
        for entry in raw_ledger:
            dt, desc, cr, dr, bal = entry[0], entry[1], entry[2], entry[3], entry[4]
            if desc == "Opening Balance":
                opening_bal = float(bal)
            elif desc == "Closing Balance":
                closing_bal = float(bal)
            else:
                tot_credit += float(cr or 0.0)
                tot_debit += float(dr or 0.0)
            clean_rows.append([dt, desc, cr, dr, bal])

        kpis = [
            ReportKPI("Opening Balance", opening_bal, "default"),
            ReportKPI("Total Credited", tot_credit, "success"),
            ReportKPI("Total Debited", tot_debit, "danger"),
            ReportKPI("Closing Balance", closing_bal, "highlight"),
        ]

        return ReportData(
            report_title="Party Statement / Ledger",
            start_date=start_date,
            end_date=end_date,
            client_name=client_name,
            filter_tags={"Party Type": get_client_type(client_name) if client_name else "Party"},
            headers=headers,
            rows=clean_rows,
            col_widths=col_widths,
            col_alignments=col_alignments,
            kpis=kpis,
            orientation="portrait",
        )

    @staticmethod
    def get_cashflow_report(start_date: str, end_date: str) -> ReportData:
        res = ReportRepository.get_cashflow_report(start_date, end_date)
        rows = res.get("rows", [])

        headers = ["Date", "Party / Entity", "Category", "Amount", "Mode", "Type", "Ref No."]
        col_widths = [12, 18, 14, 13, 14, 15, 14]
        col_alignments = ["center", "left", "center", "right", "center", "left", "center"]

        tot_in = res.get("total_in", 0.0)
        tot_out = res.get("total_out", 0.0)
        net_cash = tot_in - tot_out

        kpis = [
            ReportKPI("Total Cash Inflow", tot_in, "success"),
            ReportKPI("Total Cash Outflow", tot_out, "danger"),
            ReportKPI("Net Cash Position", net_cash, "highlight" if net_cash >= 0 else "danger"),
        ]

        return ReportData(
            report_title="Cash Flow Statement",
            start_date=start_date,
            end_date=end_date,
            headers=headers,
            rows=rows,
            col_widths=col_widths,
            col_alignments=col_alignments,
            kpis=kpis,
            orientation="portrait", # landscape
        )

    @staticmethod
    def get_profit_loss_report(start_date: str, end_date: str) -> ReportData:
        report = ReportRepository.get_profit_loss_report(start_date, end_date)
        if not report or report[0] is None:
            report = (0.0,) * 18

        rows = [
            [" ", "Revenue", "", ""],
            [1, "Collected Revenue", "", round(report[0], 2)],
            [2, "Accounts Receivable", "", round(report[1], 2)],
            [3, "Gross Revenue", "(1+2)", round(report[2], 2)],
            [" ", "", "", ""],
            [" ", "Cost of Goods Sold (COGS)", "", ""],
            [4, "Settled Purchases", "", round(report[3], 2)],
            [5, "Accounts Payable", "", round(report[4], 2)],
            [6, "Comprehensive Logistics Costs", "", round(report[6], 2)],
            [7, "Total COGS Expenditure", "(4+5+6)", round(report[7], 2)],
            [" ", "", "", ""],
            [8, "Gross Profit/Loss", "(3-7)", round(report[8], 2)],
            [" ", "", "", ""],
            [" ", "Operating Expenses (OPEX)", "", ""],
            [9, "Staff Salaries & Wages", "", round(report[5], 2)],
            [10, "Rental Expenses", "", round(report[9], 2)],
            [11, "Utilities Expenditure", "", round(report[10], 2)],
            [12, "Upkeep Expenses", "", round(report[11], 2)],
            [13, "Marketing Expenses", "", round(report[12], 2)],
            [14, "Loan Interest Cost", "", round(report[13], 2)],
            [15, "Statutory Dues", "", round(report[14], 2)], 
            [16, "Other Expances", "", round(report[15], 2)],
            [17, "Total Operating Expenses", "(9 To 16)", round(report[16], 2)],
            [" ", "", "", ""],
            [18, "Net Profit/Loss", "(8-17)", round(report[17], 2)],
            [" ", "", "", ""],
        ]

        headers = ["Sr No.", "Category", " ", "Amount"]
        col_widths = [10, 48, 16, 26]
        col_alignments = ["center", "left", "center", "right"]

        gross_revenue = report[2]
        gross_profit = report[8]
        total_opex = report[16]
        net_profit = report[17]

        kpis = [
            ReportKPI("Gross Revenue", gross_revenue, "default"),
            ReportKPI("Gross Profit", gross_profit, "success" if gross_profit >= 0 else "danger"),
            ReportKPI("Operating Expenses", total_opex, "danger"),
            ReportKPI("Net Profit / (Loss)", net_profit, "highlight" if net_profit >= 0 else "danger"),
        ]

        return ReportData(
            report_title="Profit and Loss Statement",
            start_date=start_date,
            end_date=end_date,
            headers=headers,
            rows=rows,
            col_widths=col_widths,
            col_alignments=col_alignments,
            kpis=kpis,
            orientation="portrait",
        )

    @staticmethod
    def get_revenue_report(start_date: str, end_date: str) -> ReportData:
        res = ReportRepository.get_revenue_report(start_date, end_date)
        rows = res.get("rows", [])

        headers = ["Date", "Revenue Stream / Type", "Client Name", "Amount", "Status / Mode", "Ref No."]
        col_widths = [13, 24, 21, 15, 14, 13]
        col_alignments = ["center", "left", "left", "right", "center", "center"]

        kpis = [
            ReportKPI("Total Revenue Realized", res.get("total_amount", 0.0), "highlight")
        ]

        return ReportData(
            report_title="Revenue Report",
            start_date=start_date,
            end_date=end_date,
            headers=headers,
            rows=rows,
            col_widths=col_widths,
            col_alignments=col_alignments,
            kpis=kpis,
            orientation="portrait",
        )

    @staticmethod
    def get_expense_analysis(start_date: str, end_date: str) -> ReportData:
        res = ReportRepository.get_expense_analysis(start_date, end_date)
        rows = res.get("rows", [])

        headers = ["Date", "Expense Classification", "Beneficiary / Client", "Amount", "Payment Mode", "Ref No."]
        col_widths = [13, 24, 21, 15, 14, 13]
        col_alignments = ["center", "left", "left", "right", "center", "center"]

        kpis = [
            ReportKPI("Total Operating Expenditure", res.get("total_amount", 0.0), "danger")
        ]

        return ReportData(
            report_title="Expense Analysis Report",
            start_date=start_date,
            end_date=end_date,
            headers=headers,
            rows=rows,
            col_widths=col_widths,
            col_alignments=col_alignments,
            kpis=kpis,
            orientation="portrait",
        )


# ==============================================================================
# MAIN EXPORT DISPATCHER (Public API)
# ==============================================================================

def export_pdf_report(
    report_type: str,
    start_date: str,
    end_date: str,
    client_name: Optional[str] = None,
    output_path: Optional[str] = None,
    parent_window: Optional[tk.Widget] = None,
) -> Optional[str]:
    """
    Primary entry point to export reports as themed, paginated PDF documents.

    Args:
        report_type: Name of the report (e.g., 'Sales Reports', 'Client Ledger', etc.)
        start_date: Period start in DD/MM/YYYY format
        end_date: Period end in DD/MM/YYYY format
        client_name: Optional client or supplier filter name
        output_path: Target PDF file path. If None, prompts user via Save File dialog.
        parent_window: Optional Tk window for dialog parenting.

    Returns:
        The generated PDF file path, or None if cancelled/failed.
    """
    try:
        # 1. Resolve Data Adapter
        if report_type == "Sales Reports":
            report_data = ReportDataAdapter.get_sales_report(start_date, end_date, client_name)
        elif report_type == "Purchase Reports":
            report_data = ReportDataAdapter.get_purchase_report(start_date, end_date, client_name)
        elif report_type == "Client Payment Reports":
            report_data = ReportDataAdapter.get_customer_payment_report(start_date, end_date, client_name)
        elif report_type == "Client Ledger":
            report_data = ReportDataAdapter.get_customer_ledger(start_date, end_date, client_name)
        elif report_type == "Cash Flow Statement":
            report_data = ReportDataAdapter.get_cashflow_report(start_date, end_date)
        elif report_type == "Profit and Loss Statement":
            report_data = ReportDataAdapter.get_profit_loss_report(start_date, end_date)
        elif report_type == "Revenue Reports":
            report_data = ReportDataAdapter.get_revenue_report(start_date, end_date)
        elif report_type == "Expense Analysis":
            report_data = ReportDataAdapter.get_expense_analysis(start_date, end_date)
        else:
            if parent_window:
                messagebox.showerror("Invalid Report", f"Unknown report type: {report_type}", parent=parent_window)
            return None

        # 2. Resolve File Path (Dialog or Headless)
        if not output_path:
            safe_start = datetime.strptime(start_date, "%d/%m/%Y").strftime("%d-%m-%Y")
            safe_end = datetime.strptime(end_date, "%d/%m/%Y").strftime("%d-%m-%Y")
            if client_name and client_name not in ("Select", "All", ""):
                default_name = f"{client_name}_{report_type}_{safe_start}_{safe_end}.pdf"
            else:
                default_name = f"{report_type}_{safe_start}_{safe_end}.pdf"

            file_path = filedialog.asksaveasfilename(
                parent=parent_window,
                defaultextension=".pdf",
                filetypes=[("PDF Documents", "*.pdf")],
                initialfile=default_name,
                title=f"Export {report_type} as PDF",
            )
            if not file_path:
                return None  # User cancelled dialog
        else:
            file_path = output_path

        # 3. Build Document
        builder = PDFReportBuilder(report_data)
        builder.build_pdf(file_path)

        # 4. Success Feedback & Option to Open
        if not output_path:  # Interactive mode
            resp = messagebox.askquestion(
                "PDF Export Successful",
                f"Report successfully saved to:\n{file_path}\n\nDo you want to open the PDF now?",
                parent=parent_window
            )
            if resp == "yes":
                try:
                    os.startfile(file_path)
                except Exception as open_err:
                    logger.warning("PDF saved at %s but could not be launched automatically: %s", file_path, open_err)
                    messagebox.showwarning(
                        "File Open Warning",
                        "PDF was saved successfully, but could not be launched automatically. Please open it from your file manager.",
                        parent=parent_window
                    )

        return file_path

    except ReportFilterError as rfe:
        if parent_window:
            messagebox.showwarning("Filter Warning", str(rfe), parent=parent_window)
        return None
    except PermissionError:
        msg = "Permission denied: The target PDF file is currently open in another program. Please close it and retry."
        if parent_window:
            messagebox.showerror("Permission Error", msg, parent=parent_window)
        return None
    except Exception as e:
        if parent_window:
            _show_error("Report Error", "An unexpected error occurred during PDF generation. Please try again.", parent=parent_window, exc=e)
        else:
            _show_error("Report Error", "An unexpected error occurred during PDF generation. Please try again.", exc=e)
        return None



if __name__ == "__main__":

    i = 0
    r_type = [
        "Sales Reports",
        "Purchase Reports",
        "Client Ledger",
        "Revenue Reports",
        "Expense Analysis", 
        "Client Payment Reports",
        "Cash Flow Statement",
        "Profit and Loss Statement",
    ]
    for report in r_type:
        export_pdf_report(
            report_type=report,
            start_date = "01/01/2026",
            end_date = "31/12/2026",
            # client_name="Rohan",
            output_path = f"D:/Coding Projects/BillMates/BillMates/Source Code/reports/{i}-{report}.pdf",
        )
        i += 1