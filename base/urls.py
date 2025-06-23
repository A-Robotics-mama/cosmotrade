# base/urls.py
from django.urls import path
from . import views

app_name = 'base'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('supplier-autocomplete/', views.supplier_autocomplete, name='supplier_autocomplete'),
    path('invoices-autocomplete/', views.invoices_autocomplete, name='invoices_autocomplete'),
    path("countries/autocomplete/", views.country_autocomplete, name="country_autocomplete"), 
]