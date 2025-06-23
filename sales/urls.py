from django.urls import path
from . import views

app_name = 'sales'

urlpatterns = [
    # Основные интерфейсы
    path('retail/', views.sale_retail, name='sale_retail'),
    path('invoice/<str:quotation_number>/', views.sale_invoice, name='sale_invoice'),
    path('invoice/new/', views.new_invoice_sale, name='new_invoice_sale'),

    # API endpoints
    path('get-stock-price/', views.get_stock_price, name='get_stock_price'),
    path('stock-imports/', views.stock_imports_for_product, name='stock_imports_for_product'),
    path('add-to-quotation/', views.add_to_quotation, name='add_to_quotation'),
    path('quotation/check/', views.check_quotation, name='check_quotation'),  # Восстановленный маршрут

    # Котировки
    path('quotation/<str:quotation_number>/complete/', views.complete_quotation, name='complete_quotation'),
    path('quotation/<str:quotation_number>/mark-paid/', views.mark_quotation_paid, name='mark_quotation_paid'),    
]