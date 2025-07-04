# sales/services.py
import logging
import traceback
import os
from decimal import Decimal
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.db.models import Sum
from django.core.mail import EmailMessage
from django.db import transaction
from django.template.loader import render_to_string
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings

from customers.models import Customers, CustomerBalance, CustomerPayments
from payments.models import PaymentCode
from products.models import Products
from sales.models import Quotation, SalesInvoice, TradeMargin, ItemsQuotation, ItemsSold, SalesCash, ItemsCash
from stock.models import Stock
from imports.models import Imports
from .utils import (
    validate_sale_data,
    calculate_sale_totals,
    calculate_totals,
    generate_quotation_number,
    generate_invoice_number,
    safe_decimal,
    save_sale,
    fetch_stock_price   
)
from reports.email_utils import send_quotation_email, send_invoice_email
from reports.pdf.invoice import generate_invoice_pdf
from reports.email_utils import send_invoice_email

from .exceptions import (
    SalesError,
    InvalidCustomerError,
    InvalidProductError,
    InvalidImportError,
    InsufficientStockError,
    InvalidQuotationError
)

from reports.pdf.quotation import generate_quotation_pdf

logger = logging.getLogger(__name__)

from django.shortcuts import render, redirect
from django.contrib import messages
from decimal import Decimal

from customers.models import Customers
from products.models import Products
from stock.models import Stock
from sales.models import RetailSale
from sales.utils import validate_sale_data



from decimal import Decimal

from django.shortcuts import render, redirect
from django.contrib import messages
from decimal import Decimal
from .models import RetailSale
from customers.models import Customers
from products.models import Products
from imports.models import Imports
from stock.models import Stock
from .utils import validate_sale_data
from django.utils import timezone

def handle_sale_retail(request):
    if request.method == "POST":
        customer_id = request.POST.get("customer_id")
        product_id = request.POST.get("product_id")
        import_id = request.POST.get("import_id")
        qty = request.POST.get("qty")

        if not all([customer_id, product_id, import_id, qty]):
            messages.error(request, "Missing required sale data.")
            return render(request, "sale_retail.html")

        try:
            qty = int(qty)
            if qty <= 0:
                raise ValueError
        except ValueError:
            messages.error(request, "Quantity must be a positive integer.")
            return render(request, "sale_retail.html")

        customer, product, import_obj, stock_price = validate_sale_data(request, customer_id, product_id, import_id, qty)
        if not all([customer, product, import_obj]):
            return render(request, "sale_retail.html")

        # Получение текущего остатка
        stock_record = Stock.objects.filter(product=product, import_id=import_obj).first()
        if not stock_record:
            messages.error(request, "No stock entry found for this product and import.")
            return render(request, "sale_retail.html")

        available_qty = stock_record.stock_in - stock_record.stock_out - stock_record.blocked
        if qty > available_qty:
            messages.error(request, f"Insufficient stock. Only {available_qty} available.")
            return render(request, "sale_retail.html")

        # Финансовые расчёты (пример с 5% VAT)
        vat_rate = Decimal('5.0')
        sale_vat = (stock_price * vat_rate / 100).quantize(Decimal("0.01"))
        total_with_vat = ((stock_price + sale_vat) * qty).quantize(Decimal("0.01"))
        profit = ((stock_price - Decimal(stock_record.stock_price)) * qty).quantize(Decimal("0.01"))

        # Сохраняем продажу
        RetailSale.objects.create(
            customer=customer,
            product=product,
            import_id=import_obj,
            qty=qty,
            sell_price=stock_price,
            total_price=stock_price * qty,
            vat_rate=vat_rate,
            sale_vat=sale_vat,
            total_with_vat=total_with_vat,
            profit_wo_vat=profit,
            sell_date=timezone.now().date()
        )

        # Обновляем stock_out
        stock_record.stock_out += qty
        stock_record.save()

        messages.success(request, f"✅ Sale recorded for {product.product_name} (x{qty})")
        return redirect("sales:sale_retail")

    return render(request, "sale_retail.html")


