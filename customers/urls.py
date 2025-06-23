# customers/urls.py
from django.urls import path
from . import views

app_name = 'customers'

urlpatterns = [
    path('new/', views.customer_new, name='customer_new'),
    path('edit/', views.customer_edit, name='customer_edit'),
    path('list/', views.customer_list, name='customer_list'),
    path('autocomplete/', views.customer_autocomplete, name='customer_autocomplete'),
    path('group/autocomplete/', views.group_autocomplete, name='group_autocomplete'),  # Новый маршрут
    path('balance/quotation/<int:customer_id>/', views.customer_balance_quotation, name='customer_balance'),
    path('balance/retail/<int:customer_id>/', views.customer_balance_retail, name='customer_balance_retail'),
    path('payments/quotation/', views.customer_payments, name='payments_quotation'),
    path('customer/summary/select/', views.customer_summary_select, name='customer_summary_select'),
    path('customer/summary/<int:customer_id>/', views.customer_summary, name='customer_summary'),
]