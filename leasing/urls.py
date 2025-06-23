# leasing/urls.py
from django.urls import path
from . import views

app_name = 'leasing'

urlpatterns = [
    path('new/', views.leasing_new, name='leasing_new'),
    path('list/', views.leasing_list, name='leasing_list'),
    path('delete/<str:contract_no>/', views.leasing_delete, name='leasing_delete'),
    path('edit/', views.leasing_edit, name='leasing_edit'),
    path('pay/', views.leasing_pay, name='leasing_pay'),
]