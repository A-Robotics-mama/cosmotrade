# orders/urls.py
from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('orders/create/', views.purchase_order_create, name='purchase_order_create'),
    path('orders/', views.purchase_order_list, name='purchase_order_list'),
    path('orders/<int:po_id>/', views.purchase_order_detail, name='purchase_order_detail'),
    path('orders/<int:po_id>/edit/', views.purchase_order_edit, name='purchase_order_edit'),
    path('orders/<int:po_id>/delete/', views.purchase_order_delete, name='purchase_order_delete'),
    path('orders/<int:po_id>/send/', views.purchase_order_send_email, name='purchase_order_send_email'),
    path('orders/<int:po_id>/pdf/', views.purchase_order_pdf, name='purchase_order_pdf'),
]