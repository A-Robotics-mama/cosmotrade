# app/payments/models.py
from django.db import models

class PaymentCode(models.Model):
    code = models.SmallIntegerField(primary_key=True)
    description = models.CharField(max_length=50)

    class Meta:
        db_table = '"d"."payment_codes"'  # Явно указываем схему
        managed = False

    def __str__(self):
        return f"{self.code} - {self.description}"