def handle_sale_invoice(request, quotation_number):
    customers = Customers.objects.all()
    products = Products.objects.all()
    payment_codes = PaymentCode.objects.all()
    trade_margins = TradeMargin.objects.all()

    quotation_sales = []
    status = 'PENDING'

    if quotation_number != "new":
        quotation_sales = SalesInvoice.objects.filter(
            quotation_number=quotation_number,
            sale_type='QUOTATION'
        )
        q = Quotation.objects.filter(quotation_number=quotation_number).first()
        if q:
            status = q.status

    if request.method == 'POST':
        try:
            customer_id = request.POST.get('customer_id')
            product_id = request.POST.get('product_id')
            import_id = request.POST.get('import_id')
            qty = int(request.POST.get('qty', 0))
            vat_rate = Decimal(request.POST.get('vat_rate', '0'))
            trade_margin = Decimal(request.POST.get('trade_margin', '0'))
            trade_discount = Decimal(request.POST.get('trade_discount', '0'))
            agent_commission_rate = Decimal(request.POST.get('agent_commission_rate', '0'))

            validated = validate_sale_data(request, customer_id, product_id, import_id, qty)
            if validated is None:
                raise SalesError("Недопустимые данные. Убедитесь, что клиент, товар, импорт и количество выбраны правильно.")
            customer, product, import_obj, stock_price = validated

            totals = calculate_sale_totals(stock_price, trade_margin, qty, vat_rate, trade_discount, agent_commission_rate)
            sale_data = {
                **totals,
                'qty': qty,
                'sell_date': timezone.now().date(),
                'timestamp': timezone.now(),
            }

            success, message = save_sale(quotation_number, product, customer, import_obj, sale_data, request)

            quotation_sales = SalesInvoice.objects.filter(
                quotation_number=quotation_number,
                sale_type='QUOTATION'
            )

            # Обновляем статус (вдруг поменялся после save_sale)
            q = Quotation.objects.filter(quotation_number=quotation_number).first()
            if q:
                status = q.status

            return render(request, 'sale_invoice.html', {
                'success': message if success else None,
                'error': None if success else message,
                'quotation_sales': quotation_sales,
                'quotation_number': quotation_number,
                'customers': customers,
                'products': products,
                'payment_codes': payment_codes,
                'trade_margins': trade_margins,
                'has_quotation_sales': quotation_sales.exists(),
                'status': status,
            })

        except (SalesError, InvalidCustomerError, InvalidProductError, InvalidImportError, InsufficientStockError) as e:
            return render(request, 'sale_invoice.html', {
                'customers': customers,
                'products': products,
                'payment_codes': payment_codes,
                'trade_margins': trade_margins,
                'error': str(e),
                'quotation_number': quotation_number,
                'quotation_sales': quotation_sales,
                'has_quotation_sales': quotation_sales and len(quotation_sales) > 0,
                'status': status,
            })

    return render(request, 'sale_invoice.html', {
        'quotation_sales': quotation_sales,
        'quotation_number': quotation_number,
        'customers': customers,
        'products': products,
        'payment_codes': payment_codes,
        'trade_margins': trade_margins,
        'has_quotation_sales': quotation_sales and len(quotation_sales) > 0,
        'status': status,
    })


