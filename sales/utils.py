# sales/utils.py

from decimal import Decimal, InvalidOperation
import logging
from django.utils import timezone
from django.contrib import messages
from customers.models import Customers
from imports.models import Imports
from products.models import Products
from sales.models import SalesInvoice
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
    crude_price = stock_price * trade_margin
    discount_amount = crude_price * (trade_discount / 100)
    price_after_discount = crude_price - discount_amount
    commission_amount = price_after_discount * (agent_commission_rate / 100)
    final_sell_price_without_vat = price_after_discount - commission_amount
    vat_amount = final_sell_price_without_vat * (vat_rate / 100) * qty
    customer_price = final_sell_price_without_vat + vat_amount
    profit = (final_sell_price_without_vat - stock_price) * qty
    return {
        'crude_price': crude_price,
        'discount_amount': discount_amount,
        'commission_amount': commission_amount,
        'final_sell_price_without_vat': final_sell_price_without_vat,
        'vat_amount': vat_amount,
        'customer_price': customer_price,
        'profit': profit
    }


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