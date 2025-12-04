import sys
from pathlib import Path

if getattr(sys, 'frozen', False):  # Running as a PyInstaller EXE
    root_path = Path(sys.executable).parent
else:  # Running as a Python script
    root_path = Path(__file__).parent.parent
sys.path.append(str(root_path))
 
from utilities.path_utils import generate_path, read_ini, fetch_data
from tkinter import messagebox
from reportlab.pdfgen.canvas import Canvas
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Frame, Table, TableStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.lib import colors
from num2words import num2words
import qrcode

def upi_qr(amount, transaction_note):
    try:
        upi_id = read_ini("PROFILE", "upi")
        if upi_id:
            upi_url = f"upi://pay?pa={upi_id}&am={amount}&cu=INR&tn={transaction_note}"
            qr = qrcode.make(upi_url)
            qr.save(generate_path("utilities", "assets", "qr.png"))
        else:
            return
    except Exception as e:
        messagebox.showerror("UPI Error", f"An error occurred: {e}")

def writeText(self, Text, X, Y, Height, fontName='Varela', fontSize=11, alignment=None):

    page_width = 595
    page_height = 842

    font_object = pdfmetrics.getFont(fontName)
    face = font_object.face
    descent_points = face.descent / 1000.0 * fontSize

    Y_Point = page_height - Y - Height - descent_points

    text_width = pdfmetrics.stringWidth(Text, fontName, fontSize)

    if alignment == 'C':
        X = (page_width - text_width) / 2
    elif alignment == 'R':
        X = page_width - (X + text_width)

    self.setFont(fontName, fontSize)
    self.setFillColor(colors.black)
    self.drawString(X, Y_Point, Text)

def drawRect(self, X, Y, width, height, stroke=1, fillColor=None):
    page_height = 842

    Y_point = page_height - Y - height

    if fillColor:
        self.setFillColor(colors.HexColor(fillColor))
        isFill = 1
    else:
        isFill = 0

    self.rect(X, Y_point, width, height-1, stroke, fill=isFill)

def number_to_words(amount):
    rupees_words = num2words(amount, lang='en_IN').title()
    formatted_text = f"{rupees_words} Rupees"

    def wrap_text(text, max_len1, max_len2):
        words_list = text.split()
        line1, line2 = [], []
        current_length = 0

        # Fill first line up to max_len1
        for word in words_list:
            if current_length + len(word) + 1 > max_len1:
                break
            line1.append(word)
            current_length += len(word) + 1

        # Fill second line up to max_len2
        line2 = words_list[len(line1):]
        if len(" ".join(line2)) > max_len2:
            return None, None  # Too long

        return " ".join(line1), " ".join(line2)

    max_len1, max_len2 = 51, 51

    # Try splitting with full text
    line1, line2 = wrap_text(formatted_text, max_len1, max_len2)
    if line1 and line2:
        return line1, line2

    if line1 is None or line2 is None:
        formatted_text = formatted_text.replace("Rupees", "Rs.").strip()  # Remove 'Rupees'
        line1, line2 = wrap_text(formatted_text, max_len1, max_len2)

    return line1, line2

