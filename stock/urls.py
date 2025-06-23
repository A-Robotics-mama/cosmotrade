# stock/urls.py
from django.urls import path
from . import views

app_name = 'stock'

urlpatterns = [
    path('list/', views.stock_list, name='stock_list'),
    path('expiry_date/', views.stock_expiry_date, name='stock_expiry_date'),
    path('purchase_details/', views.purchase_details, name='purchase_details'),
    path('imports_for_product/', views.stock_imports_for_product, name='stock_imports_for_product'),
]