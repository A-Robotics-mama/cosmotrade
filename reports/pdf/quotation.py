# reports/pdf/quotation.py

import logging
from decimal import Decimal
from io import BytesIO
from django.http import HttpResponse
from django.db.models import Sum
from reportlab.platypus import SimpleDocTemplate, Spacer, Table, TableStyle, Paragraph
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from customers.models import Customers
from sales.models import ItemsQuotation
from reports.pdf_utils import (
    get_pdf_styles,
    get_logo_element,
    get_supplier_buyer_table,
    get_signature_table,
    get_payment_instructions_table,
    calculate_totals
)

logger = logging.getLogger(__name__)

pdfmetrics.registerFont(TTFont('Muli-Bold', '/app/static/fonts/Muli-Bold.ttf'))

def generate_quotation_pdf(request, quotation, items, as_bytes=False):
    if not quotation or not items:
        logger.error(f"Invalid input: quotation={quotation}, items={items}")
        if as_bytes:
            raise ValueError("Quotation or items not found")
        return HttpResponse("Quotation or items not found", status=404)

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=20, bottomMargin=18)
    elements = []

    styles = get_pdf_styles()
    quotation_base = quotation.quotation_number[10:]  # Извлекаем номер без префикса
    elements.append(Paragraph(
        f"QUOTATION #{quotation_base}<br/>Date: {quotation.created_at.strftime('%d/%m/%Y')}",
        ParagraphStyle(
            name='HeaderTitle',
            fontName='Muli-Bold',
            fontSize=14,
            leading=16,
            alignment=2,
            textColor=colors.black,
        )
    ))
    elements.append(Spacer(1, 24))

    customer = quotation.customer
    combined_table = get_supplier_buyer_table(customer)
    elements.append(combined_table)
    elements.append(Spacer(1, 24))

    data = [['Supplier Code', 'Item Description', 'Quantity', 'Unit Price', 'Total']]
    subtotal = Decimal('0.00')
    for item in items:
        unit_price = item.sell_price / (1 + (item.vat_rate / 100))
        total_line = unit_price * item.qty
        subtotal += total_line
        data.append([
            item.product.manufacturer_code if item.product else 'N/A',
            item.product.product_name if item.product else 'Unknown',
            str(item.qty),
            f"€{unit_price:.2f}",
            f"€{total_line:.2f}"
        ])
    total_vat = items.aggregate(total=Sum('sale_vat'))['total'] or Decimal('0.00')
    data.append(['', '', '', 'Subtotal', f"€{subtotal:.2f}"])
    data.append(['', '', '', 'VAT', f"€{total_vat:.2f}"])
    data.append(['', '', '', 'Total', f"€{subtotal + total_vat:.2f}"])

    table = Table(data, colWidths=[100, 200, 50, 75, 75])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Muli-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 1), (-1, -1), 'Muli-Bold'),
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
    response['Content-Disposition'] = f'attachment; filename="quotation_{quotation_base}.pdf"'
    return response
