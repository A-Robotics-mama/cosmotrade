# reports/pdf_utils.py

from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.platypus import Image, Table, TableStyle, Paragraph, Spacer
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER
from django.conf import settings
import os
import logging


from reportlab.lib.styles import ParagraphStyle


from reportlab.lib.units import mm



logger = logging.getLogger(__name__)

def get_pdf_styles():
    return {
        'custom_title': ParagraphStyle(
            name='CustomTitle',
            fontName='Muli-Light',
            fontSize=12,
            leading=14,
            alignment=TA_LEFT,
            textColor=colors.black,
        ),
        'header_title': ParagraphStyle(
            name='HeaderTitle',
            fontName='Muli-Bold',
            fontSize=14,
            leading=16,
            alignment=TA_RIGHT,
            textColor=colors.black,
        ),
        'normal_style': ParagraphStyle(  # ✅ чтобы избежать любой ошибки
            name='NormalStyle',
            fontName='Muli',
            fontSize=10,
            leading=12,
            textColor=colors.black,
            alignment=TA_LEFT,
        ),
        'normal': ParagraphStyle(
            name='Normal',
            fontName='Muli',
            fontSize=10,
            leading=12,
            textColor=colors.black,
            alignment=TA_LEFT,
        ),
        'bold': ParagraphStyle(
            name='Bold',
            fontName='Muli-Bold',
            fontSize=10,
            leading=12,
            textColor=colors.black,
        ),
        'right': ParagraphStyle(
            name='Right',
            fontName='Muli',
            fontSize=10,
            leading=12,
            alignment=TA_RIGHT,
            textColor=colors.black,
        ),
        'center': ParagraphStyle(
            name='Center',
            fontName='Muli',
            fontSize=10,
            leading=12,
            alignment=TA_CENTER,
            textColor=colors.black,
        ),
    }

def get_logo_element():
    # Изменено: добавлено использование mm для задания размеров в миллиметрах для большей ясности
    # Было: width=215, height=55 (в пунктах)
    logo_path = os.path.join(settings.STATICFILES_DIRS[0], 'img', 'logo.png')
    styles = get_pdf_styles()
    if os.path.exists(logo_path):
        try:
            # Стало: размеры в мм (215 pt ≈ 76 мм, 55 pt ≈ 19 мм), сохранены пропорции
            return Image(logo_path, width=76*mm, height=19*mm)
        except Exception as e:
            # Изменено: добавлено логирование ошибок при загрузке изображения
            # Было: нет обработки ошибок Image
            logger.error(f"Failed to load logo at {logo_path}: {e}")
    # Изменено: логирование предупреждения теперь более информативное
    # Было: logger.warning(f"Logo not found at {logo_path}, falling back to text")
    logger.warning(f"Logo not found or failed to load at {logo_path}, using text fallback")
    return Paragraph("MS COSMOTRADE LIMITED", styles['custom_title'])



def get_header_table(document_type, document_number):
    styles = get_pdf_styles()
    header_data = [
        [
            get_logo_element(),

        ]
    ]
    header_table = Table(header_data, colWidths=[40,228, 297, 30])  
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (0, 0), 10),
        ('RIGHTPADDING', (1, 0), (1, 0), 10),
    ]))
    return header_table

