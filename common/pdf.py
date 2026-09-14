"""
Shared reportlab helpers. One place to build a simple letterhead-style
PDF, reused by fee receipts today and staff documents (payslips, library
overdue notices, gate passes) as those are added - so every PDF in the
system looks consistent without each app reinventing layout code.
"""
from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.pdfgen import canvas


def render_simple_document(title, subtitle, lines, footer=None):
    """
    Builds a single-page A4 PDF: a school letterhead, a title/subtitle,
    then a list of (label, value) lines. Returns raw PDF bytes.
    """
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    c.setFillColor(colors.HexColor('#1a5632'))
    c.rect(0, height - 25 * mm, width, 25 * mm, fill=True, stroke=False)
    c.setFillColor(colors.white)
    c.setFont('Helvetica-Bold', 16)
    c.drawString(20 * mm, height - 16 * mm, 'Mzuzu Secondary School')
    c.setFont('Helvetica', 9)
    c.drawString(20 * mm, height - 21 * mm, 'Mzuzu, Malawi')

    y = height - 40 * mm
    c.setFillColor(colors.black)
    c.setFont('Helvetica-Bold', 14)
    c.drawString(20 * mm, y, title)
    y -= 7 * mm
    if subtitle:
        c.setFont('Helvetica', 10)
        c.setFillColor(colors.grey)
        c.drawString(20 * mm, y, subtitle)
        y -= 10 * mm
    c.setFillColor(colors.black)

    c.setFont('Helvetica', 11)
    for label, value in lines:
        c.setFont('Helvetica-Bold', 11)
        c.drawString(20 * mm, y, f'{label}:')
        c.setFont('Helvetica', 11)
        c.drawString(70 * mm, y, str(value))
        y -= 8 * mm

    if footer:
        c.setFont('Helvetica-Oblique', 8)
        c.setFillColor(colors.grey)
        c.drawString(20 * mm, 15 * mm, footer)

    c.showPage()
    c.save()
    return buffer.getvalue()
