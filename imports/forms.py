# imports/forms.py
from django import forms
from decimal import Decimal
from suppliers.models import Suppliers
from .models import Imports

class ImportsForm(forms.ModelForm):
    supplier = forms.ModelChoiceField(
        queryset=Suppliers.objects.all(),
        label='Supplier',
        required=True
    )
    date = forms.DateField(
        input_formats=['%d/%m/%Y', '%Y-%m-%d'],
        widget=forms.DateInput(attrs={
            'type': 'text',
            'class': 'form-control',
            'id': 'date',
            'placeholder': 'dd/mm/yyyy'
        }),
        label='Date',
        required=True
    )

    class Meta:
        model = Imports
        fields = ['supplier', 'date', 'invoice', 'invoice_eur', 'freight', 'vat', 'duty', 'other', 'freight_invoice']
        labels = {
            'invoice': 'Invoice',
            'invoice_eur': 'Invoice (€)',
            'freight': 'Freight (€)',
            'vat': 'Import VAT (€)',
            'duty': 'Duty (€)',
            'other': 'Other Costs (€)',
            'freight_invoice': 'Freight Invoice'
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in ['freight', 'vat', 'duty', 'other', 'freight_invoice']:
            self.fields[field].required = False

    def clean(self):
        cleaned_data = super().clean()
        invoice_eur = cleaned_data.get('invoice_eur') or Decimal('0')
        freight = cleaned_data.get('freight') or Decimal('0')
        vat = cleaned_data.get('vat') or Decimal('0')
        duty = cleaned_data.get('duty') or Decimal('0')
        other = cleaned_data.get('other') or Decimal('0')

        cleaned_data['total_costs'] = freight + vat + duty + other
        cleaned_data['summary_import'] = invoice_eur + cleaned_data['total_costs']
        cleaned_data['costs_per_euro'] = cleaned_data['total_costs'] / invoice_eur if invoice_eur else Decimal('0')

        supplier = cleaned_data.get('supplier')
        if supplier:
            cleaned_data['supplier_id'] = supplier.supplier_id

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.supplier_id = self.cleaned_data['supplier_id']
        instance.total_costs = self.cleaned_data['total_costs']
        instance.summary_import = self.cleaned_data['summary_import']
        instance.costs_per_euro = self.cleaned_data['costs_per_euro']
        if commit:
            instance.save()
        return instance