def add_to_quotation_logic(request):
    logger = logging.getLogger(__name__)
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    customer_id = request.POST.get('customer_id')
    import_id = request.POST.get('import_id')
    product_id = request.POST.get('product_id')
    qty = request.POST.get('qty', '0')

    try:
        qty = int(qty)
    except ValueError:
        return JsonResponse({'error': 'Invalid quantity'}, status=400)

    sell_price = safe_decimal(request.POST.get('sell_price', '0'))
    final_sell_price_without_vat = safe_decimal(request.POST.get('final_sell_price_without_vat', '0'))
    vat_rate = safe_decimal(request.POST.get('vat_rate', '0'))
    trade_margin = safe_decimal(request.POST.get('trade_margin', '0'))
    trade_discount = safe_decimal(request.POST.get('trade_discount', '0'))
    agent_commission_rate = safe_decimal(request.POST.get('agent_commission_rate', '0'))
    sale_vat = safe_decimal(request.POST.get('vat_amount', '0'))
    total_with_vat = safe_decimal(request.POST.get('customer_price', '0'))
    quotation_number = request.POST.get('quotation_number', 'new')
    profit = request.POST.get('profit') or 0


    logger.info(f"Received add_to_quotation: customer_id={customer_id}, product_id={product_id}, import_id={import_id}, qty={qty}, quotation_number={quotation_number}")

    if Quotation.objects.filter(quotation_number='new').exists():
        Quotation.objects.filter(quotation_number='new').delete()
        ItemsQuotation.objects.filter(quotation__quotation_number='new').delete()

    if not quotation_number or quotation_number.lower() == 'new':
        existing_numbers = Quotation.objects.values_list('quotation_number', flat=True)
        base_number = f"QUOTATION-{timezone.now().strftime('%Y%m%d')}"
        counter = 1
        while True:
            new_number = f"{base_number}-{counter:04d}"
            if new_number not in existing_numbers:
                quotation_number = new_number
                break
            counter += 1
        logger.info(f"Generated unique quotation number: {quotation_number}")

    try:
        customer = Customers.objects.get(customer_id=customer_id)
        product = Products.objects.get(id=product_id)
        import_obj = Imports.objects.get(import_id=import_id)
        stock = Stock.objects.get(product_id=product.id, import_id=import_obj.import_id)

        if stock.stock_in - stock.stock_out - stock.blocked < qty:
            return JsonResponse({'error': f"Not enough stock. Available: {stock.stock_in - stock.stock_out - stock.blocked}, Requested: {qty}"}, status=400)

    except Exception as e:
        return JsonResponse({'error': f"Validation error: {str(e)}"}, status=400)

    sale_data = {
        'qty': qty,
        'sell_price': sell_price,
        'vat_rate': vat_rate,
        'trade_discount': trade_discount,
        'agent_commission_rate': agent_commission_rate,
        'final_sell_price_without_vat': final_sell_price_without_vat,
        'vat_amount': sale_vat,
        'customer_price': total_with_vat,
        'trade_margin': trade_margin,
        'timestamp': timezone.now(),
    }

    totals = calculate_sale_totals(
        stock_price=sell_price,
        trade_margin=trade_margin,
        qty=qty,
        vat_rate=vat_rate,
        trade_discount=trade_discount,
        agent_commission_rate=agent_commission_rate,
    )
    sale_data.update(totals)

    try:
        with transaction.atomic():
            if not Quotation.objects.filter(quotation_number=quotation_number).exists():
                quotation = Quotation.objects.create(
                    quotation_number=quotation_number,
                    customer=customer,
                    total_amount=Decimal('0.00'),
                    created_at=timezone.now(),
                    status='PENDING'
                )
            else:
                quotation = Quotation.objects.get(quotation_number=quotation_number)

            if not ItemsQuotation.objects.filter(quotation=quotation, product=product, import_id=import_obj).exists():
                ItemsQuotation.objects.create(
                    quotation=quotation,
                    product=product,
                    import_id=import_obj,
                    qty=qty,
                    sell_price=sale_data['final_sell_price_without_vat'],
                    vat_rate=sale_data['vat_rate'],
                    sale_vat=sale_data['vat_amount'],
                    total_with_vat=sale_data['customer_price'],
                    trade_margin=sale_data['trade_margin'],
                    trade_discount=sale_data['trade_discount'],
                    profit=profit,
                    timestamp=sale_data['timestamp']
                )

            quotation.total_amount = ItemsQuotation.objects.filter(quotation__quotation_number=quotation_number).aggregate(total=Sum('total_with_vat'))['total'] or Decimal('0.00')
            quotation.save()

            quotation_sales = list(ItemsQuotation.objects.filter(
                quotation__quotation_number=quotation_number
            ).values(
                'id',
                'product__product_name',
                'qty',
                'sell_price',
                'vat_rate',
                'sale_vat',
                'total_with_vat',
                'trade_margin',
                'trade_discount',
            ))

            return JsonResponse({
                'success': 'Product added to quotation',
                'quotation_number': quotation_number,
                'quotation_sales': quotation_sales,
                'total_amount': float(quotation.total_amount),
                'quotation_created': True,
                'status': quotation.status
            })

    except Exception as e:
        logger.error(f"Failed to add to quotation: {str(e)}")
        return JsonResponse({'error': f"Failed to add to quotation: {str(e)}"}, status=400)