def create_invoice(Client_ID: int, Invoice_No: int, f_path: Path, type: str = 'Original'):

    Compney_name = read_ini("PROFILE", "name")
    Compney_address = read_ini("PROFILE", "address")
    Compney_city = read_ini("PROFILE", "city")
    Compney_state = read_ini("PROFILE", "state")
    Compney_pin_code = read_ini("PROFILE", "pin_code")
    Compney_country = read_ini("PROFILE", "country")
    Compney_email = read_ini("PROFILE", "email")
    Compney_phone = read_ini("PROFILE", "phone")

    Compney_address_line = f"{Compney_city}, {Compney_state}, {Compney_country} - {Compney_pin_code}"

    Compney_upi = read_ini("PROFILE", "upi")
    Compney_bank = read_ini("PROFILE", "bank")
    Compney_acc_no = read_ini("PROFILE", "acc_no")
    Compney_IFSC = read_ini("PROFILE", "IFSC")

    pdfmetrics.registerFont(TTFont('P-Bold', generate_path("utilities", "assets", "Font", "Poppins-Bold.ttf")))
    pdfmetrics.registerFont(TTFont('P-SemiBold', generate_path("utilities", "assets", "Font","Poppins-SemiBold.ttf")))
    pdfmetrics.registerFont(TTFont('Varela', generate_path("utilities", "assets", "Font","VarelaRound-Regular.ttf")))

    width = 595
    height = 842
    
    pdf = Canvas(f_path, pagesize=[width, height])

    Canvas.writeText = writeText
    Canvas.drawRect = drawRect

    pdf.setFillColor(colors.HexColor('#C5D9F1'))
    pdf.rect(13, 792, 570, 34, stroke=1, fill=1)
    pdf.rect(13, 115, 348, 22, stroke=1, fill=1)
    pdf.rect(360, 115, 223, 22, stroke=1, fill=1)

    pdf.drawRect(13, 49, 570, 62)
    pdf.drawRect(13, 49, 570, 62)
    pdf.drawRect(13, 112, 570, 28)
    pdf.drawRect(13, 139, 347, 88)
    pdf.drawRect(360, 139, 223, 88)

    pdf.drawRect(13, 559, 347, 87)
    pdf.drawRect(13, 645, 347, 60)
    pdf.drawRect(360, 559, 223, 146)
    pdf.drawRect(13, 728, 570, 100)

    pdf.writeText(Compney_name, 0, 20, 25, 'Varela', 20, alignment='C')
    pdf.writeText(Compney_address, 0, 55, 14, 'Varela', 12, alignment='C')
    pdf.writeText(Compney_address_line, 0, 73, 14, 'Varela', 12, alignment='C')

    if Compney_email:
        pdf.writeText(f"+91 {Compney_phone}  |  {Compney_email}", 0, 91, 14, 'Varela', 12, alignment='C')
    else: 
        pdf.writeText(f"+91 {Compney_phone}", 0, 91, 14, 'Varela', 12, alignment='C')

    Clients_Detiles = fetch_data(f"SELECT * FROM Clients WHERE id = {Client_ID}")[0]

    if Clients_Detiles[6] == "Client":
        Invoice_table = "Invoices"
        Item_table = "InvoiceItems"
    elif Clients_Detiles[6] == "Supplier":
        Invoice_table = "Purchase"
        Item_table = "PurchaseItems"


    Invoice_Detiles = fetch_data(f"SELECT client_id, invoice_no, Invoice_type, date, due_date, total, reference_no FROM {Invoice_table} WHERE client_id = {Client_ID} AND invoice_no = {Invoice_No}")[0]

    Formated_InvoiceNo = "INV" + str(Invoice_No).zfill(3)

    if Invoice_Detiles[2] == "GST Sales":
        Invoice_Type = "Tax Invoice"
        Compney_gst = read_ini("PROFILE", "gstin")
        pdf.writeText(Clients_Detiles[3], 90, 211, 13, 'Varela', 11, alignment='L')
    elif Invoice_Detiles[2] == "Non-GST Sales":
        Invoice_Type = "Bill of Supply"
        Compney_gst = ''

    Sub_Total = fetch_data(f'SELECT SUM(subtotal) FROM {Item_table} WHERE invoice_no = {Invoice_No} AND client_id = {Client_ID}')[0][0]
    Discount = fetch_data(f'SELECT SUM(discount) FROM {Item_table} WHERE invoice_no = {Invoice_No} AND client_id = {Client_ID}')[0][0]
    Total_Taxes = fetch_data(f'SELECT SUM(taxes) FROM {Item_table} WHERE invoice_no = {Invoice_No} AND client_id = {Client_ID}')[0][0]
    Gross_Total = fetch_data(f'SELECT SUM(Total) FROM {Item_table} WHERE invoice_no = {Invoice_No} AND client_id = {Client_ID}')[0][0]

    Taxable_Amount = float(Sub_Total) - float(Discount)
    Total = Taxable_Amount + float(Total_Taxes)

    if Compney_state == Clients_Detiles[5]:
        Central_Tax = State_Tax = float(Total_Taxes) / 2
        Integrated_Tax = 0.0
    else: 
        Integrated_Tax = float(Total_Taxes)
        Central_Tax = State_Tax = 0.0

    Round_Off = round(Total) - float(Gross_Total)
    Grand_Total = Total + Round_Off

    Sub_Total = round(float(Sub_Total), 2)
    Discount = round(float(Discount), 2)
    Taxable_Amount = round(float(Taxable_Amount), 2)
    Central_Tax = round(float(Central_Tax), 2)
    State_Tax = round(float(State_Tax), 2)
    Integrated_Tax = round(float(Integrated_Tax), 2)
    Total_Taxes = round(float(Total_Taxes), 2)
    Round_Off = round(float(Round_Off), 2)
    Grand_Total = round(float(Grand_Total), 2)

    pdf.writeText(Invoice_Type, 0, 115, 20, 'P-Bold', 13, alignment='C')

    pdf.writeText("M/S :", 22, 140, 17, 'P-SemiBold', 11, alignment='L')
    pdf.writeText(Clients_Detiles[1], 60, 144, 13, 'Varela', 11, alignment='L')
    pdf.writeText(Clients_Detiles[2], 60, 160, 13, 'Varela', 11, alignment='L')
    pdf.writeText(Clients_Detiles[4], 60, 176, 13, 'Varela', 11, alignment='L')
    
    pdf.writeText("Place of Supply :", 22, 191, 17, 'P-SemiBold', 11, alignment='L')
    pdf.writeText(Clients_Detiles[5], 120, 194, 13, 'Varela', 11, alignment='L')
    
    pdf.writeText("GSTIN No :", 22, 208, 17, 'P-SemiBold', 11, alignment='L')
    
    pdf.writeText("Invoice No :", 370, 144, 13, 'P-SemiBold', 11, alignment='L')
    pdf.writeText(Formated_InvoiceNo, 452, 144, 13, 'Varela', 11, alignment='L')
    
    pdf.writeText("Invoice Date :", 370, 161, 13, 'P-SemiBold', 11, alignment='L')
    pdf.writeText(Invoice_Detiles[3], 452, 161, 13, 'Varela', 11, alignment='L')
    
    pdf.writeText("Due Date :", 370, 178, 13, 'P-SemiBold', 11, alignment='L')
    pdf.writeText(Invoice_Detiles[4], 452, 178, 13, 'Varela', 11, alignment='L')


    pdf.writeText("GSTIN No. :", 17, 561, 15, 'P-SemiBold', 10, alignment='L')
    pdf.writeText(Compney_gst, 85, 561, 15, 'Varela', 11, alignment='L')

    pdf.writeText("Bank Name :", 17, 578, 15, 'P-SemiBold', 10, alignment='L')
    pdf.writeText(Compney_bank, 85, 578, 15, 'Varela', 11, alignment='L')
 
    pdf.writeText("A/C No. :", 17, 595, 15, 'P-SemiBold', 10, alignment='L')
    pdf.writeText(Compney_acc_no, 85, 595, 15, 'Varela', 11, alignment='L')
    
    pdf.writeText("IFSC Code :", 17, 612, 15, 'P-SemiBold', 10, alignment='L')
    pdf.writeText(Compney_IFSC, 85, 612, 15, 'Varela', 11, alignment='L')
    
    pdf.writeText("UPI ID :", 17, 629, 15, 'P-SemiBold', 10, alignment='L')
    pdf.writeText(Compney_upi, 85, 629, 15, 'Varela', 11, alignment='L')


    pdf.writeText("Reference No. :", 17, 708, 15, 'P-SemiBold', 10, alignment='L')
    pdf.writeText(Invoice_Detiles[6], 97, 707.5, 15, 'Varela', 10, alignment='L')
   

    pdf.writeText("Sub Total", 366, 563, 15, 'P-SemiBold', 10, alignment='L')
    pdf.writeText(str(Sub_Total), 18, 565, 15, 'P-SemiBold', 10, alignment='R')

    pdf.writeText("Discount", 366, 580, 15, 'Varela', 10, alignment='L')
    pdf.writeText(str(Discount), 18, 580, 15, 'Varela', 10, alignment='R')

    pdf.writeText("Taxable Amount", 366, 598, 15, 'P-SemiBold', 10, alignment='L')
    pdf.writeText(str(Taxable_Amount), 18, 598, 15, 'P-SemiBold', 10, alignment='R')

    pdf.writeText("CGST", 366, 618, 15, 'Varela', 10, alignment='L')
    pdf.writeText(str(Central_Tax), 18, 618, 15, 'Varela', 10, alignment='R')

    pdf.writeText("SGST", 366, 635, 15, 'Varela', 10, alignment='L')
    pdf.writeText(str(State_Tax), 18, 635, 15, 'Varela', 10, alignment='R')

    pdf.writeText("IGST", 366, 652, 15, 'Varela', 10, alignment='L')
    pdf.writeText(str(Integrated_Tax), 18, 652, 15, 'Varela', 10, alignment='R')

    pdf.writeText("Total Taxes", 366, 670, 15, 'P-SemiBold', 10, alignment='L')
    pdf.writeText(str(Total_Taxes), 18, 670, 15, 'P-SemiBold', 10, alignment='R')

    pdf.writeText("Round Off", 366, 685, 15, 'Varela', 10, alignment='L')
    pdf.writeText(str(Round_Off), 18, 685, 15, 'Varela', 10, alignment='R')

    pdf.writeText("Grand Total", 366, 708, 15, 'P-SemiBold', 10, alignment='L')
    pdf.writeText(str(Grand_Total), 18, 708, 15, 'P-SemiBold', 10, alignment='R')

    taxes_line1, taxes_line2 = number_to_words(Total_Taxes)
    pdf.writeText("Total Taxes :", 17, 649, 15, 'P-SemiBold', 10, alignment='L')
    pdf.writeText(taxes_line1, 85, 649, 15, 'Varela', 10, alignment='L')
    pdf.writeText(taxes_line2, 85, 662, 15, 'Varela', 10, alignment='L')

    total_line1, total_line2 = number_to_words(Grand_Total)
    pdf.writeText("Bill Amount :", 17, 675, 15, 'P-SemiBold', 10, alignment='L')
    pdf.writeText(total_line1, 85, 675, 15, 'Varela', 10, alignment='L')
    pdf.writeText(total_line2, 85, 688, 15, 'Varela', 10, alignment='L')

    pdf.writeText("Terms & Condition:", 17, 732, 15, 'P-SemiBold', 10, alignment='L')

    pdf.writeText(read_ini("POLICY", "line1"), 25, 747, 15, 'Varela', 10, alignment='L')
    pdf.writeText(read_ini("POLICY", "line2"), 25, 762, 15, 'Varela', 10, alignment='L')
    pdf.writeText(read_ini("POLICY", "line3"), 25, 777, 15, 'Varela', 10, alignment='L')
    pdf.writeText(read_ini("POLICY", "line4"), 25, 792, 15, 'Varela', 10, alignment='L')
    pdf.writeText(read_ini("POLICY", "line5"), 25, 807, 15, 'Varela', 10, alignment='L')

    pdf.writeText(f"For, {Compney_name}", 18, 732, 15, 'Varela', 10, alignment='R')
    pdf.writeText("Authorized Signatory", 18, 811, 15, 'Varela', 10, alignment='R')

    upi_qr(Grand_Total, f"{Formated_InvoiceNo}-{Clients_Detiles[1]}")
    qr_code = generate_path("utilities", "assets", "qr.png")
    pdf.drawImage(qr_code, 276, 198, 81, 81)

    items = fetch_data(f'''SELECT item_name, item_code, quantity, unit, price, GST_Rate, Total FROM {Item_table} WHERE client_id = ? AND invoice_no = ?''', (Client_ID, Invoice_No))
    data = []
    sr_no = 1
    for row in items:
        item_name, item_code, quantity, unit, price, GST_Rate, Total = row
        data.append([
            sr_no,  
            item_name,  
            item_code, 
            f"{quantity} ({unit})",
            price,
            f"{GST_Rate} %",
            Total
        ])
        sr_no += 1

    header = ["Sr No", "Product Name", "HSN", "Quantity","Rate", "GST %", "Item Total"]
    table_data = [header] + data
    table = Table(table_data, colWidths=[38, 170, 60, 80, 80, 61, 81])
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), '#C5D9F1'),  # Header background color (#C5D9F1)
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),  # Header text color (black)
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),  # Center-align all cells
        ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, 0), 'P-SemiBold'),  # Header text vertical alignment (center)
        ('FONTNAME', (0, 1), (-1, -1), 'Varela'),  # Font for body (optional, if you want to change the body font too)
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TOPPADDING', (0, 0), (-1, 0), 5),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 5),  # Padding at the bottom of the header
        ('GRID', (0, 0), (-1, -1), 1, colors.black),  # Add gridlines
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),  # Body background color (white)
        ('LINEBELOW', (0, 0), (-1, 0), 1, colors.black),  # Add a top border for header (optional)
        ('ROWHEIGHT', (0, 0), (-1, -1), 25),  # Increase row height
    ])
    table.setStyle(style)
    frame = Frame(13, 289, 570, 330)
    frame.addFromList([table], pdf)
    pdf.drawRect(13, 228, 570, 330)

    pdf.save()


if __name__ == "__main__":
    create_invoice(1, 1, "hi.pdf")