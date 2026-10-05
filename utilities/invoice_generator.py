import sys
from pathlib import Path
from dataclasses import dataclass
from typing import List, Tuple, Optional

if getattr(sys, 'frozen', False):
    root_path = Path(sys.executable).parent
else:
    root_path = Path(__file__).parent.parent
sys.path.append(str(root_path))

from utilities.path_utils import generate_path, read_ini, fetch_data
from tkinter import messagebox
from reportlab.pdfgen.canvas import Canvas
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.platypus import Frame, Table, TableStyle, Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib import colors
import textwrap
from num2words import num2words
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Optional, Tuple, Union
import qrcode

# Import configuration (settings only)
import utilities.invoice_config as cfg


# ============================================================================
# DATA CONTAINERS
# ============================================================================

@dataclass
class CompanyInfo:
    """Company information"""
    name: str
    address: str
    city: str
    state: str
    pin_code: str
    country: str
    email: str
    phone: str
    upi: str
    bank: str
    acc_no: str
    ifsc: str
    gstin: str

    @classmethod
    def from_ini(cls) -> 'CompanyInfo':
        return cls(
            name=read_ini("PROFILE", "name"),
            address=read_ini("PROFILE", "address"),
            city=read_ini("PROFILE", "city"),
            state=read_ini("PROFILE", "state"),
            pin_code=read_ini("PROFILE", "pin_code"),
            country=read_ini("PROFILE", "country"),
            email=read_ini("PROFILE", "email"),
            phone=read_ini("PROFILE", "phone"),
            upi=read_ini("PROFILE", "upi"),
            bank=read_ini("PROFILE", "bank"),
            acc_no=read_ini("PROFILE", "acc_no"),
            ifsc=read_ini("PROFILE", "IFSC"),
            gstin=read_ini("PROFILE", "gstin")
        )


@dataclass
class InvoiceData:
    """Invoice and client data"""
    client_id: int
    invoice_no_prefix: str
    invoice_no: int
    invoice_type: str
    subtotal: float
    discount: float
    total_taxes: float
    gross_total: float
    round_off: float
    grand_total: float
    cgst: float
    sgst: float
    igst: float
    taxable_amount: float
    items: List[Tuple]
    client_details: Tuple       #  id, name, contact_no, gst, city, state, client_type
    invoice_details: Tuple      #  client_id, invoice_no, Invoice_type, date, due_date, total, reference_no, remarks


# ============================================================================
# UTILITY CLASSES
# ============================================================================

