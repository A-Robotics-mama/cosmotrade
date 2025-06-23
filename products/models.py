# products/models.py
from django.db import models

class Brands(models.Model):
    id = models.AutoField(primary_key=True)
    brand_name = models.CharField(max_length=100, unique=True)
    brand_owner = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.brand_name

    class Meta:
        managed = False
        db_table = '"d"."brands"'
        verbose_name = "Brand"
        verbose_name_plural = "Brands"

class ProductForms(models.Model):
    form_id = models.AutoField(primary_key=True)
    form_desc = models.CharField(max_length=255)

    def __str__(self):
        return self.form_desc

    class Meta:
        managed = False
        db_table = '"d"."product_forms"'
        verbose_name = "Product Form"
        verbose_name_plural = "Product Forms"

class ProductCategory(models.Model):
    category_id = models.AutoField(primary_key=True)
    category_name = models.CharField(max_length=100)

    def __str__(self):
        return self.category_name

    class Meta:
        managed = False
        db_table = '"d"."product_category"'
        verbose_name = "Product Category"
        verbose_name_plural = "Product Categories"

class Products(models.Model):
    id = models.AutoField(primary_key=True)
    product_name = models.CharField(max_length=255)
    brand = models.ForeignKey(Brands, on_delete=models.CASCADE, db_column='brand')  # Указываем db_column
    supplier = models.ForeignKey('suppliers.Suppliers', on_delete=models.CASCADE, db_column='supplier')  # Указываем db_column
    form = models.ForeignKey(ProductForms, on_delete=models.CASCADE, db_column='form_id')  # Указываем db_column
    category = models.ForeignKey(ProductCategory, on_delete=models.CASCADE, db_column='category_id')  # Указываем db_column
    product_volume = models.CharField(max_length=50, null=True, blank=True)
    manufacturer_code = models.CharField(max_length=50, unique=True, null=True)

    def __str__(self):
        return self.product_name

    class Meta:
        managed = False
        db_table = '"d"."products"'