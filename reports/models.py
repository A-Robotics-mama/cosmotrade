# /app/reports/models.py
from django.db import models
from payments.models import PaymentCode 
from products.models import Products
from sales.models import Quotation
     
# Модель для инвойсов
class Invoice(models.Model):
    invoice_number = models.CharField(max_length=50, primary_key=True)
    quotation = models.ForeignKey(Quotation, models.DO_NOTHING, db_column='quotation_number')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = '"d"."invoice"'
        verbose_name = "Invoice"
        verbose_name_plural = "Invoices"

# Модель для элементов котировок
class QuotationItems(models.Model):
    id = models.AutoField(primary_key=True)
    quotation = models.ForeignKey(Quotation, models.DO_NOTHING, db_column='quotation_id')
    product = models.ForeignKey(Products, models.DO_NOTHING, db_column='product_id')
    product_code = models.CharField(max_length=255)  # Новое поле
    import_id = models.IntegerField()
    qty = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        managed = False
        db_table = '"d"."quotation_items"'
        verbose_name = "Quotation Item"
        verbose_name_plural = "Quotation Items"