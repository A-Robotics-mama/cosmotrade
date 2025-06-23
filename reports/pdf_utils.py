from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.platypus import Image, Table, TableStyle, Paragraph, Spacer
from django.conf import settings
import os
import logging

logger = logging.getLogger(__name__)

def get_pdf_styles():
    styles = getSampleStyleSheet()
    return {
        'custom_title': ParagraphStyle(
            name='CustomTitle',
            parent=styles['Title'],
            fontName='Muli-Light',
            fontSize=12,
            leading=14,
            alignment=0,
            textColor=colors.black,
        ),
        'title_style': ParagraphStyle(
            name='TitleStyle',
            fontName='Muli-Bold',
            fontSize=16,
            leading=18,
            alignment=1,
            textColor=colors.black,
        ),
        'normal_style': ParagraphStyle(
            name='NormalStyle',
            fontName='Muli-Regular',
            fontSize=10,
            leading=12,
            textColor=colors.black,
        ),
        'header_style': ParagraphStyle(
            name='HeaderStyle',
            fontName='Muli-Bold',
            fontSize=12,
            leading=14,
            textColor=colors.whitesmoke,
        ),
    }

def get_logo_element():
    logo_path = os.path.join(settings.STATICFILES_DIRS[0], 'img', 'logo.png')
    styles = get_pdf_styles()
    if os.path.exists(logo_path):
        return Image(logo_path, width=215, height=55)
    logger.warning(f"Logo not found at {logo_path}, falling back to text")
    return Paragraph("MS COSMOTRADE LIMITED", styles['custom_title'])

def get_header_table(document_type, document_number):
    styles = get_pdf_styles()
    header_data = [
        [
            get_logo_element(),
            Paragraph(
                f"MS COSMOTRADE<br/>EVERYTHING FOR YOUR BEAUTY BUSINESS<br/><br/>{document_type} #{document_number}",
                ParagraphStyle(
                    name='HeaderTitle',
                    fontName='Muli-Bold',
                    fontSize=14,
                    leading=16,
                    alignment=2,  # Выравнивание по правому краю
                    textColor=colors.black,
                )
            )
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
    supplier_info = [
        Paragraph("Supplier:", styles['normal_style']),
        Paragraph("MS Cosmotrade Limited", styles['normal_style']),
        Paragraph("Amathountos 98, Rita Court, Block C, office 6", styles['normal_style']),
        Paragraph("Agios Tychonas, 4532, Cyprus", styles['normal_style']),
        Paragraph("VAT: CY10410284K", styles['normal_style']),
        Paragraph("Phone: +357 99779776", styles['normal_style']),
    ]
    buyer_info = [
        Paragraph("Bill To:", styles['normal_style']),
        Paragraph(customer.legal_name , styles['normal_style']),
        Paragraph(customer.street_address if customer.street_address else "", styles['normal_style']),
        Paragraph(f"{customer.postcode}, {customer.country_iso.country_name if customer.country_iso else 'N/A'}" if customer.postcode else (customer.country_iso.country_name if customer.country_iso else "N/A"), styles['normal_style']),
        Paragraph(f"VAT: {customer.vat or 'N/A'}", styles['normal_style']),
        Paragraph(f"Phone: {customer.mobile or customer.landline or 'N/A'}", styles['normal_style']),
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
    table = Table(combined_data, colWidths=[187, 107, 187])  # 35%, 20%, 35% от 535.5 pt
    table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Muli-Regular'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),  # Выравнивание по левому краю для продавца
        ('ALIGN', (2, 0), (2, -1), 'LEFT'),  # Выравнивание по левому краю для покупателя
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0, colors.transparent),  # Без границ
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
        ('FONTNAME', (0, 0), (-1, -1), 'Muli-Regular'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
    ])

def get_payment_instructions_table():
    payment_info = [
        ["Payment Instructions:"],
        ["Bank: Bank of Cyprus"],
        ["Account: 1234-5678-9012-3456"],
        ["IBAN: CY1234567890123456789012"],
        ["SWIFT: BCYPCY2N"],
    ]
    return Table(payment_info, colWidths=[300]), TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Muli-Regular'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
    ])

def calculate_totals(sales):
    total_with_vat = sum(sale.total_with_vat or 0 for sale in sales)
    total_vat = sum(sale.sale_vat or 0 for sale in sales)
    return total_with_vat, total_vat