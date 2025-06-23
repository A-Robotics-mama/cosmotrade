# rent/urls.py
from django.urls import path
from . import views

app_name = 'rent'

urlpatterns = [
    path('new/', views.rent_new, name='rent_new'),
    path('update/<int:rent_id>/', views.rent_update, name='rent_update'),
    path('list/', views.rent_list, name='rent_list'),
    path('edit/', views.rent_edit, name='rent_edit'),
]