def complete_quotation_process(quotation_number, request):
    logger = logging.getLogger(__name__)
    logger.info(f"Processing complete_quotation for quotation_number: {quotation_number}")

    try:
        quotation = Quotation.objects.get(quotation_number=quotation_number)

        if quotation.status != 'PENDING':
            return False, f'Quotation {quotation_number} is not pending.'

        items = ItemsQuotation.objects.filter(quotation=quotation)
        if not items.exists():
            return False, f'No items found for quotation {quotation_number}.'

        customer = quotation.customer
        total_with_vat = items.aggregate(total=Sum('total_with_vat'))['total'] or Decimal('0.00')
        total_vat = items.aggregate(total=Sum('sale_vat'))['total'] or Decimal('0.00')
        product_type = 'COSMETICS' if items.first().vat_rate == Decimal('19.00') else 'SUPPLEMENTS'

        with transaction.atomic():
            # ✅ Блокировка товаров
            for item in items:
                stock = Stock.objects.select_for_update().get(product_id=item.product_id, import_id=item.import_id_id)
                available_qty = stock.stock_in - stock.stock_out - stock.blocked
                if available_qty < item.qty:
                    raise ValueError(f"Недостаточно товара на складе для {item.product.product_name}")
                stock.blocked += item.qty
                stock.save(update_fields=["blocked"])
                logger.info(f"✅ Заблокировано {item.qty} ед. для {item.product.product_name} (stock_id={stock.id})")

            # ✅ Обновляем статус и сумму котировки
            quotation.total_amount = total_with_vat
            quotation.status = 'PENDING'  # Остаётся в ожидании оплаты
            quotation.save()

            # ✅ Обновляем/создаём баланс клиента
            CustomerBalance.objects.update_or_create(
                transaction_type='QUOTATION',
                transaction_id=f"QUOTATION-{quotation_number}",
                defaults={
                    'customer': customer,
                    'total_amount': total_with_vat,
                    'already_paid': Decimal('0.00'),
                    'balance_to_pay': total_with_vat,
                    'vat_amount': total_vat,
                    'created_at': timezone.now(),
                    'description': f"Quotation #{quotation_number}",
                    'product_type': product_type
                }
            )

            # ✅ Генерируем PDF и отправляем клиенту
            pdf_bytes = generate_quotation_pdf(request, quotation, items, as_bytes=True)
            if customer.email:
                send_quotation_email(
                    subject=f"Quotation #{quotation_number[10:]}",
                    body=f"Dear {customer.legal_name or customer.fullname},\n\nPlease find attached your Quotation.",
                    to=[customer.email],
                    pdf_bytes=pdf_bytes,
                    filename=f"quotation_{quotation_number}.pdf"
                )

        logger.info(f"Quotation {quotation_number} finalized. Total: {total_with_vat}")
        return True, quotation_number

    except Quotation.DoesNotExist:
        logger.error(f"Quotation {quotation_number} not found")
        return False, f'Quotation {quotation_number} not found.'

    except Exception as e:
        logger.error(f"Error finalizing quotation {quotation_number}: {str(e)}")
        logger.error(traceback.format_exc())
        return False, f'Error finalizing quotation: {str(e)}'


