# sales/views.py
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponseRedirect
from django.urls import reverse
from django.views.decorators.http import require_GET

from sales.models import SalesInvoice
from imports.models import Imports
from products.models import Products
from utils.stock import calculate_stock_price
from .services import (
    handle_sale_retail,
    handle_sale_invoice,
    add_to_quotation_logic,
    complete_quotation_process,
    mark_quotation_as_paid,
    get_stock_imports_for_product
)
from .utils import generate_quotation_number

import logging

logger = logging.getLogger(__name__)

def sale_retail(request):
    return handle_sale_retail(request)


def sale_invoice(request, quotation_number):
    return handle_sale_invoice(request, quotation_number)


def get_stock_price(request):
    product_id = request.GET.get('product_id')
    import_id = request.GET.get('import_id')
    if not product_id or not import_id:
        return JsonResponse({'error': 'Missing product_id or import_id'}, status=400)

    try:
        product = Products.objects.get(id=product_id)
        import_obj = Imports.objects.get(import_id=import_id)
        stock_price = calculate_stock_price(product, import_obj)
        return JsonResponse({'stock_price': float(stock_price)})
    except (Products.DoesNotExist, Imports.DoesNotExist, ValueError) as e:
        return JsonResponse({'error': str(e)}, status=400)


def add_to_quotation(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    return add_to_quotation_logic(request)


def complete_quotation(request, quotation_number):
    if request.method != "POST":
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    logger.info(f"Received complete_quotation request for quotation_number: {quotation_number}")
    success, message = complete_quotation_process(quotation_number, request)
    if not success:
        return JsonResponse({'error': message}, status=400)

    return JsonResponse({
        'success': message,
        'redirect_url': "/reports/quotations/",
    })


def mark_quotation_paid(request, quotation_number):
    if request.method != "POST":
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        customer, invoice_number = mark_quotation_as_paid(quotation_number)
        return HttpResponseRedirect(reverse('customers:customer_balance', args=[customer.customer_id]))
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


def new_invoice_sale(request):
    quotation_number = generate_quotation_number()
    return redirect('sales:sale_invoice', quotation_number=quotation_number)


def stock_imports_for_product(request):
    return get_stock_imports_for_product(request)


@require_GET
def check_quotation(request):
    quotation_number = request.GET.get('quotation_number')
    if not quotation_number:
        return JsonResponse({'error': 'Missing quotation_number'}, status=400)
    is_empty = not SalesInvoice.objects.filter(quotation_number=quotation_number).exists()
    return JsonResponse({'empty': is_empty})