class TextRenderer:
    """
    Handles text and shape rendering with automatic px → points conversion
    
    All methods accept values in PIXELS (px)
    Conversion to points happens automatically using cfg.PX_UNIT
    
    Usage:
        renderer = TextRenderer(canvas)
        renderer.draw_text("Hello", x=100, y=200, height=20,
                          font_size=12, alignment='C')
        # x=100 px, y=200 px, font_size=12 px
        # Automatically converted to points: x=100, y=200, font=12 (if PX_UNIT=1)
    """
 
    def __init__(self, canvas: Canvas):
        """
        Initialize TextRenderer
        
        Args:
            canvas: ReportLab Canvas object
        """
        self.canvas = canvas
        
        # Page dimensions from config (already in px)
        self.page_width_px = cfg.PAGE_WIDTH_PX
        self.page_height_px = cfg.PAGE_HEIGHT_PX
        
        # Conversion factor from config
        self.px_unit = cfg.PX_UNIT
        
        # Convert page dimensions to points for internal use
        self.page_width = self.page_width_px * self.px_unit
        self.page_height = self.page_height_px * self.px_unit
 
    def _convert_px_to_points(self, value: float) -> float:
        """
        Convert pixel value to points
        
        Args:
            value: Value in pixels
            
        Returns:
            Value in points (value * PX_UNIT)
        """
        return value * self.px_unit
 
    def draw_text(self, text: str, x: float, y: float, height: float,
                  font_name: str = 'Inter', font_size: float = 11,
                  alignment: Optional[str] = None, text_color: str = None) -> None:
        """
        Draw text with automatic unit conversion
        
        Args:
            text: Text to draw
            x: X position in PIXELS
            y: Y position in PIXELS (from top)
            height: Text height in PIXELS
            font_name: Font name (default: 'Inter')
            font_size: Font size in PIXELS (default: 11)
            alignment: Text alignment - 'L' (left), 'C' (center), 'R' (right)
            text_color: Hex color for text (default: black)
        
        Example:
            renderer.draw_text("Invoice", x=100, y=50, height=20,
                             font_name='P-Bold', font_size=20, alignment='C')
        """
        # Convert all px values to points
        x_points = self._convert_px_to_points(x)
        y_points = self._convert_px_to_points(y)
        height_points = self._convert_px_to_points(height)
        font_size_points = self._convert_px_to_points(font_size)
 
        # Get font object
        font_object = pdfmetrics.getFont(font_name)
        face = font_object.face
        
        # Calculate descent in points
        descent_points = face.descent / 1000.0 * font_size_points
        
        # Convert Y coordinate: PDF uses bottom-left origin, we use top-left
        y_point = self.page_height - y_points - height_points - descent_points
 
        # Calculate text width in points
        text_width = pdfmetrics.stringWidth(text, font_name, font_size_points)

 
        # Apply alignment
        if alignment == 'C':
            # Center alignment
            x_point = (self.page_width - text_width) / 2
        elif alignment == 'R':
            # Right alignment
            x_point = self.page_width - (x_points + text_width)
        else:
            # Left alignment (default)
            x_point = x_points

 
        # Set font and color
        self.canvas.setFont(font_name, font_size_points)
        
        if text_color:
            self.canvas.setFillColor(colors.HexColor(text_color))
        else:
            self.canvas.setFillColor(colors.black)
 
        # Draw the text
        self.canvas.drawString(x_point, y_point, text)
 
    def draw_rect(self, x: float, y: float, width: float, height: float,
                  stroke: int = 0, fill_color: Optional[str] = None,
                  stroke_color: Optional[str] = None, stroke_width: float = 1) -> None:
        """
        Draw rectangle with automatic unit conversion
        
        Args:
            x: Rectangle X position in PIXELS (from left)
            y: Rectangle Y position in PIXELS (from top)
            width: Rectangle width in PIXELS
            height: Rectangle height in PIXELS
            stroke: Whether to draw border (1=yes, 0=no) (default: 1)
            fill_color: Fill color as hex string (e.g., '#C5D9F1') (default: None)
            stroke_color: Border color as hex string (default: black)
            stroke_width: Border width in PIXELS (default: 1)
        
        Example:
            renderer.draw_rect(x=13, y=790, width=570, height=40,
                             fill_color='#C5D9F1', stroke=1, stroke_width=1)
        """
        # Convert all px values to points
        x_points = self._convert_px_to_points(x)
        y_points = self._convert_px_to_points(y)
        width_points = self._convert_px_to_points(width)
        height_points = self._convert_px_to_points(height)
        stroke_width_points = self._convert_px_to_points(stroke_width)
 
        # Convert Y coordinate: PDF uses bottom-left origin
        y_point = self.page_height - y_points - height_points
 
        # Set stroke color
        if stroke_color:
            self.canvas.setStrokeColor(colors.HexColor(stroke_color))
        else:
            self.canvas.setStrokeColor(colors.black)
 
        # Set fill color
        is_fill = 0
        if fill_color:
            self.canvas.setFillColor(colors.HexColor(fill_color))
            is_fill = 1
 
        # Set stroke width
        self.canvas.setLineWidth(stroke_width_points)
 
        # Draw rectangle
        self.canvas.rect(x_points, y_point, width_points, height_points,
                        stroke=stroke, fill=is_fill)
 
    def draw_line(self, x1: float, y1: float, x2: float, y2: float,
                  stroke_width: float = 1, stroke_color: Optional[str] = None) -> None:
        """
        Draw line with automatic unit conversion
        
        Args:
            x1: Start X in PIXELS
            y1: Start Y in PIXELS
            x2: End X in PIXELS
            y2: End Y in PIXELS
            stroke_width: Line width in PIXELS
            stroke_color: Line color as hex string
        
        Example:
            renderer.draw_line(x1=50, y1=100, x2=550, y2=100,
                             stroke_width=2, stroke_color='#000000')
        """
        # Convert px to points
        x1_points = self._convert_px_to_points(x1)
        y1_points = self._convert_px_to_points(y1)
        x2_points = self._convert_px_to_points(x2)
        y2_points = self._convert_px_to_points(y2)
        stroke_width_points = self._convert_px_to_points(stroke_width)
 
        # Convert Y coordinates (PDF origin at bottom-left)
        y1_point = self.page_height - y1_points
        y2_point = self.page_height - y2_points
 
        # Set stroke color
        if stroke_color:
            self.canvas.setStrokeColor(colors.HexColor(stroke_color))
        else:
            self.canvas.setStrokeColor(colors.black)
 
        # Set stroke width
        self.canvas.setLineWidth(stroke_width_points)
 
        # Draw line
        self.canvas.line(x1_points, y1_point, x2_points, y2_point)



class QRCodeGenerator:
    """Generates UPI QR codes"""

    @staticmethod
    def generate(amount: float, transaction_note: str,
                 company_name: str, upi_id: str,
                 output_path: Path) -> None:
        try:
            if not upi_id:
                return
            upi_url = (f"upi://pay?pa={upi_id}&pn={company_name}"
                      f"&am={amount}&tn={transaction_note}&cu=INR")
            qr = qrcode.make(upi_url)
            qr.save(str(output_path))
        except Exception as e:
            messagebox.showerror("UPI Error", f"An error occurred: {e}")


Number = Union[int, float, str, Decimal]

