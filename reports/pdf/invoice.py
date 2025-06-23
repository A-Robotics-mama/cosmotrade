# reports/pdf/invoice.py

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from io import BytesIO
from decimal import Decimal
from django.http import HttpResponse
from reports.pdf_utils import (
    get_pdf_styles, get_logo_element,
    get_supplier_buyer_table, get_signature_table,
    get_payment_instructions_table, calculate_totals
)
from sales.models import SalesInvoice
import logging

logger = logging.getLogger(__name__)

# Регистрация шрифтов
pdfmetrics.registerFont(TTFont('Muli-Light', '/app/static/fonts/Muli-Light.ttf'))
pdfmetrics.registerFont(TTFont('Muli-Regular', '/app/static/fonts/Muli.ttf'))
pdfmetrics.registerFont(TTFont('Muli-Bold', '/app/static/fonts/Muli-Bold.ttf'))
pdfmetrics.registerFont(TTFont('Roboto-Regular', '/app/static/fonts/Roboto-Regular.ttf'))
pdfmetrics.registerFont(TTFont('Roboto-Bold', '/app/static/fonts/Roboto-Bold.ttf'))
pdfmetrics.registerFont(TTFont('Roboto-Light', '/app/static/fonts/Roboto-Light.ttf'))

def generate_invoice_pdf(request, invoice_number, as_bytes=False):
    sales = SalesInvoice.objects.filter(invoice=invoice_number)
    if not sales.exists():
        logger.error(f"No sales found for invoice: {invoice_number}")
        if as_bytes:
            raise ValueError("Invoice not found")
        return HttpResponse("Invoice not found", status=404)

    first_sale = sales.first()
    customer = first_sale.customer
    total_with_vat, total_vat = calculate_totals(sales)

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=20, bottomMargin=18)
    elements = []

    styles = get_pdf_styles()

    header_data = [[
        "",
        get_logo_element(),
        Paragraph(
            f"INVOICE #{invoice_number}<br/>Date: {first_sale.timestamp.strftime('%d/%m/%Y')}",
            ParagraphStyle(
                name='HeaderTitle',
                fontName='Muli-Bold',
                fontSize=14,
                leading=16,
                alignment=2,
                textColor=colors.black,
            )
        ),
        ""
    ]]
    header_table = Table(header_data, colWidths=[40, 228, 297, 30])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (0, 0), 'TOP'),
        ('VALIGN', (1, 0), (1, 0), 'BOTTOM'),
        ('LEFTPADDING', (0, 0), (0, 0), 10),
        ('RIGHTPADDING', (1, 0), (1, 0), 10),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 24))

    combined_table = get_supplier_buyer_table(customer)
    elements.append(combined_table)
    elements.append(Spacer(1, 24))

    data = [['Supplier Code', 'Item Description', 'Quantity', 'Unit Price', 'Total']]
    subtotal = 0
    for sale in sales:
        unit_price_without_vat = sale.sell_price / (1 + (sale.vat_rate / 100))
        total_without_vat = unit_price_without_vat * sale.qty
        subtotal += total_without_vat
        data.append([
            sale.product.manufacturer_code,
            sale.product.product_name,
            str(sale.qty),
            f"\u20ac{unit_price_without_vat:.2f}",
            f"\u20ac{total_without_vat:.2f}"
        ])

    data.append(['', '', '', 'Subtotal', f"\u20ac{subtotal:.2f}"])
    data.append(['', '', '', 'VAT', f"\u20ac{total_vat:.2f}"])
    data.append(['', '', '', 'Total', f"\u20ac{subtotal + total_vat:.2f}"])

    table = Table(data, colWidths=[100, 200, 50, 75, 75])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Muli-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 1), (-1, -1), 'Muli-Regular'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 24))

    payment_table, payment_style = get_payment_instructions_table()
    payment_table.setStyle(payment_style)
    elements.append(payment_table)
    elements.append(Spacer(1, 24))

    signature_table, signature_style = get_signature_table()
    signature_table.setStyle(signature_style)
    elements.append(signature_table)

    doc.build(elements)
    pdf = buffer.getvalue()
    buffer.close()

    if as_bytes:
        return pdf
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice_{invoice_number}.pdf"'
    return response
