from rest_framework import serializers
from .models import Product

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['product_id', 'product_name', 'credit_cost', 'is_active', 'created_at']
        read_only_fields = ['product_id', 'created_at']