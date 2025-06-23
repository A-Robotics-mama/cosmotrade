# purchases/urls.py
from django.urls import path
from . import views

app_name = 'purchases'

urlpatterns = [
    path('purchases/new/', views.purchase_new, name='purchase_new'),
    path('purchases/edit/', views.purchase_edit, name='purchase_edit'),
    path('purchases/edit/<int:purchase_id>/', views.purchase_edit, name='purchase_edit_with_id'),
    path('purchases/list/', views.purchase_list, name='purchase_list'),

    # ✅ Новые маршруты
    path('stock-imports/', views.stock_imports_for_product, name='stock_imports_for_product'),
    path('get-stock-price/', views.get_stock_price, name='get_stock_price'),
]
