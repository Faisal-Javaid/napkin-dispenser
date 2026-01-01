from rest_framework import serializers
from .models import Transaction
from users.serializers import UserSerializer
from dispensers.serializers import DispenserSerializer
from products.serializers import ProductSerializer

class TransactionSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    dispenser = DispenserSerializer(read_only=True)
    product = ProductSerializer(read_only=True)
    
    class Meta:
        model = Transaction
        fields = ['id', 'user', 'dispenser', 'product', 'row_number', 
                  'credits_used', 'status', 'timestamp']
        read_only_fields = fields

class TransactionCreateSerializer(serializers.Serializer):
    dispenser_id = serializers.UUIDField()
    product_id = serializers.UUIDField()
    row_number = serializers.IntegerField(min_value=1, max_value=4)
    
    def validate(self, data):
        # Additional validation can be added here
        return data