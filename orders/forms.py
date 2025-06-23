from django import forms
from django.forms import inlineformset_factory
from .models import PurchaseOrder, PurchaseOrderItem
from suppliers.models import Suppliers
from products.models import Products

class PurchaseOrderForm(forms.ModelForm):
    class Meta:
        model = PurchaseOrder
        fields = ['po_number', 'supplier', 'delivery_address', 'contact_person']
        widgets = {
            'po_number': forms.TextInput(attrs={'class': 'form-control'}),
            'supplier': forms.Select(attrs={'class': 'form-select'}),
            'delivery_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'contact_person': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['supplier'].queryset = Suppliers.objects.all()

class PurchaseOrderItemForm(forms.ModelForm):
    product_autocomplete = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control product-autocomplete', 'placeholder': 'Search Product...'}),
        label="Product",
        required=True
    )
    product_id = forms.CharField(
        widget=forms.HiddenInput(attrs={'class': 'product-id'}),
        required=True
    )

    class Meta:
        model = PurchaseOrderItem
        fields = ['quantity']
        widgets = {
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['product_autocomplete'].initial = self.instance.product.product_name
            self.fields['product_id'].initial = self.instance.product.id

    def clean(self):
        cleaned_data = super().clean()
        product_id = cleaned_data.get('product_id')
        if not product_id:
            raise forms.ValidationError("Please select a product.")
        try:
            product = Products.objects.get(id=product_id)
            cleaned_data['product'] = product
        except Products.DoesNotExist:
            raise forms.ValidationError("Selected product does not exist.")
        quantity = cleaned_data.get('quantity')
        if quantity is not None and quantity <= 0:
            raise forms.ValidationError("Quantity must be greater than 0.")
        return cleaned_data

# ✅ Новый: функция для создания formset с нужным extra
def get_purchase_order_item_formset(extra=1):
    return inlineformset_factory(
        PurchaseOrder,
        PurchaseOrderItem,
        form=PurchaseOrderItemForm,
        extra=extra,
        can_delete=True
    )
