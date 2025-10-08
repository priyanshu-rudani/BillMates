import sys
from pathlib import Path

if getattr(sys, 'frozen', False):  # Running as a PyInstaller EXE
    root_path = Path(sys.executable).parent
else:  # Running as a Python script
    root_path = Path(__file__).parent.parent
sys.path.append(str(root_path))
 
from utilities.path_utils import generate_path, database_path, read_ini, write_ini
import tkinter as tk
from tkinter import messagebox
from reportlab.pdfgen import canvas
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from datetime import datetime
from num2words import num2words
import locale


def export_Cheque(Path, Payee_name, figureAmount, Date_Formate, Cheque_Date, Cheque_Type, isBearer):

    Payee_name = str(Payee_name) or ""
    figureAmount = float(figureAmount) or 0.00
    Date_Formate = str(Date_Formate) or "D D M M Y Y Y Y"
    Cheque_Date = str(Cheque_Date) or ""
    Cheque_Type = str(Cheque_Type) or "None"
    isBearer = bool(isBearer) or False

    def number_to_words(amount):
        rupees = int(amount)  # Extract whole number

        rupees_words = num2words(rupees, lang='en_IN').title()

        formatted_text = f"** {rupees_words} Rupees Only **"

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

        max_len1, max_len2 = 60, 50

        # Try splitting with full text
        line1, line2 = wrap_text(formatted_text, max_len1, max_len2)
        if line1 and line2:
            return line1, line2

        if line1 is None or line2 is None:
            formatted_text = formatted_text.replace("Rupees", "Rs.").strip()  # Remove 'Rupees'
            line1, line2 = wrap_text(formatted_text, max_len1, max_len2)

        if line1 is None or line2 is None:  
            formatted_text = formatted_text.strip('*')  # Remove formatting symbols
            line1, line2 = wrap_text(formatted_text, max_len1, max_len2)

        if line1 is None or line2 is None:
            line1, line2 = wrap_text(formatted_text, 65, max_len2)  # Increase first line limit

        if line1 is None or line2 is None:
            line1, line2 = wrap_text(formatted_text, 70, max_len2)  # Last resort: Increase limit to 70

        return line1, line2

    line1, line2 = number_to_words(figureAmount)

    locale.setlocale(locale.LC_ALL, 'en_IN')  # Set locale to Indian format
    amount = locale.format_string("%0.2f", figureAmount, grouping=True)

    amount = f"*{amount}*"

    c = canvas.Canvas(Path, pagesize=[595.2, 841.92])

    pdfmetrics.registerFont(TTFont('Varela', generate_path("utilities", "assets", "Font","VarelaRound-Regular.ttf")))

    positions = [
        (364, 805, f"** {Payee_name} **"), 
        (341, 775, line1),      # 60 Word Count
        (316, 810, line2),      # 50 Word Count
        (316, 410, amount)     # 20 Word Count
    ]

    for x, y, text in positions:
        c.setFont('Varela', 12)
        c.saveState()
        c.translate(x, y)
        c.rotate(-90)
        c.drawString(0, 0, str(text))
        c.restoreState()


    if Date_Formate == "D D M M Y Y Y Y":
        date = [
            (402, 430.75, Cheque_Date[0]), # D
            (402, 412.00, Cheque_Date[1]), # D
            (402, 393.25, Cheque_Date[3]), # M
            (402, 374.50, Cheque_Date[4]), # M
            (402, 355.75, Cheque_Date[6]), # Y
            (402, 337.00, Cheque_Date[7]), # Y
            (402, 318.75, Cheque_Date[8]), # Y
            (402, 300.00, Cheque_Date[9])  # Y
        ]
        for x, y, text in date:
            c.setFont('Varela', 12)
            c.saveState()
            c.translate(x, y)
            c.rotate(-90)
            c.drawString(0, 0, str(text))
            c.restoreState()
    elif Date_Formate == "DD-MM-YYYY":
        Date = datetime.strptime(Cheque_Date, "%d/%m/%Y").strftime("%d-%m-%Y")
        c.setFont('Varela', 12)
        c.saveState()
        c.translate(402, 397.625)
        c.rotate(-90)
        c.drawString(0, 0, str(Date))
        c.restoreState()
    elif Date_Formate == "DD/MM/YYYY":
        c.setFont('Varela', 12)
        c.saveState()
        c.translate(402, 397.625)
        c.rotate(-90)
        c.drawString(0, 0, str(Cheque_Date))
        c.restoreState()


    if isBearer == True:
        c.setFont('Varela', 12)
        c.saveState()
        c.translate(361, 360)
        c.rotate(-90)
        c.drawString(0, 0, "XXXXXXX")
        c.restoreState()


    if Cheque_Type == "Account":
        image_path = generate_path("utilities", "assets", "AC Pay.png")
        x, y = 361.68 , 778.56
        width, height = 78.72, 68.4

        c.saveState()
        c.translate(0 , 0)
        c.rotate(0)
        c.drawImage(image_path, x, y, width, height, mask='auto')
        c.restoreState()
    elif Cheque_Type == "Cross":
        image_path = generate_path("utilities", "assets", "cross.png")
        x, y = 361.68 , 778.56
        width, height = 78.72, 68.4

        c.saveState()
        c.translate(0 , 0)
        c.rotate(0)
        c.drawImage(image_path, x, y, width, height, mask='auto')
        c.restoreState()


    c.save()


if __name__ == "__main__":
    export_Cheque(
        Path = "cheque.pdf",
        Payee_name = "Krishna Fashion",
        figureAmount = "5000",
        Date_Formate = "DD-MM-YYYY", 
        Cheque_Date = "07/11/2007",
        Cheque_Type = "Account",
        isBearer = "False"
    )