class NumberFormatter:
    MAX_INT_DIGITS = 9
    MAX_DECIMALS = 3
    _DIGITS = ("Zero", "One", "Two", "Three", "Four",
               "Five", "Six", "Seven", "Eight", "Nine")

    @staticmethod
    def _to_decimal(amount: Number) -> Decimal:
        if isinstance(amount, bool) or amount is None:
            raise TypeError(f"Unsupported amount type: {type(amount).__name__}")
        try:
            value = Decimal(str(amount).strip().replace(",", ""))
        except (InvalidOperation, ValueError) as exc:
            raise ValueError(f"Invalid amount: {amount!r}") from exc
        if not value.is_finite():
            raise ValueError(f"Amount must be finite: {amount!r}")
        value = value.quantize(Decimal(1).scaleb(-NumberFormatter.MAX_DECIMALS),
                               rounding=ROUND_HALF_UP)
        if len(str(abs(value).to_integral_value())) > NumberFormatter.MAX_INT_DIGITS:
            raise ValueError(f"Amount exceeds {NumberFormatter.MAX_INT_DIGITS} digits: {amount!r}")
        return value

    @classmethod
    def _words(cls, value: Decimal, currency: str) -> str:
        sign = "Minus " if value < 0 else ""
        value = abs(value)
        whole = int(value)
        frac = f"{value:.{cls.MAX_DECIMALS}f}".split(".")[1].rstrip("0")

        def to_words(n: int) -> str:
            return num2words(n, lang="en_IN").replace("-", " ").replace(",", "").title()

        text = to_words(whole)
        if frac:
            zeros = len(frac) - len(frac.lstrip("0"))
            text += " Point " + "Zero " * zeros + to_words(int(frac))
        return f"{sign}{text} {currency} Only"

    @staticmethod
    def _wrap(text: str, max1: int, max2: int) -> Optional[Tuple[str, str]]:
        words, line1, length = text.split(), [], 0
        for word in words:
            if length + len(word) + (1 if line1 else 0) > max1:
                break
            length += len(word) + (1 if line1 else 0)
            line1.append(word)
        line2 = " ".join(words[len(line1):])
        if len(line2) > max2 or not line1:
            return None
        return " ".join(line1), line2

    @classmethod
    def amount_to_words(cls, amount: Number, max1: int = 88, max2: int = 88) -> Tuple[str, str]:
        """Returns (line1, line2). Raises ValueError/TypeError on invalid input or overflow."""
        value = cls._to_decimal(amount)
        for currency, l1, l2 in (("Rupees", max1, max2), ("Rs.", max1, max2), ("Rs.", 51, 51)):
            result = cls._wrap(cls._words(value, currency), l1, l2)
            if result:
                return result
        raise ValueError(f"Amount text does not fit the available lines: {amount!r}")

    

class DatabaseLoader:
    """Loads invoice data from database"""

    @staticmethod
    def load_invoice_data(client_id: int, invoice_no: int) -> InvoiceData:
        """Load all invoice data"""
        client_details = fetch_data(
            f"SELECT id, name, contact_no, gst, city, state, client_type FROM Clients WHERE id = {client_id}"
        )[0]

        client_type = client_details[6]
        invoice_table = "Invoices" if client_type == "Client" else "Purchase"
        item_table = "InvoiceItems" if client_type == "Client" else "PurchaseItems"
        invoice_no_prefix_value = "INV" if client_type == "Client" else "PUR"

        invoice_details = fetch_data(
            f"""SELECT client_id, invoice_no, Invoice_type, date, due_date, total, reference_no, remarks 
               FROM {invoice_table} 
               WHERE client_id = {client_id} AND invoice_no = {invoice_no}"""
        )[0]

        subtotal = float(fetch_data(
            f'SELECT SUM(subtotal) FROM {item_table} '
            f'WHERE invoice_no = {invoice_no} AND client_id = {client_id}'
        )[0][0] or 0)

        discount = float(fetch_data(
            f'SELECT SUM(discount_amount) FROM {item_table} '
            f'WHERE invoice_no = {invoice_no} AND client_id = {client_id}'
        )[0][0] or 0)

        total_taxes = float(fetch_data(
            f'SELECT SUM(taxes) FROM {item_table} '
            f'WHERE invoice_no = {invoice_no} AND client_id = {client_id}'
        )[0][0] or 0)

        gross_total = float(fetch_data(
            f'SELECT SUM(Total) FROM {item_table} '
            f'WHERE invoice_no = {invoice_no} AND client_id = {client_id}'
        )[0][0] or 0)

        items = fetch_data(
            f'''SELECT 
                    item_name, item_code, quantity, unit, price, subtotal, discount_amount, discount_percent, GST_Rate, taxes, Total  
                FROM {item_table} 
                WHERE client_id = ? AND invoice_no = ?''',
            (client_id, invoice_no)
        )

        taxable_amount = subtotal - discount
        cgst = sgst = igst = 0.0

        company_state = read_ini("PROFILE", "state")
        if client_details[5] == company_state:
            cgst = sgst = total_taxes / 2
        else:
            igst = total_taxes

        round_off = round(taxable_amount + total_taxes) - gross_total
        grand_total = gross_total + round_off

        return InvoiceData(
            client_id=client_id,
            invoice_no_prefix=invoice_no_prefix_value,
            invoice_no=invoice_no,
            invoice_type=invoice_details[2],
            subtotal=round(subtotal, 2),
            discount=round(discount, 2),
            total_taxes=round(total_taxes, 2),
            gross_total=round(gross_total, 2),
            round_off=round(round_off, 2),
            grand_total=round(grand_total, 2),
            cgst=round(cgst, 2),
            sgst=round(sgst, 2),
            igst=round(igst, 2),
            taxable_amount=round(taxable_amount, 2),
            items=items,
            client_details=client_details,
            invoice_details=invoice_details
        )


# ============================================================================
# INVOICE RENDERER
# ============================================================================

