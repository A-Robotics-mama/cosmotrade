# sales/models.py
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from customers.models import Customers
from products.models import Products
from imports.models import Imports
from stock.models import Stock
from decimal import Decimal, InvalidOperation
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

# -------------------- Котировки ----------------------
class Quotation(models.Model):
    quotation_number = models.CharField(max_length=255, unique=True, primary_key=True)  # Совместимость с reports
    customer = models.ForeignKey(Customers, on_delete=models.SET_NULL, null=True, blank=True, db_column='customer_id', related_name='sales_quotations')
    created_at = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, choices=[
        ('PENDING', 'Pending'),
        ('COMPLETED', 'Completed'),
    ], default='PENDING')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)  # Добавлено из reports.Quotation

    class Meta:
        managed = False
        db_table = '"d"."quotation"'
        verbose_name = "Quotation"
        verbose_name_plural = "Quotations"

    def __str__(self):
        return self.quotation_number

# -------------------- Детали котировок ----------------------
class ItemsQuotation(models.Model):
    quotation = models.ForeignKey(Quotation, on_delete=models.CASCADE, db_column='quotation_number')
    product = models.ForeignKey(Products, on_delete=models.SET_NULL, null=True, db_column='product_id')
    import_id = models.ForeignKey(Imports, on_delete=models.SET_NULL, null=True, db_column='import_id')
    qty = models.PositiveIntegerField()
    sell_price = models.DecimalField(max_digits=10, decimal_places=2)
    vat_rate = models.DecimalField(max_digits=5, decimal_places=2)
    sale_vat = models.DecimalField(max_digits=10, decimal_places=2)  # Исправлено с max_length на max_digits
    total_with_vat = models.DecimalField(max_digits=10, decimal_places=2)
    trade_margin = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    trade_discount = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        managed = False
        db_table = '"d"."items_quotation"'
        verbose_name = "Items Quotation"
        verbose_name_plural = "Items Quotations"

    def __str__(self):
        return f"Item for {self.quotation.quotation_number} - {self.product.product_name}"
# -------------------- Розничные продажи ----------------------
class RetailSale(models.Model):
    id = models.AutoField(primary_key=True)
    product = models.ForeignKey(Products, on_delete=models.SET_NULL, null=True, db_column='product_id')
    customer = models.ForeignKey(Customers, on_delete=models.SET_NULL, null=True, db_column='customer_id')
    sell_date = models.DateField(default=timezone.now)
    qty = models.PositiveIntegerField()
    sell_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    vat_rate = models.DecimalField(max_digits=5, decimal_places=2)
    sale_vat = models.DecimalField(max_digits=10, decimal_places=2)
    total_with_vat = models.DecimalField(max_digits=10, decimal_places=2)
    payment_code = models.CharField(max_length=20, blank=True, null=True)
    agent_commission = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    profit_wo_vat = models.DecimalField(max_digits=10, decimal_places=2)
    vat_to_pay = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    manager_id = models.IntegerField(blank=True, null=True)
    timestamp = models.DateTimeField(default=timezone.now)
    invoice = models.CharField(max_length=50, blank=True, null=True)
    serial_number = models.CharField(max_length=50, blank=True, null=True)
    trade_margin = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    trade_discount = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    import_id = models.ForeignKey('imports.Imports', on_delete=models.SET_NULL, null=True, db_column='import_id')

    class Meta:
        managed = False
        db_table = '"d"."sales_retail"'

    def __str__(self):
        return f"RetailSale #{self.id} - {self.product} to {self.customer}"

# -------------------- Официальные продажи ---------------------
class SalesInvoice(models.Model):
    id = models.AutoField(primary_key=True)
    quotation = models.ForeignKey(Quotation, on_delete=models.SET_NULL, null=True, blank=True, db_column='quotation_id')
    customer = models.ForeignKey(Customers, on_delete=models.SET_NULL, null=True, db_column='customer_id')
    sell_date = models.DateField(default=timezone.now)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)  # Общая сумма без НДС
    vat_rate = models.DecimalField(max_digits=5, decimal_places=2)
    sale_vat = models.DecimalField(max_digits=10, decimal_places=2)  # Сумма НДС
    total_with_vat = models.DecimalField(max_digits=10, decimal_places=2)  # Общая сумма с НДС
    sale_type = models.CharField(max_length=20, choices=[
        ('QUOTATION', 'Quotation'),
        ('INVOICED', 'Invoiced'),
    ])
    status = models.CharField(max_length=20, choices=[
        ('PENDING', 'Pending'),
        ('PAID', 'Paid'),
    ])
    agent_commission = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    profit_wo_vat = models.DecimalField(max_digits=10, decimal_places=2)
    manager_id = models.IntegerField(blank=True, null=True)
    timestamp = models.DateTimeField(default=timezone.now)
    invoice = models.CharField(max_length=50, blank=True, null=True)
    trade_margin = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    trade_discount = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    quotation_number = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = '"d"."sales_invoice"'

    def __str__(self):
        return f"Sale Invoice {self.id} - {self.quotation_number or self.invoice}"
    
    @property
    def final_sell_price_without_vat(self):
        """Финальная цена без НДС — пересчитанная из total_with_vat"""
        try:
            return self.total_with_vat / (Decimal("1") + (self.vat_rate / 100))
        except (InvalidOperation, ZeroDivisionError):
            return self.total_with_vat

# -------------------- Детали оплаченных продаж ----------------------
class ItemsSold(models.Model):
    sales_invoice = models.ForeignKey(SalesInvoice, on_delete=models.CASCADE, db_column='sales_invoice_id')
    product = models.ForeignKey(Products, on_delete=models.SET_NULL, null=True, db_column='product_id')
    import_id = models.ForeignKey(Imports, on_delete=models.SET_NULL, null=True, db_column='import_id')
    qty = models.PositiveIntegerField()
    sell_price = models.DecimalField(max_digits=10, decimal_places=2)
    vat_rate = models.DecimalField(max_digits=5, decimal_places=2)
    sale_vat = models.DecimalField(max_digits=10, decimal_places=2)
    total_with_vat = models.DecimalField(max_digits=10, decimal_places=2)
    trade_margin = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    trade_discount = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        managed = False
        db_table = '"d"."items_sold"'
        verbose_name = "Items Sold"
        verbose_name_plural = "Items Sold"

    def __str__(self):
        return f"Item for Invoice {self.sales_invoice.id} - {self.product.product_name}"

#------------------------ TradeMargin ------------------------------------
class TradeMargin(models.Model):
    id = models.AutoField(primary_key=True)
    trade_margin = models.DecimalField(max_digits=5, decimal_places=2)

    class Meta:
        managed = False
        db_table = '"d"."trade_margin"'

    def __str__(self):
        return f"{self.trade_margin}%"
    
# ----------------- Command(BaseCommand) -----------------------

class Command(BaseCommand):
    help = 'Unblocks stock for unpaid quotations older than 10 days.'

    def handle(self, *args, **options):
        threshold_date = timezone.now() - timedelta(days=10)
        quotations = SalesInvoice.objects.filter(
            sale_type='QUOTATION',
            status='PENDING',
            timestamp__lt=threshold_date
        )

        count = 0
        for q in quotations:
            try:
                stock = Stock.objects.get(product_id=q.product_id, import_id=q.import_id_id)
                stock.blocked = max(stock.blocked - q.qty, 0)
                stock.save()
                q.status = 'EXPIRED'
                q.save()
                count += 1
            except Stock.DoesNotExist:
                continue

        self.stdout.write(self.style.SUCCESS(f"✔ Unblocked stock for {count} expired quotations."))