def mark_quotation_as_paid(quotation_number, request):
    logger.info(f"Processing mark_quotation_as_paid for quotation_number: {quotation_number}")

    try:
        with transaction.atomic():
            quotation = Quotation.objects.get(quotation_number=quotation_number)
            if quotation.status != 'PENDING':
                raise ValueError(f"Котировка {quotation_number} не в статусе PENDING (текущий: {quotation.status})")

            items = ItemsQuotation.objects.filter(quotation=quotation)
            if not items.exists():
                raise ValueError(f"Не найдены элементы для котировки {quotation_number}")

            customer = quotation.customer
            total_with_vat = items.aggregate(total=Sum('total_with_vat'))['total'] or Decimal('0.00')
            total_vat = items.aggregate(total=Sum('sale_vat'))['total'] or Decimal('0.00')
            product_type = 'COSMETICS' if items.first().vat_rate == Decimal('19.00') else 'SUPPLEMENTS'

            today = timezone.now().date()
            prefix = f"INV-S-{today.strftime('%Y%m%d')}-"
            last = SalesInvoice.objects.filter(invoice__startswith=prefix).order_by('-invoice').first()
            new_number = int(last.invoice.split('-')[-1]) + 1 if last and last.invoice else 1
            invoice_number = f"{prefix}{new_number:06d}"

            while SalesInvoice.objects.filter(invoice=invoice_number).exists():
                new_number += 1
                invoice_number = f"{prefix}{new_number:06d}"

            for item in items:
                # ✅ Получаем строку склада
                stock = Stock.objects.get(product_id=item.product_id, import_id=item.import_id_id)

                # ✅ Проверка доступного количества
                available_qty = stock.stock_in - stock.stock_out - stock.blocked
                if available_qty < item.qty:
                    raise ValueError(f"Недостаточно доступного товара для {item.product.product_name}")

                # ✅ Обновление: списываем и снимаем блокировку
                stock.blocked = max(0, stock.blocked - item.qty)
                stock.stock_out += item.qty
                stock.save(update_fields=["blocked", "stock_out"])


            profit_wo_vat = total_with_vat - total_vat

            sales_invoice = SalesInvoice.objects.create(
                quotation=quotation,
                customer=customer,
                sell_date=timezone.now().date(),
                total_price=total_with_vat - total_vat,
                vat_rate=items.first().vat_rate,
                sale_vat=total_vat,
                total_with_vat=total_with_vat,
                sale_type='INVOICED',
                status='PAID',
                invoice=invoice_number,
                timestamp=timezone.now(),
                profit_wo_vat=profit_wo_vat,
                quotation_number=quotation_number,
                trade_discount=items.first().trade_discount,
                trade_margin=items.first().trade_margin
            )

            for item in items:
                ItemsSold.objects.create(
                    sales_invoice=sales_invoice,
                    product_id=item.product_id,
                    import_id=item.import_id,
                    qty=item.qty,
                    sell_price=item.sell_price,
                    vat_rate=item.vat_rate,
                    sale_vat=item.sale_vat,
                    total_with_vat=item.total_with_vat,
                    trade_margin=item.trade_margin,
                    trade_discount=item.trade_discount,
                    profit=item.profit,  # ← ВАЖНО: передаём уже рассчитанное
                    timestamp=timezone.now()
                )

            balance = CustomerBalance.objects.filter(
                transaction_type='QUOTATION',
                transaction_id=f"QUOTATION-{quotation_number}"
            ).first()

            if balance:
                balance.transaction_type = 'CASH_SALE'
                balance.already_paid = total_with_vat
                balance.balance_to_pay = Decimal('0.00')
                balance.invoice_number = invoice_number
                balance.save()
            else:
                CustomerBalance.objects.create(
                    customer=customer,
                    transaction_type='CASH_SALE',
                    transaction_id=f"QUOTATION-{quotation_number}",
                    total_amount=total_with_vat,
                    already_paid=total_with_vat,
                    balance_to_pay=Decimal('0.00'),
                    vat_amount=total_vat,
                    created_at=timezone.now(),
                    description=f"Payment for Quotation #{quotation_number}",
                    product_type=product_type,
                    invoice_number=invoice_number
                )

            CustomerPayments.objects.create(
                customer=customer,
                amount_paid=total_with_vat,
                payment_date=timezone.now(),
                payment_code=None,
                payment_details=f"Оплата котировки #{quotation_number} (Инвойс: {invoice_number})",
                transaction_type='CASH_SALE',
                transaction_id=quotation_number,
                vat_amount=total_vat,
                installment_number=0,
                product_type=product_type
            )

            pdf_data = generate_invoice_pdf(request, invoice_number, as_bytes=True)
            if not isinstance(pdf_data, bytes):
                raise ValueError("generate_invoice_pdf did not return bytes")

            if customer.email:
                send_invoice_email(
                    subject=f"Инвойс #{invoice_number}",
                    body=f"Уважаемый {customer.legal_name or customer.fullname},\n\nВ приложении ваш инвойс #{invoice_number}.",
                    to=[customer.email],
                    pdf_bytes=pdf_data,
                    filename=f"invoice_{invoice_number}.pdf",
                    cc=['accounts@cosmotrade-ms.com']
                )

            invoice_path = settings.BASE_DIR / 'documents' / 'invoices_out' / f"invoice_{invoice_number}.pdf"
            invoice_path.parent.mkdir(parents=True, exist_ok=True)
            with open(invoice_path, 'wb') as f:
                f.write(pdf_data)

            quotation.status = 'COMPLETED'
            quotation.save()

            logger.info(f"Котировка {quotation_number} отмечена как оплаченная с инвойсом {invoice_number}")
            return True, customer.customer_id

    except Exception as e:
        logger.error(f"Ошибка при отметке котировки {quotation_number} как оплаченной: {str(e)}")
        logger.error(f"Трассировка: {traceback.format_exc()}")
        return False, str(e)


