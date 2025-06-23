# /apps/base/models.py
from django.db import models

# Модель для стран
class Countries(models.Model):
    country_iso = models.CharField(primary_key=True, max_length=2)
    country_name = models.TextField(blank=True, null=True)
    country_code = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = '"d"."countries"'
        verbose_name = "Country"
        verbose_name_plural = "Countries"
