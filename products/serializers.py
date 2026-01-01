from rest_framework import serializers
from .models import Product

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'product_name', 'credit_cost', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']