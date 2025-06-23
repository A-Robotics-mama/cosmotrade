# imports/models.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from suppliers.models import Suppliers
from decimal import Decimal

class Imports(models.Model):
    import_id = models.BigAutoField(primary_key=True)
    supplier = models.ForeignKey(Suppliers, on_delete=models.CASCADE, db_column='supplier_id')
    date = models.DateField()
    invoice = models.CharField(max_length=50)
    invoice_eur = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    freight = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    vat = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    duty = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    other = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    total_costs = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    summary_import = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    costs_per_euro = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    freight_invoice = models.CharField(max_length=255, blank=True, null=True)
    import_vat_per_euro = models.DecimalField(max_digits=10, decimal_places=4, default=0.00)

    class Meta:
        db_table = '"d"."imports"'
        managed = False

    def __str__(self):
        return f"Import {self.import_id} - {self.supplier.supplier_code} - {self.date}"

    def save(self, *args, **kwargs):
        freight = Decimal(self.freight) if self.freight is not None else Decimal('0.00')
        vat = Decimal(self.vat) if self.vat is not None else Decimal('0.00')
        duty = Decimal(self.duty) if self.duty is not None else Decimal('0.00')
        other = Decimal(self.other) if self.other is not None else Decimal('0.00')
        invoice_eur = Decimal(self.invoice_eur) if self.invoice_eur is not None else Decimal('0.00')

        # Рассчитываем total_costs без учёта VAT
        self.total_costs = freight + duty + other  # Исключаем vat
        self.summary_import = invoice_eur + self.total_costs
        self.costs_per_euro = self.total_costs / invoice_eur if invoice_eur > 0 else Decimal('0.00')
        self.import_vat_per_euro = vat / self.summary_import if self.summary_import > 0 else Decimal('0.00')

        super().save(*args, **kwargs)