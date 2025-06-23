# purchases/models.py
from django.db import models
from decimal import Decimal

class Purchases(models.Model):
    id = models.AutoField(primary_key=True)
    product = models.ForeignKey('products.Products', on_delete=models.CASCADE)
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2)
    qty = models.IntegerField()
    stock_price = models.DecimalField(max_digits=10, decimal_places=2)
    expiry_date = models.DateField(blank=True, null=True)
    manager_id = models.IntegerField()
    timestamp = models.DateTimeField()
    invoice = models.CharField(max_length=50)
    vat = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    serial_number = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = '"d"."purchases"'