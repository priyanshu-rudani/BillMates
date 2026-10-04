"""
Invoice Configuration - Settings Only
No rendering logic, just settings and measurements in pixels (px)
"""

# ============================================================================
# PX TO POINTS CONVERSION
# ============================================================================
PX_UNIT = 0.75  # 1 px = 0.75 point (96 DPI equivalent)

# ============================================================================
# PAGE SETUP (in pixels)
# ============================================================================
PAGE_WIDTH_PX = 794      # A4 width
PAGE_HEIGHT_PX = 1123     # A4 height

PAGE_WIDTH = PAGE_WIDTH_PX * PX_UNIT
PAGE_HEIGHT = PAGE_HEIGHT_PX * PX_UNIT

# ============================================================================
# COLORS
# ============================================================================
COLOR_PRIMARY = "#174D87"
COLOR_BORDER = "#B8CCE0"
COLOR_TEXT = "#0E3863"
COLOR_TEXT_BG = "#FFFFFF"
COLOR_BG_DARK = "#174D87"
COLOR_BG_LIGHT = "#EDF5FA"   #  '#EDF5FA'
COLOR_BG = "#FFFFFF"


# ============================================================================
# FONTS
# ============================================================================
FONT_HEADING = "Inter-Bold"
FONT_SUBHEADING = "Inter-Medium"
FONT_BODY = "Inter"
FONT_PATH = "utilities/assets/Font"

# Font Sizes (in pixels)
FONT_SIZE_HEADER_PX = 22
FONT_SIZE_SUBHEADER_PX = 10
FONT_SIZE_LABEL_PX = 9
FONT_SIZE_VALUE_PX = 9
FONT_SIZE_SMALL_PX = 8
FONT_SIZE_TINY_PX = 7.5


# ============================================================================
# SECTION TOGGLES (Enable/Disable sections)
# ============================================================================
HEADER_ENABLED = True
COMPANY_INFO_ENABLED = True
INVOICE_DETAILS_ENABLED = True
CUSTOMER_DETAILS_ENABLED = True
ITEMS_TABLE_ENABLED = True
AMOUNTS_TEXT_ENABLED = True
REFERENCE_DETAILS_ENABLED = True
QR_CODE_ENABLED = True
SUMMARY_ENABLED = True
PAYMENT_INFO_ENABLED = True
FOOTER_ENABLED = True
SIGN_BLOCK_ENABLED= True
FOOTER_TEXT_ENABLED = True




# ============================================================================
# TABLE COLUMNS CONFIGURATION - EDIT THIS TO CUSTOMIZE TABLE
# ============================================================================
ITEMS_TABLE_COLUMNS_PX = [
    ("S.No.", 32),
    ("Item Description", 160),
    ("HSN/SAC Code", 77),
    ("Qty", 76),
    ("Rate (₹)", 75),
    ("Discount (%)", 75),
    ("Taxable Value (₹)", 83),
    ("Applicable Tax Rate (%)", 80),
    ("Total Amount (₹)", 77),
]

# Convert column widths to points
ITEMS_TABLE_COLUMNS = [
    (name, width * PX_UNIT) for name, width in ITEMS_TABLE_COLUMNS_PX
]


# ============================================================================
# SUMMARY FIELDS TO DISPLAY - EDIT THIS TO CUSTOMIZE SUMMARY
# ============================================================================

SUMMARY_FIELDS = [
    ("Subtotal (Taxable Value)", "subtotal", False),  # (label, key, is_bold)
    ("Total Discount", "discount", False),
    ("Taxable Value (After Discount)", "taxable_amount", True),
    ("CGST", "cgst", False),
    ("SGST", "sgst", False),
    ("IGST", "igst", False),
    ("Total Tax Amount", "total_taxes", False),
    ("Round Off", "round_off", False),
    ("Grand Total", "grand_total", True),
]


# ============================================================================
# QR CODE SECTION - MEASUREMENTS (pixels)
# ============================================================================
QR_CODE_X_PX = 300
QR_CODE_Y_PX = 813
QR_CODE_WIDTH_PX = 94
QR_CODE_HEIGHT_PX = 94

# Convert to points
QR_CODE_X = QR_CODE_X_PX * PX_UNIT
QR_CODE_Y = QR_CODE_Y_PX * PX_UNIT
QR_CODE_WIDTH = QR_CODE_WIDTH_PX * PX_UNIT
QR_CODE_HEIGHT = QR_CODE_HEIGHT_PX * PX_UNIT

# ============================================================================
# DATA LABELS - STRINGS
# ============================================================================

CONTACT_COUNTRY_CODE = "+91"



