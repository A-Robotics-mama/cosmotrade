# reports/views.py

import logging
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.core.mail import EmailMessage
from django.utils import timezone
from django.db.models import Sum

from customers.models import Customers
from products.models import Products
from payments.models import PaymentCode
from sales.models import TradeMargin, SalesInvoice, Quotation, ItemsQuotation

from reports.services import (
 
    delete_quotation,
    get_quotation_list,
    serve_invoice_file,
    autocomplete_invoice_queryset
)
from reports.pdf.quotation import generate_quotation_pdf
from reports.pdf.invoice import generate_invoice_pdf

logger = logging.getLogger(__name__)



def quotation_list(request):
    customer_id = request.GET.get('customer_hidden')
    quotations = get_quotation_list(customer_id=customer_id)

    return render(request, 'quotation_list.html', {
        'quotations': quotations,
        'customer': request.GET.get('customer', ''),
        'customer_hidden': customer_id or ''
    })


def quotation_delete(request, quotation_number):
    if request.method != "POST":
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    success, message = delete_quotation(quotation_number)
    if not success:
        return JsonResponse({'error': message}, status=400)

    return JsonResponse({'success': message, 'redirect_url': '/reports/quotations/'})


def invoice_pdf(request, invoice_number):
    try:
        pdf_data = generate_invoice_pdf(request, invoice_number, as_bytes=True)
        response = HttpResponse(pdf_data, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="invoice_{invoice_number}.pdf"'
        response['Content-Length'] = len(pdf_data)
        return response
    except Exception as e:
        logger.error(f"Error generating invoice PDF {invoice_number}: {str(e)}")
        return HttpResponse("Error generating invoice", status=500)


def quotation_pdf(request, quotation_number):
    logger.info(f"Generating PDF for quotation_number: {quotation_number}")
    try:
        quotation = Quotation.objects.get(quotation_number=quotation_number)
        items = ItemsQuotation.objects.filter(quotation=quotation)
        if not items.exists():
            logger.error(f"No items found for quotation {quotation_number}")
            return HttpResponse("No items found for this quotation", status=404)
        
        pdf_bytes = generate_quotation_pdf(request, quotation, items, as_bytes=True)
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="quotation_{quotation_number}.pdf"'
        return response
    except Quotation.DoesNotExist:
        logger.error(f"Quotation {quotation_number} not found")
        return HttpResponse("Quotation not found", status=404)
    except Exception as e:
        logger.error(f"Error generating quotation PDF {quotation_number}: {str(e)}")
        return HttpResponse(f"Error generating PDF: {str(e)}", status=500)


def quotation_details(request, quotation_number):
    if request.method != 'GET':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    quotation = Quotation.objects.get(quotation_number=quotation_number)
    items = ItemsQuotation.objects.filter(quotation=quotation)
    if not items.exists():
        return JsonResponse({'error': f'No items found for quotation {quotation_number}'}, status=404)

    total_amount = items.aggregate(total=Sum('total_with_vat'))['total'] or 0.00
    data = {
        'items': list(items.values('id', 'product__product_name', 'qty', 'total_with_vat')),
        'total_amount': float(total_amount)
    }
    return JsonResponse(data)


def serve_invoice(request, invoice_number):
    return serve_invoice_file(invoice_number)


def invoice_autocomplete(request):
    term = request.GET.get('term', '')
    product_id = request.GET.get('product_id', '')
    supplier_id = request.GET.get('supplier_id', '')
    data = autocomplete_invoice_queryset(term, product_id, supplier_id)
    return JsonResponse(data, safe=False)
