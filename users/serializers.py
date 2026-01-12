from rest_framework import serializers
from .models import User, Wallet

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'phone_number', 'email', 'user_type',
                  'account_type','subscription_type', 'subscription_start_date',
            'subscription_end_date', 'account_verified', 'is_active',
                  'created_at']
        read_only_fields = ['id', 'created_at', 'account_verified']

class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['id', 'phone_number', 'email', 'password',
                  'user_type', 'account_type','subscription_type']

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)

        if user.subscription_type == User.SubscriptionType.BASIC:
            user.subscription_start_date = user.created_at
            user.save()

        elif user.subscription_type == User.SubscriptionType.CORPORATE:
            user.account_verified = True  # Auto-verify corporate accounts
            user.subscription_start_date = user.created_at
            # Corporate plans get 30 days by default
            from django.utils.timezone import now, timedelta
            user.subscription_end_date = now() + timedelta(days=30)
            user.save()
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

class SubscriptionUpdateSerializer(serializers.Serializer):
    subscription_type = serializers.ChoiceField(choices=User.SubscriptionType.choices)
    duration_days = serializers.IntegerField(min_value=1, max_value=365, required=False)

    def validate(self, data):
        subscription_type = data.get('subscription_type')
        duration_days = data.get('duration_days', 30)  # Default 30 days

        if subscription_type == User.SubscriptionType.CORPORATE and not duration_days:
            raise serializers.ValidationError("Duration days is required for corporate subscriptions")

        return data