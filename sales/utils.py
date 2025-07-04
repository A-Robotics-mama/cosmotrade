# sales/utils.py

from decimal import Decimal, InvalidOperation
import logging
from django.utils import timezone
from django.contrib import messages
from django.http import JsonResponse
from django.db import transaction, connection
from django.db.models import Sum, F

from customers.models import Customers
from imports.models import Imports
from products.models import Products
from sales.models import Quotation, SalesInvoice, ItemsQuotation
from stock.models import Stock
from decimal import Decimal, InvalidOperation
import logging

logger = logging.getLogger(__name__)


def validate_sale_data(request, customer_id, product_id, import_id, qty):
    try:
        customer = Customers.objects.get(customer_id=customer_id)
        product = Products.objects.get(id=product_id)
        import_obj = Imports.objects.get(import_id=import_id)
        stock = Stock.objects.get(product_id=product.id, import_id=import_obj.import_id)

        if stock.stock_in - stock.stock_out < int(qty):
            raise ValueError(f"Not enough stock. Available: {stock.stock_in - stock.stock_out}, Requested: {qty}")

        price = stock.stock_price or Decimal('0.00')
        return customer, product, import_obj, price

    except Exception as e:
        raise ValueError(f"Invalid sale data: {str(e)}")


def calculate_sale_totals(stock_price, trade_margin, qty, vat_rate, trade_discount, agent_commission_rate):
    stock_price = safe_decimal(stock_price)
    trade_margin = safe_decimal(trade_margin)
    qty = int(qty)
    vat_rate = safe_decimal(vat_rate)
    trade_discount = safe_decimal(trade_discount)
    agent_commission_rate = safe_decimal(agent_commission_rate)

    crude_price = stock_price * trade_margin
    discount_amount = (crude_price * trade_discount) / 100
    price_after_discount = crude_price - discount_amount
    commission_amount = (price_after_discount * agent_commission_rate) / 100
    final_sell_price_without_vat = price_after_discount - commission_amount
    total_no_vat = final_sell_price_without_vat * qty  # Total w/o VAT
    sale_vat = (total_no_vat * vat_rate) / 100  # VAT on total w/o VAT
    total_with_vat = total_no_vat + sale_vat  # Total including VAT
    profit_wo_vat = (final_sell_price_without_vat - stock_price) * qty  # Profit calculation

    return {
        'crude_price': crude_price,
        'discount_amount': discount_amount,
        'commission_amount': commission_amount,
        'final_sell_price_without_vat': final_sell_price_without_vat,
        'vat_amount': sale_vat,
        'customer_price': total_with_vat,
        'profit': profit_wo_vat,
    }


