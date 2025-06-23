from django import forms
from .models import Customers

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customers
        fields = '__all__'
        widgets = {
            'birthday': forms.DateInput(attrs={'type': 'date'}),
            'nameday': forms.DateInput(attrs={'type': 'date'}),
        }
