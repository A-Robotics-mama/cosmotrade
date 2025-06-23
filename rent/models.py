# /app/rent/models.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from customers.models import Customers
from products.models import Products


class Rent(models.Model):
    rent_id = models.AutoField(primary_key=True)
    serial_number = models.CharField(max_length=50)
    current_hours = models.DecimalField(max_digits=10, decimal_places=2)
    last_reported_hours = models.DecimalField(max_digits=10, decimal_places=2)
    last_report_date = models.DateField(blank=True, null=True)
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2)
    rental_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    total_amount_due = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        managed = False
        db_table = '"t"."rent"'

    def __str__(self):
        return f"Rent {self.rent_id} - Serial: {self.serial_number}"

