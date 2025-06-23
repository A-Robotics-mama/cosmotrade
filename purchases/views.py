# purchases/views.py
from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_GET
from django.core.exceptions import ObjectDoesNotExist
from django.views.decorators.csrf import csrf_exempt
from django.db.models import F

from datetime import datetime
from decimal import Decimal
from stock.models import Stock
from products.models import Products
from suppliers.models import Suppliers
from imports.models import Imports
from devices.models import Devices
from .models import Purchases
from utils.stock import calculate_stock_price

import logging

logger = logging.getLogger(__name__)

def parse_date(date_str):
    if not date_str:
        return None
    for date_format in [
        '%d/%m/%y', '%d/%m/%Y',  # DD/MM/YY, DD/MM/YYYY
        '%Y/%m/%d', '%Y-%m-%d',  # YYYY/MM/DD, YYYY-MM-DD
        '%d-%m-%y', '%d-%m-%Y',  # DD-MM-YY, DD-MM-YYYY
        '%d.%m.%y', '%d.%m.%Y'   # DD.MM.YY, DD.MM.YYYY
    ]:
        try:
            return datetime.strptime(date_str, date_format).date()
        except ValueError:
            continue
    return None

def purchase_new(request):
    if request.method == 'POST':
        invoice = request.POST.get('invoice')
        product_id = request.POST.get('product_id')
        serial_number = request.POST.get('serial_number')
        purchase_price = Decimal(request.POST.get('purchase_price', '0'))
        qty = int(request.POST.get('qty', 0))
        expiry_date_str = request.POST.get('expiry_date')
        stock_price_input = request.POST.get('stock_price')
        if stock_price_input:
            stock_price = Decimal(stock_price_input)
        else:
            stock_price = Decimal(calculate_stock_price(product.id, import_obj.import_id))

        vat = Decimal(request.POST.get('vat', '0'))
        device = request.POST.get('device') == 'on'
        timestamp = timezone.now()
        manager_id = request.user.id if request.user.is_authenticated else 1

        # Конвертируем дату истечения срока годности
        expiry_date = parse_date(expiry_date_str)
        if expiry_date_str and expiry_date is None:
            return render(request, 'purchase_new.html', {
                'error': 'Invalid expiry date format. Please use DD/MM/YY (e.g., 28/05/25).',
            })

        try:
            # Заменяем get() на filter(...).first()
            import_obj = Imports.objects.filter(invoice=invoice).first()
            if not import_obj:
                return render(request, 'purchase_new.html', {
                    'error': f'Import with invoice {invoice} not found.',
                })
        except Exception as e:
            return render(request, 'purchase_new.html', {
                'error': f'Error finding import: {str(e)}',
            })

        try:
            product = Products.objects.get(id=product_id)
        except Products.DoesNotExist:
            return render(request, 'purchase_new.html', {
                'error': f'Product with ID {product_id} not found.',
            })

        if serial_number:
            existing_purchase = Purchases.objects.filter(serial_number=serial_number).exclude(id=None).first()
            if existing_purchase:
                return render(request, 'purchase_new.html', {
                    'error': f'A purchase with serial number {serial_number} already exists.',
                })

        purchase = Purchases(
            product=product,
            purchase_price=purchase_price,
            qty=qty,
            stock_price=stock_price,
            expiry_date=expiry_date,
            manager_id=manager_id,
            timestamp=timestamp,
            invoice=invoice,
            vat=vat,
            serial_number=serial_number if serial_number else None
        )
        print(f"Saving purchase: stock_price={purchase.stock_price}, vat={purchase.vat}, import_vat_per_euro={import_obj.import_vat_per_euro}")
        purchase.save()

        if serial_number:
            try:
                device = Devices.objects.get(serial_number=serial_number)
            except Devices.DoesNotExist:
                Devices.objects.create(
                    supplier_id=import_obj.supplier,
                    serial_number=serial_number,
                    purchase_date=import_obj.date,
                    sale_date=None,
                    customer_id=None,
                    installation_date=None,
                    notes=None
                )

        stock, created = Stock.objects.get_or_create(
            product=product,
            import_id=import_obj,
            expiry_date=expiry_date,
            defaults={
                'stock_in': qty,
                'stock_out': 0,
                'created_at': timestamp
            }
        )
        if not created:
            stock.stock_in += qty
            stock.unit_price = stock_price
            stock.save()

        return redirect('purchases:purchase_list')

    return render(request, 'purchase_new.html', {})

