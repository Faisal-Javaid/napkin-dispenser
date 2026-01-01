from django.db import models
import uuid

class Dispenser(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ble_beacon_id = models.CharField(max_length=100, unique=True)
    location_name = models.CharField(max_length=200)
    gps_coordinates = models.JSONField()  # {'lat': 24.7136, 'lng': 46.6753}
    install_date = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'dispensers'
        ordering = ['location_name']

    def __str__(self):
        return f'{self.location_name} ({self.ble_beacon_id})'

class DispenserProduct(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dispenser = models.ForeignKey(Dispenser, on_delete=models.CASCADE, related_name='rows')
    row_number = models.IntegerField()
    product = models.ForeignKey('products.Product', on_delete=models.SET_NULL, 
                                null=True, blank=True, related_name='dispenser_products')
    current_inventory = models.IntegerField(default=0)
    max_capacity = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'dispenser_products'
        unique_together = ['dispenser', 'row_number']
        ordering = ['dispenser', 'row_number']

    def __str__(self):
        product_name = self.product.product_name if self.product else 'Empty'
        return f'{self.dispenser.location_name} - Row {self.row_number}: {product_name}'