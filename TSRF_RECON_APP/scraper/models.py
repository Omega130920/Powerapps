from django.db import models

class ProductRegistry(models.Model):
    id = models.AutoField(primary_key=True)
    product_id = models.CharField(max_length=100, blank=True, null=True, db_column='product_id')
    barcode = models.CharField(max_length=50, db_column='barcode')
    product_name = models.TextField(blank=True, null=True, db_column='product_name')
    target_folder = models.CharField(max_length=150, db_column='target_folder')
    
    # NEW DIMENSIONAL METRICS
    pd_height = models.DecimalField(max_length=10, max_digits=10, decimal_places=2, blank=True, null=True, db_column='pd_height')
    pd_length = models.DecimalField(max_length=10, max_digits=10, decimal_places=2, blank=True, null=True, db_column='pd_length')
    pd_width = models.DecimalField(max_length=10, max_digits=10, decimal_places=2, blank=True, null=True, db_column='pd_width')
    
    created_at = models.DateTimeField(auto_now_add=True, db_column='created_at')

    class Meta:
        managed = False  # Stays hand-off
        db_table = 'product_registry'

    def __str__(self):
        return f"{self.barcode} [{self.pd_height}x{self.pd_length}x{self.pd_width}]"