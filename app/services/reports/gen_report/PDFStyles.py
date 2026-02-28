import os
from pathlib import Path

from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER

# ==========================
# FONT REGISTRATION
# ==========================

def register_fonts(font_dir_name="static/Fonts/"):
    """
    Register Sarabun full font family.
    """
    current_file = Path(__file__).resolve()
    # สมมติว่าไฟล์นี้อยู่ที่ app/services/report.py 
    # เราต้องย้อนกลับไป 2 ชั้นเพื่อเจอโฟลเดอร์หลัก
    project_root = current_file.parent.parent.parent.parent
    
    font_path = project_root / font_dir_name 

    # --- Core 4 ---
    pdfmetrics.registerFont(TTFont("Sarabun-Regular", f"{font_path}/Sarabun-Regular.ttf"))
    pdfmetrics.registerFont(TTFont("Sarabun-Bold", f"{font_path}/Sarabun-Bold.ttf"))
    pdfmetrics.registerFont(TTFont("Sarabun-Italic", f"{font_path}/Sarabun-Italic.ttf"))
    pdfmetrics.registerFont(TTFont("Sarabun-BoldItalic", f"{font_path}/Sarabun-BoldItalic.ttf"))

    # --- Extra Weights ---
    pdfmetrics.registerFont(TTFont("Sarabun-Light", f"{font_path}/Sarabun-Light.ttf"))
    pdfmetrics.registerFont(TTFont("Sarabun-LightItalic", f"{font_path}/Sarabun-LightItalic.ttf"))
    pdfmetrics.registerFont(TTFont("Sarabun-Medium", f"{font_path}/Sarabun-Medium.ttf"))
    pdfmetrics.registerFont(TTFont("Sarabun-MediumItalic", f"{font_path}/Sarabun-MediumItalic.ttf"))
    pdfmetrics.registerFont(TTFont("Sarabun-SemiBold", f"{font_path}/Sarabun-SemiBold.ttf"))
    pdfmetrics.registerFont(TTFont("Sarabun-SemiBoldItalic", f"{font_path}/Sarabun-SemiBoldItalic.ttf"))
    pdfmetrics.registerFont(TTFont("Sarabun-ExtraBold", f"{font_path}/Sarabun-ExtraBold.ttf"))
    pdfmetrics.registerFont(TTFont("Sarabun-ExtraBoldItalic", f"{font_path}/Sarabun-ExtraBoldItalic.ttf"))
    pdfmetrics.registerFont(TTFont("Sarabun-ExtraLight", f"{font_path}/Sarabun-ExtraLight.ttf"))
    pdfmetrics.registerFont(TTFont("Sarabun-ExtraLightItalic", f"{font_path}/Sarabun-ExtraLightItalic.ttf"))
    pdfmetrics.registerFont(TTFont("Sarabun-Thin", f"{font_path}/Sarabun-Thin.ttf"))
    pdfmetrics.registerFont(TTFont("Sarabun-ThinItalic", f"{font_path}/Sarabun-ThinItalic.ttf"))


# ==========================
# STYLES
# ==========================

def get_styles():
    styles = {}

    # Base body
    styles["body"] = ParagraphStyle(
        name="Body",
        fontName="Sarabun-Light",
        fontSize=10,
        leading=20,
        textColor=colors.black
    )

    # Cover page body (slightly bigger)
    styles["body_cover"] = ParagraphStyle(
        name="BodyCover",
        fontName="Sarabun-Regular",
        fontSize=14,
        leading=22,
        textColor=colors.black
    )

    # Small text
    styles["body_small"] = ParagraphStyle(
        name="BodySmall",
        fontName="Sarabun-Light",
        fontSize=8,
        leading=16,
        textColor=colors.black
    )

    # Title
    styles["title"] = ParagraphStyle(
        name="Title",
        fontName="Sarabun-SemiBold",
        fontSize=18,
        leading=28,
        textColor=colors.black
    )

    # Section header
    styles["section"] = ParagraphStyle(
        name="Section",
        fontName="Sarabun-SemiBold",
        fontSize=12,
        leading=24,
        textColor=colors.black
    )

    # Strong bold style
    styles["bold"] = ParagraphStyle(
        name="Bold",
        fontName="Sarabun-Bold",
        fontSize=10,
        leading=20,
        textColor=colors.black
    )

    styles["center"] = ParagraphStyle(
        name="Center",
        parent=styles["body"],
        alignment=TA_CENTER
    )

    return styles