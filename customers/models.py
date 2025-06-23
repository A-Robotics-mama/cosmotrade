# customers/models.py
from django.db import models

# customers/models.py
from django.db import models
from base.models import Countries

class Customers(models.Model):
    # customer_id = models.AutoField(primary_key=True)
    # fullname = models.CharField(max_length=100)
    # legal_name = models.CharField(max_length=50, blank=True, null=True)
    customer_id = models.IntegerField(primary_key=True)
    fullname = models.CharField(max_length=100, null=False)
    legal_name = models.CharField(max_length=50, blank=True, null=True)
    group_id = models.CharField(max_length=10)
    country_iso = models.ForeignKey(Countries, on_delete=models.SET_NULL, null=True, db_column='country_iso', to_field='country_iso')
    street_address = models.CharField(max_length=255, blank=True, null=True)
    postcode = models.CharField(max_length=10, blank=True, null=True)
    landline = models.CharField(max_length=20, blank=True, null=True)
    mobile = models.CharField(max_length=20, blank=True, null=True)
    email = models.CharField(max_length=100, blank=True, null=True)
    instagram = models.CharField(max_length=255, blank=True, null=True)
    web = models.CharField(max_length=255, blank=True, null=True)
    contact_person = models.CharField(max_length=255, blank=True, null=True)
    birthday = models.DateField(blank=True, null=True)
    nameday = models.DateField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    vat = models.CharField(max_length=20, blank=True, null=True)
    credit_rating = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    customer_type = models.CharField(max_length=20, choices=[
        ('CORPORATE', 'Corporate'),
        ('INDIVIDUAL_SELLER', 'Individual Seller'),
        ('INDIVIDUAL_BUYER', 'Individual Buyer'),
    ], default='INDIVIDUAL_BUYER')

    class Meta:
        managed = False
        db_table = '"d"."customers"'
        verbose_name = "Customer"
        verbose_name_plural = "Customers"

    def __str__(self):
        return self.legal_name if self.legal_name else self.fullname
    
class CustomersGroups(models.Model):
    group_id = models.CharField(primary_key=True, max_length=10)
    group_desc = models.CharField(unique=True, max_length=50)

    class Meta:
        managed = False
        db_table = '"d"."customers_groups"'
        verbose_name = "Customer Group"
        verbose_name_plural = "Customer Groups"

class CustomerBalance(models.Model):
    id = models.AutoField(primary_key=True)
    customer = models.ForeignKey(Customers, on_delete=models.CASCADE)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    already_paid = models.DecimalField(max_digits=10, decimal_places=2)
    balance_to_pay = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=20, choices=[
        ('CASH_SALE', 'Cash Sale'),
        ('LEASING', 'Leasing'),
        ('RENT', 'Rent'),
        ('QUOTATION', 'Quotation'),  # Добавляем новое значение
    ])
    transaction_id = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True)
    invoice_number = models.CharField(max_length=50, blank=True, null=True)  # Добавляем поле для номера инвойса
    vat_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    product_type = models.CharField(max_length=20, blank=True, null=True, choices=[
        ('DEVICE', 'Device'),
        ('COSMETICS', 'Cosmetics'),
        ('SUPPLEMENTS', 'Supplements'),
    ])
    invoice_number = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = False
        db_table = '"d"."customer_balance"'
        verbose_name = "Customer Balance"
        verbose_name_plural = "Customer Balances"

class CustomerPayments(models.Model):
    payment_id = models.AutoField(primary_key=True)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField()
    payment_code = models.SmallIntegerField()
    payment_details = models.TextField(null=True, blank=True)
    customer = models.ForeignKey('Customers', on_delete=models.CASCADE, null=True, blank=True)
    transaction_type = models.CharField(max_length=20, choices=[
        ('CASH_SALE', 'Cash Sale'),
        ('LEASING', 'Leasing'),
        ('RENT', 'Rent'),
        ('RETURN', 'Return'),
        ('QUOTATION', 'Quotation'),  # Оставляем как есть
    ], null=True, blank=True)
    transaction_id = models.CharField(max_length=50, null=True, blank=True)
    vat_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    installment_number = models.IntegerField(null=True, blank=True)
    product_type = models.CharField(max_length=20, choices=[
        ('DEVICE', 'Device'),
        ('COSMETICS', 'Cosmetics'),
        ('SUPPLEMENTS', 'Supplements'),
        ('FURNITURE', 'Furniture'),
    ], null=True, blank=True)

    class Meta:
        managed = False
        db_table = '"d"."customer_payments"'

    def __str__(self):
        return f"Payment {self.payment_id} - {self.customer.fullname if self.customer else 'N/A'}"
