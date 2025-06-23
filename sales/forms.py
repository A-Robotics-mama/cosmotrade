# apps/sales/forms.py
from django import forms
from .models import RetailSale

class RetailSaleForm(forms.ModelForm):
    class Meta:
        model = RetailSale
        exclude = ['stock_price']  # ❌ Исключаем это поле из формы — рассчитывается автоматически