def purchase_edit(request, purchase_id=None):
    if request.method == 'POST':
        purchase_id = request.POST.get('purchase_id')
        if not purchase_id or not purchase_id.isdigit():
            return redirect('purchases:purchase_list')
        
        purchase = Purchases.objects.get(id=purchase_id)
        
        if 'update' in request.POST:
            purchase.purchase_price = Decimal(request.POST.get('purchase_price', purchase.purchase_price))
            purchase.qty = int(request.POST.get('qty', purchase.qty))
            stock_price_input = request.POST.get('stock_price')
            if stock_price_input:
                purchase.stock_price = Decimal(stock_price_input)
            else:
                import_obj = Imports.objects.filter(invoice=purchase.invoice).first()
                if import_obj:
                    purchase.stock_price = Decimal(calculate_stock_price(purchase.product_id, import_obj.import_id))
                else:
                    purchase.stock_price = Decimal('0')

            purchase.vat = Decimal(request.POST.get('vat', purchase.vat))
            purchase.serial_number = request.POST.get('serial_number', purchase.serial_number)
            expiry_date_str = request.POST.get('expiry_date', '')
            if expiry_date_str:
                purchase.expiry_date = parse_date(expiry_date_str)
                if purchase.expiry_date is None:
                    return render(request, 'purchase_edit.html', {
                        'error': 'Invalid expiry date format. Please use DD/MM/YY (e.g., 28/05/25).',
                        'purchase': purchase
                    })
            else:
                purchase.expiry_date = None
            purchase.save()
            return redirect('purchases:purchase_list')
        
        elif 'delete' in request.POST:
            purchase.delete()
            return redirect('purchases:purchase_list')
        
        return render(request, 'purchase_edit.html', {'purchase': purchase})
    
    else:
        if purchase_id:
            try:
                purchase = Purchases.objects.get(id=purchase_id)
                return render(request, 'purchase_edit.html', {'purchase': purchase})
            except Purchases.DoesNotExist:
                return render(request, 'purchase_edit.html', {
                    'error': f'No purchase found with ID {purchase_id}.',
                    'purchases': None
                })
        
        search_query = request.GET.get('purchase_id', '')
        purchases = None
        if search_query and search_query.isdigit():
            purchases = Purchases.objects.filter(id=search_query)
        
        return render(request, 'purchase_edit.html', {
            'purchases': purchases,
            'purchase_id': search_query
        })

def purchase_list(request):
    supplier_id = request.GET.get('supplier_id', '')
    product_id = request.GET.get('product_id', '')
    invoice = request.GET.get('invoice', '')
    supplier_input = request.GET.get('supplier_input', '')
    product_input = request.GET.get('product_input', '')
    invoice_input = request.GET.get('invoice_input', '')

    purchases = Purchases.objects.all()

    if supplier_id and supplier_id.isdigit():
        purchases = purchases.filter(product__supplier_id=int(supplier_id))
    if product_id and product_id.isdigit():
        purchases = purchases.filter(product_id=int(product_id))
    if invoice:
        purchases = purchases.filter(invoice=invoice)

    return render(request, 'purchase_list.html', {
        'purchases': purchases,
        'supplier_id': supplier_id,
        'product_id': product_id,
        'invoice': invoice,
        'supplier_input': supplier_input,
        'product_input': product_input,
        'invoice_input': invoice_input,
    })



@require_GET
def stock_imports_for_product(request):
    product_id = request.GET.get("product_id")
    if not product_id:
        return JsonResponse({"error": "Missing product_id"}, status=400)
    
    stocks = Stock.objects.filter(product_id=product_id, stock_in__gt=F('stock_out'))
    data = [
        {
            "import_id": stock.import_id.import_id,
            "expiry_date": stock.expiry_date.strftime('%d/%m/%Y') if stock.expiry_date else "",
            "available_qty": stock.stock_in - stock.stock_out,
        }
        for stock in stocks
    ]
    return JsonResponse({"results": data})


@require_GET
def get_stock_price(request):
    product_id = request.GET.get("product_id")
    import_id = request.GET.get("import_id")
    if not product_id or not import_id:
        return JsonResponse({"error": "Missing product_id or import_id"}, status=400)
    
    try:
        price = calculate_stock_price(int(product_id), int(import_id))
        return JsonResponse({"price": str(price)})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
