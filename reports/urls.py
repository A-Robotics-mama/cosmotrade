from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('quotations/', views.quotation_list, name='quotation_list'),
    path('quotation/<str:quotation_number>/delete/', views.quotation_delete, name='quotation_delete'),
    path('quotation/<str:quotation_number>/pdf/', views.quotation_pdf, name='quotation_pdf'),
    path('invoice/<str:invoice_number>/pdf/', views.invoice_pdf, name='invoice_pdf'),
    path('invoice/<str:invoice_number>/download/', views.serve_invoice, name='serve_invoice'),
    path('invoice-autocomplete/', views.invoice_autocomplete, name='invoice_autocomplete'),
    path('quotation/details/<str:quotation_number>/', views.quotation_details, name='quotation_details'),
]