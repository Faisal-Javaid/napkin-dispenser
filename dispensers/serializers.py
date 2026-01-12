from rest_framework import serializers
from .models import Dispenser, DispenserProduct
from products.serializers import ProductSerializer

class DispenserProductSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = DispenserProduct
        fields = ['id', 'row_number', 'product', 'product_id',
                  'current_inventory', 'max_capacity', 'created_at']
        read_only_fields = ['id', 'created_at']

class DispenserSerializer(serializers.ModelSerializer):
    rows = DispenserProductSerializer(many=True, read_only=True)

    class Meta:
        model = Dispenser
        fields = ['dispenser_id', 'ble_beacon_id', 'location_name', 'gps_coordinates',
                  'install_date', 'created_at', 'rows']
        read_only_fields = ['dispenser_id', 'install_date', 'created_at', 'rows']