class InvoiceRenderer:
    """Invoice rendering engine - each method is self-contained"""

    def __init__(self):
        self.canvas = None
        self.renderer = None
        self._register_fonts()

    def _register_fonts(self) -> None:
        """Register all required fonts"""
        fonts = {
            'Inter-Bold': 'Inter-Bold.ttf',
            'Inter-Medium': 'Inter-Medium.ttf',
            'Inter': 'Inter-Regular.ttf',


        }
        for font_name, font_file in fonts.items():
            pdfmetrics.registerFont(
                TTFont(font_name, generate_path(cfg.FONT_PATH, font_file))
            )

    # ========================================================================
    # RENDER METHODS - Each method is self-contained with full render logic
    # ========================================================================

    def render_header(self, company: CompanyInfo) -> None:
        """Render header with company name"""
        if not cfg.HEADER_ENABLED:
            return

        # Draw company name
        self.renderer.draw_text(
            text=company.name,
            x=30.31,
            y=31.91,
            height=25.76,
            font_name=cfg.FONT_HEADING, 
            font_size=cfg.FONT_SIZE_HEADER_PX,
            text_color=cfg.COLOR_TEXT,
            alignment='L'
        )

        # Draw TAX INVOICE
        self.renderer.draw_text(
            text="INVOICE",
            x=30.31,
            y=31.91,
            height=25.76,
            font_name=cfg.FONT_HEADING, 
            font_size=cfg.FONT_SIZE_HEADER_PX,
            text_color=cfg.COLOR_TEXT,
            alignment='R'
        )

    def render_company_info(self, company: CompanyInfo) -> None:
        """Render company contact information"""
        if not cfg.COMPANY_INFO_ENABLED:
            return

        address_line = f"{company.city}, {company.state}, {company.country} - {company.pin_code}"

        # Address Line 1
        self.renderer.draw_text(
            text=company.address,
            x=30.31,
            y=83,
            height=15.91,
            font_name=cfg.FONT_BODY, 
            font_size=cfg.FONT_SIZE_SUBHEADER_PX,
            text_color=cfg.COLOR_TEXT,
            alignment='L'
        )

        # Address Line 2
        self.renderer.draw_text(
            text=address_line,
            x=30.31,
            y=101,
            height=15.91,
            font_name=cfg.FONT_BODY, 
            font_size=cfg.FONT_SIZE_SUBHEADER_PX,
            text_color=cfg.COLOR_TEXT,
            alignment='L'
        )

        # Phone No.
        contact_text = f"{cfg.CONTACT_COUNTRY_CODE} {company.phone}"

        self.renderer.draw_text(
            text=contact_text,
            x=30.31,
            y=118,
            height=15.91,
            font_name=cfg.FONT_BODY, 
            font_size=cfg.FONT_SIZE_SUBHEADER_PX,
            text_color=cfg.COLOR_TEXT,
            alignment='L'
        )

        # Email id
        self.renderer.draw_text(
            text=company.email,
            x=30.31,
            y=135,
            height=15.91,
            font_name=cfg.FONT_BODY, 
            font_size=cfg.FONT_SIZE_SUBHEADER_PX,
            text_color=cfg.COLOR_TEXT,
            alignment='L'
        )

        # GSTIN

        gstin = f"GSTIN:  {company.gstin}"

        self.renderer.draw_text(
            text=gstin,
            x=30.31,
            y=155,
            height=15.91,
            font_name=cfg.FONT_HEADING, 
            font_size=cfg.FONT_SIZE_SUBHEADER_PX,
            text_color=cfg.COLOR_TEXT,
            alignment='L'
        )

    def render_invoice_details(self, invoice_data: InvoiceData) -> None:
        """Render invoice type and client details"""
        if not cfg.INVOICE_DETAILS_ENABLED:
            return

        # Determine invoice type display text
        display_type = ("Tax Invoice" if invoice_data.invoice_type == "GST Sales"
                        else "Bill of Supply")
        formatted_invoice_no = str(invoice_data.invoice_no_prefix) + str(invoice_data.invoice_no).zfill(3)

        self.renderer.draw_rect(
            x=449,
            y=82,
            width=315,
            height=95,
            fill_color=cfg.COLOR_BG_LIGHT
        )

        # ========================================================
        # Text Label
        # ========================================================

        # Invoice No - Label
        self.renderer.draw_text(
            text="Invoice Number :",
            x=469,
            y=92,
            height=15,
            font_name=cfg.FONT_SUBHEADING, 
            font_size=cfg.FONT_SIZE_LABEL_PX,
            text_color=cfg.COLOR_TEXT,
            alignment='L'
        )

        # Invoice Date - Label
        self.renderer.draw_text(
            text="Invoice Date :",
            x=469,
            y=111,
            height=15,
            font_name=cfg.FONT_SUBHEADING, 
            font_size=cfg.FONT_SIZE_LABEL_PX,
            text_color=cfg.COLOR_TEXT,
            alignment='L'
        )

        # Due date - Label
        self.renderer.draw_text(
            text="Due Date :",
            x=469,
            y=130,
            height=15,
            font_name=cfg.FONT_SUBHEADING, 
            font_size=cfg.FONT_SIZE_LABEL_PX,
            text_color=cfg.COLOR_TEXT,
            alignment='L'
        )

        # Invoice Type - Label
        self.renderer.draw_text(
            text="Invoice Type :",
            x=469,
            y=149,
            height=15,
            font_name=cfg.FONT_SUBHEADING, 
            font_size=cfg.FONT_SIZE_LABEL_PX,
            text_color=cfg.COLOR_TEXT,
            alignment='L'
        )


        # ========================================================
        # Value Label
        # ========================================================

        # Invoice No - Value
        self.renderer.draw_text(
            text=formatted_invoice_no,
            x=577,
            y=92,
            height=15,
            font_name=cfg.FONT_BODY, 
            font_size=cfg.FONT_SIZE_VALUE_PX,
            text_color=cfg.COLOR_TEXT,
            alignment='L'
        )

        # Invoice Date - Value
        self.renderer.draw_text(
            text=invoice_data.invoice_details[3],
            x=577,
            y=111,
            height=15,
            font_name=cfg.FONT_BODY, 
            font_size=cfg.FONT_SIZE_VALUE_PX,
            text_color=cfg.COLOR_TEXT,
            alignment='L'
        )

        # Due date - Value
        self.renderer.draw_text(
            text=invoice_data.invoice_details[4],
            x=577,
            y=130,
            height=15,
            font_name=cfg.FONT_BODY, 
            font_size=cfg.FONT_SIZE_VALUE_PX,
            text_color=cfg.COLOR_TEXT,
            alignment='L'
        )

        # Invoice Type - Value
        self.renderer.draw_text(
            text=display_type,
            x=577,
            y=149,
            height=15,
            font_name=cfg.FONT_BODY, 
            font_size=cfg.FONT_SIZE_VALUE_PX,
            text_color=cfg.COLOR_TEXT,
            alignment='L'
        )

    def render_customer_details(self, invoice_data: InvoiceData) -> None:
        """Render invoice type and client details"""
        if not cfg.CUSTOMER_DETAILS_ENABLED:
            return


        self.renderer.draw_rect(
            x=30,
            y=194,
            width=736,
            height=26,
            fill_color=cfg.COLOR_BG_DARK,
            stroke=1,
            stroke_color=cfg.COLOR_BG_DARK,
            stroke_width=0.76
        )
        self.renderer.draw_rect(
            x=30,
            y=220,
            width=736,
            height=105,
            fill_color=None,
            stroke=1,
            stroke_color=cfg.COLOR_BG_DARK,
            stroke_width=0.76

        )


        self.renderer.draw_text(
            text="BILLED TO",
            x=42,
            y=196,
            height=17,
            font_name=cfg.FONT_SUBHEADING, 
            font_size=cfg.FONT_SIZE_SUBHEADER_PX,
            text_color=cfg.COLOR_TEXT_BG,
            alignment='L'
        )


        # Customer Name - label
        self.renderer.draw_text(
            text="Customer Name :",
            x=42,
            y=230,
            height=17,
            font_name=cfg.FONT_SUBHEADING, 
            font_size=cfg.FONT_SIZE_LABEL_PX,
            text_color=cfg.COLOR_TEXT,
            alignment='L'
        )

        # Customer Address - label
        self.renderer.draw_text(
            text="Customer Address :",
            x=42,
            y=253,
            height=17,
            font_name=cfg.FONT_SUBHEADING, 
            font_size=cfg.FONT_SIZE_LABEL_PX,
            text_color=cfg.COLOR_TEXT,
            alignment='L'
        )

        # Customer Contact - label
        self.renderer.draw_text(
            text="Customer Contact :",
            x=42,
            y=276,
            height=17,
            font_name=cfg.FONT_SUBHEADING, 
            font_size=cfg.FONT_SIZE_LABEL_PX,
            text_color=cfg.COLOR_TEXT,
            alignment='L'
        )

        # Customer GSTIN - label
        self.renderer.draw_text(
            text="Customer GSTIN :",
            x=42,
            y=298,
            height=17,
            font_name=cfg.FONT_SUBHEADING, 
            font_size=cfg.FONT_SIZE_LABEL_PX,
            text_color=cfg.COLOR_TEXT,
            alignment='L'
        )



        # Customer Name - Value
        self.renderer.draw_text(
            text=invoice_data.client_details[1],
            x=155,
            y=230,
            height=17,
            font_name=cfg.FONT_BODY, 
            font_size=cfg.FONT_SIZE_VALUE_PX,
            text_color=cfg.COLOR_TEXT,
            alignment='L'
        )

        # Customer Address - Value
        address_line = f"{invoice_data.client_details[4]}, {invoice_data.client_details[5]}"
        self.renderer.draw_text(
            text=address_line,
            x=155,
            y=253,
            height=17,
            font_name=cfg.FONT_BODY, 
            font_size=cfg.FONT_SIZE_VALUE_PX,
            text_color=cfg.COLOR_TEXT,
            alignment='L'
        )

        # Customer Contact - Value
        contact_text = f"{cfg.CONTACT_COUNTRY_CODE} {invoice_data.client_details[2]}"
        self.renderer.draw_text(
            text=contact_text,
            x=155,
            y=276,
            height=17,
            font_name=cfg.FONT_BODY, 
            font_size=cfg.FONT_SIZE_VALUE_PX,
            text_color=cfg.COLOR_TEXT,
            alignment='L'
        )

        # Customer GSTIN - Value
        self.renderer.draw_text(
            text=invoice_data.client_details[3],
            x=155,
            y=298,
            height=17,
            font_name=cfg.FONT_BODY, 
            font_size=cfg.FONT_SIZE_VALUE_PX,
            text_color=cfg.COLOR_TEXT,
            alignment='L'
        )

    def render_items_table(self, invoice_data: InvoiceData) -> None:
        """Render items table"""
        if not cfg.ITEMS_TABLE_ENABLED:
            return

        # Build table data
        header = [name for name, _ in cfg.ITEMS_TABLE_COLUMNS]
        col_widths = [width for _, width in cfg.ITEMS_TABLE_COLUMNS]


        header_style = ParagraphStyle(
            name='TableHeader',
            fontName=cfg.FONT_SUBHEADING,
            fontSize=cfg.FONT_SIZE_TINY_PX,
            alignment=TA_CENTER,
            wordWrap='LTR',
            textColor=colors.HexColor(cfg.COLOR_TEXT_BG),  # Header text color
        )

        wrapped_header = [Paragraph(cell, header_style) for cell in header]


        table_data = [wrapped_header] 

        for sr_no, item in enumerate(invoice_data.items, 1):
            item_name, item_code, quantity, unit, price, subtotal, discount_amount, discount_percent, GST_Rate, taxes, Total = item
            table_data.append([
                sr_no,
                item_name, 
                item_code,
                f"{quantity} {unit}",
                price, 
                f"{discount_percent}% ({discount_amount})",
                subtotal - discount_amount,
                f"{GST_Rate}% ({taxes})",
                Total
            ])

        # Create table
        table = Table(table_data, colWidths=col_widths)

        # Style table
        style = TableStyle([
            # Header styling
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(cfg.COLOR_BG_DARK)),  # Header background
            ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),  # Header vertical alignment
            ('ROWHEIGHT', (0, 0), (-1, 0), 44),  # Header height 44px
            
            # Data rows styling
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor(cfg.COLOR_BG)),  # Data background
            ('TEXTCOLOR', (0, 1), (-1, -1), cfg.COLOR_TEXT),   # Data Color
            ('FONTNAME', (0, 1), (-1, -1), cfg.FONT_BODY),  # Data font family
            ('FONTSIZE', (0, 1), (-1, -1), 7.5),  # Data font size 8px
            ('VALIGN', (0, 1), (-1, -1), 'MIDDLE'),  # Data vertical alignment
            ('ROWHEIGHT', (0, 1), (-1, -1), 23),  # Data row height
            
            # Global styling
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),  # Center align all cells
            ('GRID', (0, 0), (-1, -1), 0.75, colors.HexColor(cfg.COLOR_BORDER)),  # Grid borders
        ])
        table.setStyle(style)

        # Draw table frame
        frame = Frame(
            x1=21.5,     
            y1=309.0, 
            width=553, 
            height=288.75,
            showBoundary=0
        )
        frame.addFromList([table], self.canvas)

        # Draw table border box
        self.renderer.draw_rect(
            x=30,
            y=334,
            width=735,
            height=385,
            fill_color=None,
            stroke=1,
            stroke_color=cfg.COLOR_BORDER,
            stroke_width=0.76

        )

    def render_amounts_text(self, invoice_data: InvoiceData) -> None:
        """Render amounts in words section"""
        if not cfg.AMOUNTS_TEXT_ENABLED:
            return

        self.renderer.draw_rect(
            x=30,
            y=727,
            width=383,
            height=63,
            fill_color=cfg.COLOR_BG_LIGHT
        )

        # Grand Total in words
        total_line1, total_line2 = NumberFormatter.amount_to_words(
            # amount = 777777777.33
            invoice_data.grand_total
        )
        self.renderer.draw_text(
            text="Amount in Words",
            x=42,
            y=737,
            height=15,
            font_name=cfg.FONT_HEADING, 
            font_size=cfg.FONT_SIZE_LABEL_PX,
            text_color=cfg.COLOR_TEXT,
            alignment='L'
        )

        self.renderer.draw_text(
            text=total_line1,
            x=42,
            y=752,
            height=15,
            font_name=cfg.FONT_BODY, 
            font_size=cfg.FONT_SIZE_SMALL_PX,
            text_color=cfg.COLOR_TEXT,
            alignment='L'
        )

        self.renderer.draw_text(
            text=total_line2,
            x=42,
            y=766,
            height=15,
            font_name=cfg.FONT_BODY, 
            font_size=cfg.FONT_SIZE_SMALL_PX,
            text_color=cfg.COLOR_TEXT,
            alignment='L'
        )

    def render_reference_details(self, invoice_data: InvoiceData) -> None:
        """Render reference details section"""
        if not cfg.REFERENCE_DETAILS_ENABLED:
            return

        self.renderer.draw_rect(
            x=30,
            y=800,
            width=383,
            height=120,
            fill_color=cfg.COLOR_BG_LIGHT
        )

        self.renderer.draw_text(
            text="Reference",
            x=42,
            y=811,
            height=15,
            font_name=cfg.FONT_HEADING, 
            font_size=cfg.FONT_SIZE_LABEL_PX,
            text_color=cfg.COLOR_TEXT,
            alignment='L'
        )

        # Reference Number

        self.renderer.draw_text(
            text="Reference Number :",
            x=42,
            y=832,
            height=15,
            font_name=cfg.FONT_SUBHEADING, 
            font_size=cfg.FONT_SIZE_SMALL_PX,
            text_color=cfg.COLOR_TEXT,
            alignment='L'
        )

        self.renderer.draw_text(
            text=invoice_data.invoice_details[6],
            # text="Nothing",
            x=125,
            y=832,
            height=15,
            font_name=cfg.FONT_BODY, 
            font_size=cfg.FONT_SIZE_SMALL_PX,
            text_color=cfg.COLOR_TEXT,
            alignment='L'
        )

        # Remark Details

        self.renderer.draw_text(
            text="Remark Details :",
            x=42,
            y=851,
            height=15,
            font_name=cfg.FONT_SUBHEADING, 
            font_size=cfg.FONT_SIZE_SMALL_PX,
            text_color=cfg.COLOR_TEXT,
            alignment='L'
        )

        # 1. Format text (max 63 chars/line, up to 3 lines)
        lines = textwrap.wrap(str(invoice_data.invoice_details[7]), width=63)[:3]
        text = "<br/>".join(lines)

        # 2. Style (font size converted: px * 0.75)
        font_size = cfg.FONT_SIZE_SMALL_PX * 0.75
        style = ParagraphStyle(
            "invoice_detail",
            fontName=cfg.FONT_BODY,
            fontSize=font_size,
            leading=font_size * 1.2,
            textColor=cfg.COLOR_TEXT,
            alignment=TA_LEFT,
        )

        # 3. Draw directly onto the canvas (42 px = 31.5 pt, 870 px = 652.5 pt)
        p = Paragraph(text, style)
        w, h = p.wrap(315, 24)  # 24 pt = 32 px
        p.drawOn(self.renderer.canvas, 31.5, 168)

    def render_qr_code(self, company: CompanyInfo,
                        invoice_data: InvoiceData) -> None:
        """Render QR code"""
        if not cfg.QR_CODE_ENABLED:
            return

        formatted_invoice_no = "INV" + str(invoice_data.invoice_no).zfill(3)
        qr_output = generate_path("utilities", "assets", "qr.png")

        # Generate QR code
        QRCodeGenerator.generate(
            invoice_data.grand_total,
            f"{formatted_invoice_no}-{invoice_data.client_details[1]}",
            company.name,
            company.upi,
            qr_output
        )

        # Draw QR code
        self.canvas.drawImage(
            str(qr_output),
            cfg.QR_CODE_X,
            cfg.PAGE_HEIGHT - cfg.QR_CODE_Y - cfg.QR_CODE_HEIGHT,
            cfg.QR_CODE_WIDTH,
            cfg.QR_CODE_HEIGHT
        )

    def render_summary(self, invoice_data: InvoiceData) -> None:
        """Render financial summary section"""
        if not cfg.SUMMARY_ENABLED:
            return


        self.renderer.draw_rect(
            x=420,
            y=727,
            width=345,
            height=191.5,
            fill_color=None,
            stroke=1,
            stroke_color=cfg.COLOR_BORDER,
            stroke_width=0.76
        )

        self.renderer.draw_rect(
            x=420.5,
            y=898,
            width=344,
            height=20.2,
            fill_color=cfg.COLOR_BG_DARK
        )

        
        y = 731  # Start from top
        y_offset = 1

        # Render each summary field from config
        for label, key, is_bold in cfg.SUMMARY_FIELDS:
            value = getattr(invoice_data, key)
            font = cfg.FONT_SUBHEADING if is_bold else cfg.FONT_BODY
            color = cfg.COLOR_TEXT_BG if (key == 'grand_total') else cfg.COLOR_TEXT

            # Label (left side)
            self.renderer.draw_text(
                text=label,
                x=434,
                y=y + y_offset,  # Add offset (moves down from top)
                height=13,
                font_name=font,
                font_size=cfg.FONT_SIZE_LABEL_PX,
                text_color=color,
                alignment='L'
            )

            # Value (right side)
            self.renderer.draw_text(
                text=str(value),
                x=43,
                y=y + y_offset,  # Add offset (moves down from top)
                height=13,
                font_name=font,
                font_size=cfg.FONT_SIZE_VALUE_PX,
                text_color=color,
                alignment='R'
            )

            self.renderer.draw_line(
                x1=420,
                y1= y + y_offset + 18,
                x2=765,
                y2= y + y_offset + 18,
                stroke_width=0.53,
                stroke_color=cfg.COLOR_BORDER,

            )

            y_offset += 21.1  # Move down 20px for next row

    def render_footer(self, company: CompanyInfo) -> None:
        """Render footer with terms and signature"""
        if not cfg.FOOTER_ENABLED:
            return

        # Draw footer box
        self.renderer.draw_rect(
            x=30,
            y=930,
            width=736,
            height=148,
            fill_color=None,
            stroke=1,
            stroke_color=cfg.COLOR_BG_DARK,
            stroke_width=0.76
        )


        self.renderer.draw_text(
            text="Bank / Payment Details",
            x=42,
            y=940,
            height=18,
            font_name=cfg.FONT_HEADING, 
            font_size=cfg.FONT_SIZE_SUBHEADER_PX,
            text_color=cfg.COLOR_TEXT,
            alignment='L'
        )


        self.renderer.draw_text(
            text="Terms & Conditions",
            x=264,
            y=940,
            height=18,
            font_name=cfg.FONT_HEADING, 
            font_size=cfg.FONT_SIZE_SUBHEADER_PX,
            text_color=cfg.COLOR_TEXT,
            alignment='L'
        )


        # Payment details - each can be customized individually

        self.renderer.draw_text("Bank Name :", 42, 966, 15,
                            font_name=cfg.FONT_SUBHEADING,
                            font_size=cfg.FONT_SIZE_LABEL_PX,
                            text_color=cfg.COLOR_TEXT)
        self.renderer.draw_text(company.bank, 120, 966, 15,
                            font_name=cfg.FONT_BODY,
                            font_size=cfg.FONT_SIZE_VALUE_PX,
                            text_color=cfg.COLOR_TEXT)

        self.renderer.draw_text("Account Number :", 42, 990, 15,
                            font_name=cfg.FONT_SUBHEADING,
                            font_size=cfg.FONT_SIZE_LABEL_PX,
                            text_color=cfg.COLOR_TEXT)
        self.renderer.draw_text(company.acc_no, 120, 990, 15,
                            font_name=cfg.FONT_BODY,
                            font_size=cfg.FONT_SIZE_VALUE_PX,
                            text_color=cfg.COLOR_TEXT)

        self.renderer.draw_text("IFSC Code :", 42, 1013, 15,
                            font_name=cfg.FONT_SUBHEADING,
                            font_size=cfg.FONT_SIZE_LABEL_PX,
                            text_color=cfg.COLOR_TEXT)
        self.renderer.draw_text(company.ifsc, 120, 1013, 15,
                            font_name=cfg.FONT_BODY,
                            font_size=cfg.FONT_SIZE_VALUE_PX,
                            text_color=cfg.COLOR_TEXT)

        self.renderer.draw_text("UPI/Payment :", 42, 1037, 15,
                            font_name=cfg.FONT_SUBHEADING,
                            font_size=cfg.FONT_SIZE_LABEL_PX,
                            text_color=cfg.COLOR_TEXT)
        self.renderer.draw_text(company.upi, 120, 1037, 15,
                            font_name=cfg.FONT_BODY,
                            font_size=cfg.FONT_SIZE_VALUE_PX,
                            text_color=cfg.COLOR_TEXT)


        # Policy lines
        for i in range(1, 6):
            policy_line = read_ini("POLICY", f"line{i}")
            current_y = 965 + (i - 1) * 18
            self.renderer.draw_text(
                policy_line, 264, current_y, 15,
                font_name=cfg.FONT_BODY,
                font_size=cfg.FONT_SIZE_SMALL_PX,
                text_color=cfg.COLOR_TEXT
            )

    def render_signblock(self, company: CompanyInfo) -> None:
        """Render Sign block"""
        if not cfg.SIGN_BLOCK_ENABLED:
            return    

        self.renderer.draw_text(
            text=f"For {company.name},",
            x=575,
            y=940,
            height=18,
            font_name=cfg.FONT_HEADING, 
            font_size=cfg.FONT_SIZE_SUBHEADER_PX,
            text_color=cfg.COLOR_TEXT,
            alignment='L'
        )

        self.renderer.draw_line(
            x1=575,
            y1=1048,
            x2=738,
            y2=1048,
            stroke_width=0.76,
            stroke_color=cfg.COLOR_BG_DARK,
        )

    def render_footer_text(self) -> None:
       
        if not cfg.FOOTER_TEXT_ENABLED:
            return

        self.renderer.draw_line(
            x1=30,
            y1=1096,
            x2=297,
            y2=1096,
            stroke_width=0.76,
            stroke_color=cfg.COLOR_BG_DARK,
        )

        self.renderer.draw_text(
            text="Thank You for Your Business",
            x=310,
            y=1082,
            height=18,
            font_name=cfg.FONT_SUBHEADING, 
            font_size=cfg.FONT_SIZE_LABEL_PX,
            text_color=cfg.COLOR_TEXT,
            alignment='C'
        )

        self.renderer.draw_line(
            x1=498,
            y1=1096,
            x2=765,
            y2=1096,
            stroke_width=0.76,
            stroke_color=cfg.COLOR_BG_DARK,
        )





    # ========================================================================
    # MAIN RENDER METHOD - Orchestrates all rendering
    # ========================================================================

    def render(self, client_id: int, invoice_no: int, output_path: Path) -> None:
        """Main render orchestrator - calls all section methods"""
        # Load data
        company = CompanyInfo.from_ini()
        invoice_data = DatabaseLoader.load_invoice_data(client_id, invoice_no)

        # Create canvas
        self.canvas = Canvas(
            str(output_path),
            pagesize=[cfg.PAGE_WIDTH, cfg.PAGE_HEIGHT]
        )
        self.renderer = TextRenderer(self.canvas)

        # Render all sections (each is self-contained)

        self.render_header(company)
        self.render_company_info(company)
        self.render_invoice_details(invoice_data)
        self.render_customer_details(invoice_data)
        self.render_items_table(invoice_data)
        self.render_amounts_text(invoice_data)
        self.render_reference_details(invoice_data)
        self.render_qr_code(company, invoice_data)
        self.render_summary(invoice_data)
        self.render_footer(company)
        self.render_signblock(company)
        self.render_footer_text()


        # Save PDF
        self.canvas.save()


def create_invoice(client_id: int, invoice_no: int, output_path: Path) -> None:
    """Public API to create invoice"""
    renderer = InvoiceRenderer()
    renderer.render(client_id, invoice_no, output_path)


if __name__ == "__main__":
    create_invoice(1, 1, Path("invoice_output.pdf"))