# orders/models.py
from django.db import models

class PurchaseOrder(models.Model):
    id = models.AutoField(primary_key=True)
    po_number = models.CharField(max_length=50, unique=True)
    #supplier = models.ForeignKey('suppliers.Suppliers', on_delete=models.CASCADE, related_name='orders_purchase_orders')
    supplier = models.ForeignKey(
    'suppliers.Suppliers',
    on_delete=models.CASCADE,
    related_name='orders_purchase_orders',
    db_column='supplier'  # <-- обязательно!
)
    
    delivery_address = models.TextField()
    contact_person = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = '"d"."purchases_purchaseorder"'

    def __str__(self):
        return self.po_number

class PurchaseOrderItem(models.Model):
    id = models.AutoField(primary_key=True)
    purchase_order = models.ForeignKey(
        PurchaseOrder, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey('products.Products', on_delete=models.CASCADE, related_name='orders_purchase_order_items')
    quantity = models.IntegerField()

    class Meta:
        managed = False
        db_table = '"d"."purchases_purchaseorderitem"'