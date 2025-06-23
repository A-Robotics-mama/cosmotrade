# reports/services.py

from decimal import Decimal
from django.utils import timezone
from django.core.mail import EmailMessage
from django.conf import settings
from django.http import HttpResponse, FileResponse
from django.db.models import Sum

from imports.models import Imports


from sales.models import Quotation, ItemsQuotation, SalesInvoice
from customers.models import CustomerBalance, CustomerPayments
from stock.models import Stock
from .pdf.quotation import generate_quotation_pdf
from .pdf.invoice import generate_invoice_pdf
from reports.email_utils import send_quotation_email, send_invoice_email
import os
import logging
import traceback

logger = logging.getLogger(__name__)

def delete_quotation(quotation_number):
    try:
        # Получаем объект котировки
        quotation = Quotation.objects.get(quotation_number=quotation_number)
        quotation_id = quotation.id  # Числовой ID

        # Удаляем строки ItemsQuotation, связанные по quotation_number
        ItemsQuotation.objects.filter(quotation_number=quotation_number).delete()

        # Удаляем строки SalesInvoice, связанные по quotation_id
        SalesInvoice.objects.filter(quotation_id=quotation_id).delete()

        # Удаляем записи баланса и платежей, где используется строковый quotation_number
        CustomerBalance.objects.filter(
            transaction_type='QUOTATION',
            transaction_id=f"QUOTATION-{quotation_number}"
        ).delete()

        CustomerPayments.objects.filter(
            transaction_type='QUOTATION',
            transaction_id=f"QUOTATION-{quotation_number}"
        ).delete()

        # Удаляем саму котировку
        quotation.delete()

        return True, "Quotation and related records successfully deleted."

    except Quotation.DoesNotExist:
        logger.error(f"Quotation {quotation_number} not found")
        return False, f"Quotation {quotation_number} not found."
    except Exception as e:
        logger.error(f"🔥 Error deleting quotation {quotation_number}: {str(e)}\n{traceback.format_exc()}")
        return False, str(e)



def get_quotation_list(customer_id=None):
    # Фильтрация по клиенту, если задан
    quotations = Quotation.objects.all()
    if customer_id:
        quotations = quotations.filter(customer_id=customer_id)

    quotations = quotations.order_by('-created_at')
    result = []
    for q in quotations:
        items = ItemsQuotation.objects.filter(quotation=q)
        if items.exists():
            total_with_vat = items.aggregate(total=Sum('total_with_vat'))['total'] or Decimal('0.00')
            result.append({
                'quotation_number': q.quotation_number,
                'customer': q.customer,
                'created_at': q.created_at,
                'total_amount': q.total_amount or total_with_vat,
                'status': q.status
            })
    return result


def serve_invoice_file(invoice_number):
    invoice_path = os.path.join(settings.BASE_DIR, 'apps', 'invoices_out', f"invoice_{invoice_number}.pdf")
    logger.info(f"Attempting to serve invoice PDF: {invoice_path}")

    if not os.path.exists(invoice_path):
        logger.error(f"Invoice file not found at {invoice_path}")
        invoice_dir = os.path.join(settings.BASE_DIR, 'apps', 'invoices_out')
        if os.path.exists(invoice_dir):
            files = os.listdir(invoice_dir)
            logger.info(f"Files in invoices_out directory: {files}")
        else:
            logger.error(f"invoices_out directory does not exist: {invoice_dir}")
        return HttpResponse("Invoice not found", status=404)

    try:
        file_size = os.path.getsize(invoice_path)
        logger.info(f"File size: {file_size} bytes")

        response = FileResponse(
            open(invoice_path, 'rb'),
            content_type='application/pdf',
            as_attachment=True,
            filename=f"invoice_{invoice_number}.pdf"
        )

        response['Content-Length'] = file_size
        response['Content-Disposition'] = f'attachment; filename="invoice_{invoice_number}.pdf"'

        logger.info(f"Successfully serving invoice PDF: {invoice_path}")
        return response
    except Exception as e:
        logger.error(f"Error serving invoice PDF {invoice_path}: {str(e)}")
        return HttpResponse("Error serving invoice", status=500)


def autocomplete_invoice_queryset(term='', product_id='', supplier_id=''):
    logger.info(f"Invoice autocomplete term: '{term}', product_id: {product_id}, supplier_id: {supplier_id}")

    qs = Imports.objects.all()

    if supplier_id:
        logger.info(f"Filtering by supplier_id: {supplier_id}")
        qs = qs.filter(supplier_id=supplier_id)

    if product_id:
        logger.info(f"Filtering by product_id: {product_id}")
        qs = qs.filter(stock__product_id=product_id)

    if term.strip():
        qs = qs.filter(invoice__icontains=term)

    qs = qs.distinct()

    logger.info(f"Found imports: {[item.invoice for item in qs]}")

    invoices = []
    for item in qs:
        invoice_data = {
            'value': item.import_id,
            'label': f"Invoice {item.invoice} (Import {item.import_id})",
            'costs_per_euro': float(item.costs_per_euro),
            'vat': float(item.vat or 0),
            'invoice_eur': float(item.invoice_eur or 0),
            'supplier_id': item.supplier_id,
            'id': item.import_id
        }
        invoices.append(invoice_data)

    logger.info(f"Invoice autocomplete results: {invoices}")
    return invoices
