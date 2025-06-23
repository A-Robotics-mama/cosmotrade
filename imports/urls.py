# imports/urls.py
from django.urls import path
from . import views

app_name = 'imports'

urlpatterns = [
    path('new/', views.import_new, name='import_new'),
    path('edit/', views.import_edit, name='import_edit'),
    path('list/', views.import_list, name='import_list'),
    path('success/<str:message>/', views.import_success, name='import_success'),
    path('supplier-code-autocomplete/', views.supplier_code_autocomplete, name='supplier_code_autocomplete'),
    path('autocomplete/', views.import_autocomplete, name='import_autocomplete'),
    path('delete/<int:import_id>/', views.import_delete, name='import_delete'),
]