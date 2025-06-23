# devices/models.py
from django.db import models
from customers.models import Customers
from suppliers.models import Suppliers
from products.models import Products

class Devices(models.Model):
    id = models.AutoField(primary_key=True)
    supplier_id = models.ForeignKey(Suppliers, models.DO_NOTHING, db_column='supplier_id')
    serial_number = models.CharField(max_length=50)
    purchase_date = models.DateField()
    sale_date = models.DateField(blank=True, null=True)
    customer_id = models.ForeignKey(Customers, models.DO_NOTHING, db_column='customer_id', blank=True, null=True)
    installation_date = models.DateField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'devices'
        verbose_name = "Device"
        verbose_name_plural = "Devices"

    def __str__(self):
        return f"Device {self.serial_number} - Supplier {self.supplier_id}"

class DeviceService(models.Model):
    device = models.ForeignKey(Devices, on_delete=models.CASCADE, related_name='services')
    service_date = models.DateField()
    description = models.TextField()
    technician = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'd.device_services'

    def __str__(self):
        return f"Service for {self.device.serial_number} on {self.service_date}"

class DevicePartReplacement(models.Model):
    device = models.ForeignKey(Devices, on_delete=models.CASCADE, related_name='part_replacements')
    part_name = models.CharField(max_length=255)  # Заменили ForeignKey на строку
    replacement_date = models.DateField()
    quantity = models.IntegerField(default=1)
    notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'd.device_part_replacements'  # Обновили схему с t на d

    def __str__(self):
        return f"Part {self.part_name} replaced for {self.device.serial_number} on {self.replacement_date}"


class DeviceMonitoring(models.Model):
    device = models.ForeignKey(Devices, on_delete=models.CASCADE, related_name='monitorings')
    monitoring_date = models.DateField()
    hours_of_operation = models.FloatField(default=0.0)
    pulse_count = models.IntegerField(default=0)
    other_parameters = models.JSONField(null=True, blank=True)
    notes = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'd.device_monitoring'

    def __str__(self):
        return f"Monitoring for {self.device.serial_number} on {self.monitoring_date}"