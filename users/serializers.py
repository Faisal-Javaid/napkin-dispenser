from rest_framework import serializers
from .models import User, Wallet

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'phone_number', 'email', 'user_type', 
                  'account_type', 'account_verified', 'is_active',
                  'created_at']
        read_only_fields = ['id', 'created_at', 'account_verified']

class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    
    class Meta:
        model = User
        fields = ['id', 'phone_number', 'email', 'password', 
                  'user_type', 'account_type']
        
    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        # Create wallet for customers
        if user.user_type == User.UserType.CUSTOMER:
            Wallet.objects.create(user=user)
        return user

class UserLoginSerializer(serializers.Serializer):
    phone_number = serializers.CharField(required=False)
    email = serializers.EmailField(required=False)
    password = serializers.CharField(write_only=True)

class WalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = ['id', 'balance', 'subscription_end_date', 'created_at']