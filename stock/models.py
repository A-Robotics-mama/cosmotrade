# stock/models.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from products.models import Products
from imports.models import Imports
from purchases.models import Purchases
from decimal import Decimal

class Stock(models.Model):
    id = models.AutoField(primary_key=True)
    product = models.ForeignKey(Products, on_delete=models.SET_NULL, null=True, db_column='product_id')
    import_id = models.ForeignKey(Imports, on_delete=models.SET_NULL, null=True, db_column='import_id')
    expiry_date = models.DateField(blank=True, null=True)
    stock_in = models.IntegerField()
    stock_out = models.IntegerField()
    created_at = models.DateTimeField(default=timezone.now, null=True)
    vat_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    serial_number = models.CharField(max_length=50, blank=True, null=True)
    blocked = models.IntegerField(default=0)


    class Meta:
        managed = False
        db_table = '"d"."stock"'

    def save(self, *args, **kwargs):
        try:
            purchase = Purchases.objects.get(invoice=self.import_id.invoice, product=self.product)
            self.serial_number = purchase.serial_number if purchase.serial_number else ''
        except Purchases.DoesNotExist:
            self.serial_number = ''
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Stock {self.id} - {self.product}"

    @property
    def stock_price(self):
        try:
            purchase = Purchases.objects.get(invoice=self.import_id.invoice, product=self.product)
            return purchase.stock_price + (purchase.stock_price * Decimal('0.1')) + (purchase.stock_price * Decimal('0.01'))
        except Purchases.DoesNotExist:
            return Decimal('0.00')