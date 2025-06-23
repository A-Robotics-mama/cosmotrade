
# suppliers/models.py
from django.db import models

class Suppliers(models.Model):
    supplier_id = models.AutoField(primary_key=True)
    legal_name = models.TextField()
    country = models.CharField(max_length=2, blank=True, null=True)
    str_address = models.CharField(max_length=255, blank=True, null=True)
    bank = models.TextField(blank=True, null=True)
    bank_address = models.CharField(max_length=255, blank=True, null=True)
    bic = models.CharField(max_length=25, blank=True, null=True)
    bank_acc = models.CharField(max_length=50, blank=True, null=True)
    supplier_code = models.CharField(max_length=3, unique=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    mobile = models.CharField(max_length=20, blank=True, null=True)
    email = models.CharField(max_length=255, blank=True, null=True)
    instagram = models.CharField(max_length=255, blank=True, null=True)
    web = models.CharField(max_length=255, blank=True, null=True)
    contact_person = models.CharField(max_length=255, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.legal_name} ({self.supplier_code})"

    class Meta:
        managed = False
        db_table = '"d"."suppliers"'
        verbose_name = "Supplier"
        verbose_name_plural = "Suppliers"