def get_supplier_buyer_table(customer):
    styles = get_pdf_styles()
    
    # Заменено 'normal_style' → 'normal'
    supplier_info = [
        Paragraph("Supplier:", styles['normal']),
        Paragraph("MS Cosmotrade Limited", styles['normal']),
        Paragraph("8 Aiolou, app 302, Germasogeia, 4041, Cyprus", styles['normal']),
        Paragraph("VAT: CY10410284K", styles['normal']),
        Paragraph("Phone: +357 99779776", styles['normal']),
    ]
    buyer_info = [
        Paragraph("Bill To:", styles['normal']),
        Paragraph(customer.legal_name, styles['normal']),
        Paragraph(customer.street_address if customer.street_address else "", styles['normal']),
        Paragraph(
            f"{customer.postcode}, {customer.country_iso.country_name if customer.country_iso else 'N/A'}"
            if customer.postcode else
            (customer.country_iso.country_name if customer.country_iso else "N/A"),
            styles['normal']
        ),
        Paragraph(f"VAT: {customer.vat or 'N/A'}", styles['normal']),
        Paragraph(f"Phone: {customer.mobile or customer.landline or 'N/A'}", styles['normal']),
    ]

    combined_data = []
    max_rows = max(len(supplier_info), len(buyer_info))
    for i in range(max_rows):
        row = [
            supplier_info[i] if i < len(supplier_info) else "",
            "",  # Разделительное поле
            buyer_info[i] if i < len(buyer_info) else ""
        ]
        combined_data.append(row)

    table = Table(combined_data, colWidths=[187, 107, 187])
    table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Muli'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('ALIGN', (2, 0), (2, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0, colors.transparent),
        ('LEFTPADDING', (0, 0), (0, -1), 0),
        ('LEFTPADDING', (2, 0), (2, -1), 0),
    ]))
    return table


def get_signature_table():
    signature_info = [
        ["Created by MS Cosmotrade CMS"],
        
        ["Phone: +35799779776"],
    ]
    return Table(signature_info, colWidths=[300]), TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Muli'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
    ])

def get_payment_instructions_table():
    payment_info = [
        ["Payment Instructions:"],
        ["Beneficiary: MS Cosmotrade Limited"],
        ["Beneficiary Address: 8 Aiolou, app 302, Germasogeia, 4041, Cyprus"],
        ["Bank: ASTROBANK PUBLIC COMPANY"],
        ["IBAN: CY45008002020000000002828185"],
        ["BIC/SWIFT: PIRBCY2NXXX"],
    ]
    return Table(payment_info, colWidths=[300]), TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Muli'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
    ])

def calculate_totals(sales):
    total_with_vat = sum(sale.total_with_vat or 0 for sale in sales)
    total_vat = sum(sale.sale_vat or 0 for sale in sales)
    return total_with_vat, total_vat


def register_fonts():
    pdfmetrics.registerFont(TTFont('Muli', '/app/static/fonts/Muli.ttf'))
    pdfmetrics.registerFont(TTFont('Muli-Bold', '/app/static/fonts/Muli-Bold.ttf'))
    pdfmetrics.registerFont(TTFont('Muli-Light', '/app/static/fonts/Muli-Light.ttf'))
    pdfmetrics.registerFont(TTFont('Roboto-Regular', '/app/static/fonts/Roboto-Regular.ttf'))
    pdfmetrics.registerFont(TTFont('Roboto-Bold', '/app/static/fonts/Roboto-Bold.ttf'))
    pdfmetrics.registerFont(TTFont('Roboto-Light', '/app/static/fonts/Roboto-Light.ttf'))


def get_common_styles():
    return {
        'custom_title': ParagraphStyle(
            name='CustomTitle',
            fontName='Muli-Light',
            fontSize=12,
            leading=14,
            alignment=0,
            textColor=colors.black,
        ),
        'header_title': ParagraphStyle(
            name='HeaderTitle',
            fontName='Muli-Bold',
            fontSize=14,
            leading=16,
            alignment=TA_RIGHT,
            textColor=colors.black,
        ),
        'normal': ParagraphStyle(
            name='Normal',
            fontName='Muli',
            fontSize=10,
            leading=12,
            textColor=colors.black,
        ),
        'bold': ParagraphStyle(
            name='Bold',
            fontName='Muli-Bold',
            fontSize=10,
            leading=12,
            textColor=colors.black,
        ),
        'right': ParagraphStyle(
            name='Right',
            fontName='Muli',
            fontSize=10,
            leading=12,
            alignment=TA_RIGHT,
            textColor=colors.black,
        ),
        'center': ParagraphStyle(
            name='Center',
            fontName='Muli',
            fontSize=10,
            leading=12,
            alignment=TA_CENTER,
            textColor=colors.black,
        ),
    }
