# products/urls.py
from django.urls import path
from .views import product_list, product_create, product_edit, product_list_json, product_autocomplete

app_name = 'products'

urlpatterns = [
    path('products/', product_list, name='product_list'),
    path('products/add/', product_create, name='product_create'),
    path('products/edit/<int:product_id>/', product_edit, name='product_edit'),
    path('products/json/', product_list_json, name='product_list_json'),
    path('products/autocomplete/', product_autocomplete, name='product_autocomplete'),
]