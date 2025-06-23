# devices/urls.py
from django.urls import path
from . import views

app_name = 'devices'

urlpatterns = [
    path('edit/', views.devices_edit, name='devices_edit'),
    path('list/', views.devices_list, name='devices_list'),
    path('detail/<int:device_id>/', views.device_detail, name='device_detail'),
    path('serial-number-autocomplete/', views.serial_number_autocomplete, name='serial_number_autocomplete'),
]