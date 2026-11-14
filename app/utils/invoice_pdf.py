
from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
)


BRAND_NAME = "DYABROS"
BRAND_ADDRESS = (
    "5/50, 4th Floor, Harnam Singh Dispensary Wali Gali, "
    "Karol Bagh, New Delhi 110005"
)
BRAND_PHONE = "+91 9887114263"
BRAND_EMAIL = "business@dyabros.com"

ASSETS_DIR = Path(__file__).resolve().parents[1] / "assets"

LOGO_PATH = ASSETS_DIR / "dyabros-logo.png"
LATIN_FONT_PATH = ASSETS_DIR / "ArialUnicode.ttf"
RUPEE_FONT_PATH = ASSETS_DIR / "NotoSansDevanagari.ttf"

if "ArialUnicode" not in pdfmetrics.getRegisteredFontNames():
    pdfmetrics.registerFont(TTFont("ArialUnicode", str(LATIN_FONT_PATH)))

if "RupeeFont" not in pdfmetrics.getRegisteredFontNames():
    pdfmetrics.registerFont(TTFont("RupeeFont", str(RUPEE_FONT_PATH)))


def generate_invoice_pdf(invoice):
    buffer = BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title=f"Invoice {invoice.get('invoice_number', '')}",
    )

    styles = getSampleStyleSheet()

    # Use embedded Unicode font throughout the invoice
    for style_name in styles.byName:
        styles[style_name].fontName = "ArialUnicode"

    styles.add(ParagraphStyle(
        name="Brand",
        parent=styles["Title"],
        fontName="ArialUnicode",
        fontSize=22,
        textColor=colors.HexColor("#F0441B"),
        alignment=0,
        spaceAfter=4,
    ))

    styles.add(ParagraphStyle(
        name="SmallText",
        parent=styles["Normal"],
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#666666"),
    ))

    styles.add(ParagraphStyle(
        name="RightHeading",
        parent=styles["Heading1"],
        alignment=TA_RIGHT,
        fontSize=19,
    ))

    styles.add(ParagraphStyle(
        name="CellText",
        parent=styles["Normal"],
        fontSize=8,
        leading=11,
    ))

    styles.add(ParagraphStyle(
        name="CellRight",
        parent=styles["Normal"],
        fontSize=8,
        alignment=TA_RIGHT,
    ))

    def safe(value):
        return escape(str(value if value not in (None, "") else "—"))

    def money(value):
        amount = f"{float(value or 0):,.2f}"
        return Paragraph(
            f'<font name="RupeeFont">₹</font>{amount}',
            styles["CellRight"]
        )

    story = []

    # Header with actual DYABROS logo
    logo = Image(str(LOGO_PATH), width=48 * mm, height=20 * mm)
    logo.hAlign = "LEFT"

    header = Table(
        [[
            logo,
            Paragraph("TAX INVOICE", styles["RightHeading"]),
        ]],
        colWidths=[85 * mm, 89 * mm],
    )

    header.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LINEBELOW", (0, 0), (-1, -1), 1.2, colors.black),
    ]))

    story.append(header)
    story.append(Spacer(1, 7 * mm))

    # Seller and buyer details
    seller = (
        f"<b>SOLD BY</b><br/><br/>"
        f"<b>{BRAND_NAME}</b><br/>"
        f"{safe(BRAND_ADDRESS)}<br/>"
        f"Phone: {safe(BRAND_PHONE)}<br/>"
        f"Email: {safe(BRAND_EMAIL)}"
    )

    buyer = (
        f"<b>BILLED TO</b><br/><br/>"
        f"<b>{safe(invoice.get('business_name'))}</b><br/>"
        f"{safe(invoice.get('contact_name'))}<br/>"
        f"{safe(invoice.get('address'))}<br/>"
        f"Phone: {safe(invoice.get('phone'))}<br/>"
        f"Email: {safe(invoice.get('email'))}<br/>"
        f"GSTIN: {safe(invoice.get('gst_number'))}"
    )

    parties = Table(
        [[
            Paragraph(seller, styles["SmallText"]),
            Paragraph(buyer, styles["SmallText"]),
        ]],
        colWidths=[87 * mm, 87 * mm],
    )

    parties.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))

    story.append(parties)
    story.append(Spacer(1, 5 * mm))

    # Invoice metadata
    invoice_date = invoice.get("invoice_date")
    if hasattr(invoice_date, "strftime"):
        invoice_date = invoice_date.strftime("%d %B %Y")

    metadata = [
        ["Invoice Number", "Invoice Date", "Order Number", "Payment Status"],
        [
            safe(invoice.get("invoice_number")),
            safe(invoice_date),
            safe(invoice.get("order_number")),
            safe(invoice.get("payment_status")),
        ],
    ]

    meta_table = Table(
        metadata,
        colWidths=[43.5 * mm] * 4,
    )

    meta_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F2F4F6")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#777777")),
        ("FONTNAME", (0, 0), (-1, -1), "ArialUnicode"),
        ("FONTSIZE", (0, 0), (-1, 0), 7),
        ("FONTSIZE", (0, 1), (-1, 1), 8),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
    ]))

    story.append(meta_table)
    story.append(Spacer(1, 7 * mm))

    # Product rows
    item_data = [[
        "ITEM DESCRIPTION",
        "SKU",
        "QTY",
        "RATE",
        "TAXABLE",
    ]]

    for item in invoice.get("items", []):
        item_data.append([
            Paragraph(safe(item.get("name")), styles["CellText"]),
            Paragraph(safe(item.get("sku")), styles["CellText"]),
            str(item.get("quantity", 0)),
            money(item.get("price", 0)),
            money(item.get("line_total", 0)),
        ])

    items_table = Table(
        item_data,
        colWidths=[65 * mm, 43 * mm, 15 * mm, 25 * mm, 25 * mm],
        repeatRows=1,
    )

    items_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#151515")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "ArialUnicode"),
        ("FONTSIZE", (0, 0), (-1, 0), 7),
        ("FONTSIZE", (0, 1), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#DDE1E6")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (2, 1), (-1, -1), "RIGHT"),
        ("TOPPADDING", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
    ]))

    story.append(items_table)
    story.append(Spacer(1, 8 * mm))

    # Totals
    totals = [
        ["Taxable Amount", money(invoice.get("subtotal"))],
        [f"GST ({invoice.get('gst_rate', 18)}%)", money(invoice.get("gst"))],
        ["INVOICE TOTAL", money(invoice.get("total"))],
    ]

    totals_table = Table(
        totals,
        colWidths=[55 * mm, 35 * mm],
        hAlign="RIGHT",
    )

    totals_table.setStyle(TableStyle([
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("FONTNAME", (0, 0), (-1, -1), "ArialUnicode"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("LINEABOVE", (0, 2), (-1, 2), 1, colors.black),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))

    story.append(totals_table)
    story.append(Spacer(1, 12 * mm))

    story.append(Paragraph(
        f"<b>Payment Status:</b> {safe(invoice.get('payment_status'))}",
        styles["Normal"],
    ))

    story.append(Spacer(1, 4 * mm))

    story.append(Paragraph(
        "This invoice was generated electronically by DYABROS.",
        styles["SmallText"],
    ))

    document.build(story)

    buffer.seek(0)
    return buffer