def add_to_quotation_logic(request):
    from django.utils import timezone
    from django.http import JsonResponse
    from django.db import transaction
    from django.db.models import Sum
    from decimal import Decimal
    import logging
    from customers.models import Customers
    from imports.models import Imports
    from products.models import Products
    from sales.models import Quotation, ItemsQuotation
    from stock.models import Stock

    logger = logging.getLogger(__name__)

    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    customer_id = request.POST.get('customer_id')
    import_id = request.POST.get('import_id')
    product_id = request.POST.get('product_id')
    qty = request.POST.get('qty', '0')
    quotation_number = request.POST.get('quotation_number', 'new')

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

    required_keys = ['final_sell_price_without_vat', 'vat_rate', 'vat_amount', 'customer_price',
                     'trade_margin', 'trade_discount', 'profit', 'timestamp']
    missing = [key for key in required_keys if key not in sale_data]
    if missing:
        return JsonResponse({'error': f"Отсутствуют ключи в sale_data: {missing}"}, status=400)

    try:
        customer = Customers.objects.get(customer_id=customer_id)
        product = Products.objects.get(id=product_id)
        import_obj = Imports.objects.get(import_id=import_id)
        stock = Stock.objects.get(product_id=product.id, import_id=import_obj.import_id)

        with transaction.atomic():
            quotation, _ = Quotation.objects.get_or_create(
                quotation_number=quotation_number,
                defaults={
                    'customer': customer,
                    'total_amount': Decimal('0.00'),
                    'created_at': timezone.now(),
                    'status': 'PENDING'
                }
            )

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
                    profit=sale_data['profit'],
                    timestamp=sale_data['timestamp']
                )

            quotation.total_amount = ItemsQuotation.objects.filter(quotation=quotation).aggregate(
                total=Sum('total_with_vat')
            )['total'] or Decimal('0.00')
            quotation.save()

            quotation_sales = list(ItemsQuotation.objects.filter(quotation=quotation).values(
                'id', 'product__product_name', 'qty', 'sell_price', 'vat_rate',
                'sale_vat', 'total_with_vat', 'trade_margin', 'trade_discount'
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
        return JsonResponse({'error': f"Ошибка при сохранении: {str(e)}"}, status=400)


def calculate_totals(sales_queryset):
    total_with_vat = sum([sale.total_with_vat for sale in sales_queryset])
    total_vat = sum([sale.sale_vat for sale in sales_queryset])
    return total_with_vat, total_vat


def generate_invoice_number(prefix):
    today = timezone.now().date()
    prefix_str = f"{prefix}-{today.strftime('%Y%m%d')}-"
    last_sale = SalesInvoice.objects.filter(invoice__startswith=prefix_str).order_by('-invoice').first()
    new_number = 1
    if last_sale:
        try:
            last_number = int(last_sale.invoice.split('-')[-1])
            new_number = last_number + 1
        except (ValueError, IndexError):
            new_number = 1
    invoice_number = f"{prefix_str}{new_number:06d}"
    while SalesInvoice.objects.filter(invoice=invoice_number).exists():
        new_number += 1
        invoice_number = f"{prefix_str}{new_number:06d}"
    return invoice_number


def generate_quotation_number():
    today = timezone.now().date()
    prefix = f"QUOTATION-{today.strftime('%Y%m%d')}-"
    last_sale = SalesInvoice.objects.filter(quotation_number__startswith=prefix).order_by('-quotation_number').first()
    new_number = int(last_sale.quotation_number[-6:]) + 1 if last_sale else 1
    return f"{prefix}{new_number:06d}"


def safe_decimal(val):
    try:
        val = str(val).replace(',', '.').strip()
        if not val or val.lower() in ['none', 'nan']:
            return Decimal('0.00')
        return Decimal(val)
    except (InvalidOperation, ValueError, TypeError):
        return Decimal('0.00')


def save_sale(quotation, product, customer, import_obj, sale_data, request):
    logger.info(f"📥 Entered save_sale() with: product_id={product.id}, qty={sale_data.get('qty')}, customer_id={customer.customer_id}, import_id={import_obj.import_id}")

    try:
        logger.info(f"save_sale called with sale_data: {sale_data}")

        required_keys = ['qty', 'final_sell_price_without_vat', 'vat_rate', 'vat_amount', 'customer_price', 'profit', 'sell_date', 'timestamp']
        missing = [key for key in required_keys if key not in sale_data]
        if missing:
            logger.error(f"Missing keys in sale_data: {missing}")
            raise ValueError(f"Missing required keys: {', '.join(missing)}")

        sale = SalesInvoice(
            quotation_number=quotation.quotation_number,
            product_id=product.id,
            customer_id=customer.customer_id,
            import_id_id=import_obj.import_id,
            sell_date=sale_data['sell_date'],
            qty=sale_data['qty'],
            sell_price=sale_data['final_sell_price_without_vat'],
            total_price=sale_data['final_sell_price_without_vat'] * sale_data['qty'],
            vat_rate=sale_data['vat_rate'],
            sale_vat=sale_data['vat_amount'],
            total_with_vat=sale_data['customer_price'],
            sale_type='QUOTATION',
            status='PENDING',
            agent_commission=sale_data.get('commission_amount', Decimal('0.0')),
            profit_wo_vat=sale_data['profit'],
            manager_id=request.user.id if request.user.is_authenticated else 1,
            timestamp=sale_data['timestamp'],
            trade_margin=sale_data.get('trade_margin', Decimal('0.0')),
            trade_discount=sale_data.get('trade_discount', Decimal('0.0'))
        )

        logger.info(f"📝 Creating sale object with: product={product.id}, qty={sale_data['qty']}, quotation_number={quotation.quotation_number}")
        sale.save()
        logger.info(f"✅ Sale saved successfully: id={sale.id}, quotation_number={quotation.quotation_number}")

        # Блокировка товара
        stock = Stock.objects.get(product_id=product.id, import_id=import_obj.import_id)
        stock.blocked += sale_data['qty']
        stock.save()
        logger.info(f"📦 Stock updated for product {product.id}, blocked now={stock.blocked}")

        return True, "Product added to quotation and stock blocked."

    except Stock.DoesNotExist as e:
        logger.error(f"Stock not found: {str(e)}")
        return False, "Stock record not found."
    except ValueError as e:
        logger.error(f"Validation error in save_sale: {str(e)}")
        return False, str(e)
    except Exception as e:
        logger.error(f"Unexpected error in save_sale: {str(e)} with sale_data={sale_data}")
        return False, f"Failed to save sale: {str(e)}"
    

def fetch_stock_price(product_id, import_id):
    try:
        stock = Stock.objects.get(product_id=product_id, import_id=import_id)
        return stock.stock_price or Decimal('0.00')
    except Stock.DoesNotExist:
        return Decimal('0.00')


