# payments/urls.py
from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('payment-code-autocomplete/', views.payment_code_autocomplete, name='payment_code_autocomplete'),
]