def get_stock_imports_for_product(request):
    product_id = request.GET.get('product_id')
    if not product_id:
        return JsonResponse({'error': 'Missing product_id'}, status=400)

    try:
        product = Products.objects.get(id=product_id)
    except Products.DoesNotExist:
        return JsonResponse({'error': 'Invalid product_id'}, status=404)

    imports = Imports.objects.filter(stock__product_id=product.id).distinct()

    results = []
    for imp in imports:
        results.append({
            'import_id': imp.import_id,
            'invoice': imp.invoice,
            'label': f"{imp.invoice} (ID: {imp.import_id})",
            'costs_per_euro': float(imp.costs_per_euro or 0),
            'vat': float(imp.vat or 0),
            'invoice_eur': float(imp.invoice_eur or 0),
        })

    return JsonResponse(results, safe=False)


def edit_quotation_service(request, quotation_number):
    if request.method == 'GET':
        try:
            quotation = Quotation.objects.get(quotation_number=quotation_number)
            items = ItemsQuotation.objects.filter(quotation__quotation_number=quotation_number)
            context = {
                'quotation_number': quotation.quotation_number,
                'customer': quotation.customer.legal_name if quotation.customer else None,
                'created_at': quotation.created_at.strftime('%Y-%m-%d'),
                'status': quotation.status,
                'total_amount': float(quotation.total_amount) if quotation.total_amount else 0.0,
                'items': items
            }
            return render(request, 'quotation_edit.html', context)
        except ObjectDoesNotExist:
            return JsonResponse({'error': f'Quotation {quotation_number} not found'}, status=404)
    elif request.method == 'POST':
        try:
            quotation = Quotation.objects.get(quotation_number=quotation_number)
            new_status = request.POST.get('status')
            if new_status in ['PENDING', 'CANCELLED', 'COMPLETED']:
                quotation.status = new_status
                quotation.save()
                return render(request, 'quotation_edit.html', {'success': 'Status updated successfully', 'quotation_number': quotation_number})
            else:
                return JsonResponse({'error': 'Invalid status value'}, status=400)
        except ObjectDoesNotExist:
            return JsonResponse({'error': f'Quotation {quotation_number} not found'}, status=404)
    return JsonResponse({'error': 'Method not allowed'}, status=405)


def handle_sale_cash(request):
    customer_id = request.POST.get('customer_id')
    product_id = request.POST.get('product_id')
    import_id = request.POST.get('import_id')
    invoice = request.POST.get('invoice') or None
    qty = int(request.POST.get('qty') or 0)
    sell_price = Decimal(request.POST.get('sell_price') or '0.00')

    if not (customer_id and product_id and qty > 0 and sell_price > 0):
        return {'success': False, 'message': "Incomplete or invalid data."}

    customer = Customers.objects.get(pk=customer_id)
    product = Products.objects.get(pk=product_id)
    import_obj = Imports.objects.get(pk=import_id) if import_id else None
    total = qty * sell_price
    stock_price = fetch_stock_price(product_id, import_id)
    profit = (sell_price - stock_price) * qty if stock_price is not None else None

    # ✅ Списание со склада
    try:
        stock_entry = Stock.objects.get(product=product, import_id=import_obj)
        available_qty = stock_entry.stock_in - stock_entry.stock_out - stock_entry.blocked
        if qty > available_qty:
            return {'success': False, 'message': f"Not enough stock. Available: {available_qty}"}
        stock_entry.stock_out += qty
        stock_entry.save()
    except Stock.DoesNotExist:
        return {'success': False, 'message': "Stock entry not found."}

    # ✅ Продажа и запись
    sale = SalesCash.objects.create(
        customer=customer,
        sell_date=timezone.now().date(),
        invoice=invoice
    )

    ItemsCash.objects.create(
        sale=sale,
        product=product,
        import_id=import_obj,
        qty=qty,
        sell_price=sell_price,
        total=total,
        profit=profit,
        timestamp=timezone.now()
    )

    return {'success': True, 'message': f"Cash sale recorded. Total: €{total:.2f}"}
