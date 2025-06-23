# utils/stock.py

from decimal import Decimal
from imports.models import Imports
from purchases.models import Purchases

def calculate_stock_price(product, import_obj):
    try:
        purchase = Purchases.objects.get(product=product, invoice=import_obj.invoice)
        base_price = purchase.purchase_price
        costs_ratio = import_obj.costs_per_euro or Decimal('0.00')
        return base_price + (base_price * costs_ratio)
    except (Purchases.DoesNotExist, Imports.DoesNotExist, AttributeError):
        return Decimal('0.00')

