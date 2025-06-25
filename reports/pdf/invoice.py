# reports/pdf/invoice.py

import logging
import os
from decimal import Decimal
from io import BytesIO

from django.http import HttpResponse
from django.db.models import Sum
from django.conf import settings

from reportlab.platypus import (
    SimpleDocTemplate, Spacer, Table, TableStyle,
    Paragraph, Image
)
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_RIGHT

from customers.models import Customers
from sales.models import SalesInvoice, ItemsSold
from reports.pdf_utils import (
    get_pdf_styles,
    get_supplier_buyer_table,
    get_signature_table,
    get_payment_instructions_table,
)
from reports.pdf_utils import register_fonts
register_fonts()

from reports.pdf_utils import get_common_styles
styles = get_common_styles()

logger = logging.getLogger(__name__)

# Шрифты
pdfmetrics.registerFont(TTFont('Muli-Bold', '/app/static/fonts/Muli-Bold.ttf'))

def generate_invoice_pdf(request, invoice_number, as_bytes=False):
    try:
        sale = SalesInvoice.objects.get(invoice=invoice_number)
        items = ItemsSold.objects.filter(sales_invoice=sale)
        customer = sale.customer

        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=20,
            bottomMargin=18
        )
        elements = []
        styles = get_pdf_styles()

        # 🔹 Загрузка логотипа (в точности как в котировке)
        logo_path = os.path.join(settings.STATICFILES_DIRS[0], 'img', 'logo.png')
        if os.path.exists(logo_path):
            try:
                logo = Image(logo_path, width=60.8 * mm, height=15.2 * mm)
            except Exception as e:
                logger.error(f"Failed to load logo: {e}")
                logo = Paragraph("MS COSMOTRADE LIMITED", styles['custom_title'])
        else:
            logger.warning(f"Logo not found at {logo_path}, fallback to text")
            logo = Paragraph("MS COSMOTRADE LIMITED", styles['custom_title'])

        # 🔹 Заголовок справа
        header_paragraph = Paragraph(
            f"INVOICE #{invoice_number}<br/>Date: {sale.sell_date.strftime('%d/%m/%Y')}",
            ParagraphStyle(
                name='HeaderTitle',
                fontName='Muli-Bold',
                fontSize=14,
                leading=16,
                alignment=TA_RIGHT,
                textColor=colors.black,
            )
        )

        # 🔹 Таблица шапки
        header_table = Table(
            [[logo, header_paragraph]],
            colWidths=[None, None],
            hAlign='LEFT'
        )
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (0, 0), 0),
            ('RIGHTPADDING', (0, 0), (0, 0), 40),  # логотип к левому краю
            ('LEFTPADDING', (1, 0), (1, 0), 40),  # инвойс к правому краю
            ('RIGHTPADDING', (1, 0), (1, 0), 0),
        ]))


        # 🔹 Вставка шапки и отступов
        elements.append(Spacer(1, 30))
        elements.append(header_table)
        elements.append(Spacer(1, 50))

        # 🔹 Таблица поставщик / покупатель
        combined_table = get_supplier_buyer_table(customer)
        elements.append(combined_table)
        elements.append(Spacer(1, 24))

        # 🔹 Таблица позиций
        data = [['Code', 'Item Description', 'QTY', 'Unit Price', 'VAT', 'Total']]
        for item in items:
            data.append([
                item.product.manufacturer_code if item.product else 'N/A',
                item.product.product_name if item.product else 'Unknown',
                str(item.qty),
                f"€{item.sell_price:.2f}",
                f"€{item.sale_vat:.2f}",
                f"€{item.total_with_vat:.2f}"
            ])
        table = Table(data, colWidths=[70, 160, 50, 65, 65, 65])  # Общая ширина ≈ 475 pt
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Muli-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 1), (-1, -1), 'Muli-Bold'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ]))

        elements.append(table)
        elements.append(Spacer(1, 24))

        # 🔹 Сводные суммы
        total_price = sale.total_price or Decimal('0.00')
        sale_vat = sale.sale_vat or Decimal('0.00')
        total_with_vat = sale.total_with_vat or (total_price + sale_vat)

        elements.append(Paragraph(f"<b>Subtotal:</b> €{total_price:.2f}", styles['right']))
        elements.append(Paragraph(f"<b>VAT:</b> €{sale_vat:.2f}", styles['right']))
        elements.append(Paragraph(f"<b>Total:</b> €{total_with_vat:.2f}", styles['right']))
        elements.append(Spacer(1, 24))

        # 🔹 Платежные инструкции
        payment_table, payment_style = get_payment_instructions_table()
        payment_table.setStyle(payment_style)
        elements.append(payment_table)
        elements.append(Spacer(1, 24))

        # 🔹 Подписи
        signature_table, signature_style = get_signature_table()
        signature_table.setStyle(signature_style)
        elements.append(signature_table)

        # 🔹 Генерация PDF
        doc.build(elements)
        pdf = buffer.getvalue()
        buffer.close()

        if as_bytes:
            return pdf

        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="invoice_{invoice_number}.pdf"'
        response.write(pdf)
        return response

    except SalesInvoice.DoesNotExist:
        logger.error(f"Invoice {invoice_number} not found")
        if as_bytes:
            raise ValueError("Invoice not found")
        return HttpResponse("Invoice not found", status=404)
    except Exception as e:
        logger.error(f"Error generating invoice PDF: {str(e)}")
        if as_bytes:
            raise ValueError(f"Error generating PDF: {str(e)}")
        return HttpResponse(f"Error generating PDF: {str(e)}", status=500)
