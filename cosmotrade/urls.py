from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('base.urls', namespace='base')),
    path('', include('products.urls', namespace='products')),
    path('', include('suppliers.urls', namespace='suppliers')),
    path('', include('orders.urls', namespace='orders')),
    path('', include('purchases.urls', namespace='purchases')),
    path('imports/', include('imports.urls', namespace='imports')),
    path('stock/', include('stock.urls', namespace='stock')),
    path('sales/', include('sales.urls', namespace='sales')),
    path('customers/', include('customers.urls', namespace='customers')),
    path('devices/', include('devices.urls')),
    path('leasing/', include('leasing.urls')),
    path('payments/', include('payments.urls')),
    path('rent/', include('rent.urls')),
    path('reports/', include('reports.urls', namespace='reports')),  # Убедимся, что namespace задан
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)