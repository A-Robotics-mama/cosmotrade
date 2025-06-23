# /app/sales/models.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from customers.models import Customers
from devices.models import Devices

class Leasing(models.Model):
    contract_no = models.CharField(max_length=50, primary_key=True)
    customer = models.ForeignKey(Customers, on_delete=models.CASCADE)
    product = models.ForeignKey(Devices, on_delete=models.CASCADE)
    serial_number = models.CharField(max_length=50, blank=True, null=True)
    start_date = models.DateField()
    date_of_payment = models.DateField(blank=True, null=True)
    paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    contract_file = models.CharField(max_length=255, blank=True)
    sell_price = models.DecimalField(max_digits=10, decimal_places=2)
    vat_rate = models.DecimalField(max_digits=5, decimal_places=2)
    sale_vat = models.DecimalField(max_digits=10, decimal_places=2)
    purchase_vat = models.DecimalField(max_digits=10, decimal_places=2)
    vat_to_pay = models.DecimalField(max_digits=10, decimal_places=2)
    first_installment = models.DecimalField(max_digits=10, decimal_places=2)
    number_of_installments = models.IntegerField()
    installment_amount = models.DecimalField(max_digits=10, decimal_places=2)
    already_paid = models.DecimalField(max_digits=10, decimal_places=2)
    balance_to_pay = models.DecimalField(max_digits=10, decimal_places=2)
    agent_commission_rate = models.DecimalField(max_digits=5, decimal_places=2)
    agent_commission = models.DecimalField(max_digits=10, decimal_places=2)
    profit_wo_vat = models.DecimalField(max_digits=10, decimal_places=2)
    last_installment_number = models.IntegerField(default=0)

    class Meta:
        db_table = 'leasing'
        verbose_name = "Leasing"
        verbose_name_plural = "Leasings"

    def __str__(self):
        return f"Leasing {self.contract_no} - Customer {self.customer.fullname}"

