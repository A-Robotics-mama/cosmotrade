# suppliers/urls.py
from django.urls import path
from .views import supplier_list, supplier_create, supplier_edit, country_autocomplete

app_name = 'suppliers'

urlpatterns = [
    path('suppliers/', supplier_list, name='supplier_list'),
    path('suppliers/add/', supplier_create, name='supplier_create'),
    path('suppliers/edit/<int:supplier_id>/', supplier_edit, name='supplier_edit'),
    path('suppliers/country-autocomplete/', country_autocomplete, name='country_autocomplete'),
]