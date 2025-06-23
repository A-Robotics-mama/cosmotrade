# sales/admin.py
from django.contrib import admin
from .models import RetailSale

@admin.register(RetailSale)
class RetailSaleAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'customer', 'sell_date', 'total_with_vat')
    search_fields = ('product__product_name', 'customer__customer_name')
    list_filter = ('sell_date', 'vat_rate')
