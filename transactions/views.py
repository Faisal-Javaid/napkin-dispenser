from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction as db_transaction
from django.shortcuts import get_object_or_404
from .models import Transaction
from .serializers import TransactionSerializer, TransactionCreateSerializer
from users.permissions import IsAdmin, IsCustomer
from users.models import User, Wallet
from dispensers.models import Dispenser, DispenserProduct
from products.models import Product
from logs.models import Log

class TransactionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        if user.is_admin:
            return Transaction.objects.select_related('user', 'dispenser', 'product').all()

        # Users can only see their own transactions
        return Transaction.objects.select_related('user', 'dispenser', 'product').filter(user=user)

    @action(detail=False, methods=['post'], permission_classes=[IsCustomer])
    def purchase(self, request):
        """Process a purchase transaction"""
        serializer = TransactionCreateSerializer(data=request.data)
        if not serializer.is_valid():
            Log.objects.create(
                level='warn',
                action='TRANSACTION_FAILED',
                description='Transaction failed - invalid data',
                user_id=request.user.id,
                ip_address=self._get_client_ip(request),
                request_body=request.data,
                error_message=str(serializer.errors)
            )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        user = request.user

        try:
            with db_transaction.atomic():
                # Get product with lock
                product = get_object_or_404(Product.objects.select_for_update(),
                                          product_id=data['product_id'], is_active=True)

                # Get dispenser
                dispenser = get_object_or_404(Dispenser, dispenser_id=data['dispenser_id'])

                # Get dispenser product row with lock
                dispenser_product = get_object_or_404(
                    DispenserProduct.objects.select_for_update(),
                    dispenser=dispenser,
                    row_number=data['row_number'],
                    product=product
                )

                # Get user wallet with lock
                wallet = get_object_or_404(Wallet.objects.select_for_update(), user=user)

                # Validate transaction
                if dispenser_product.current_inventory <= 0:
                    Log.objects.create(
                        level='warn',
                        action='TRANSACTION_FAILED',
                        description=f'Transaction failed - product out of stock',
                        user_id=user.id,
                        ip_address=self._get_client_ip(request),
                        metadata={
                            'dispenser_id': str(dispenser.id),
                            'product_id': str(product.id),
                            'row_number': data['row_number']
                        }
                    )
                    return Response({'error': 'Product out of stock'},
                                  status=status.HTTP_400_BAD_REQUEST)

                if wallet.balance < product.credit_cost:
                    Log.objects.create(
                        level='warn',
                        action='TRANSACTION_FAILED',
                        description=f'Transaction failed - insufficient credits',
                        user_id=user.id,
                        ip_address=self._get_client_ip(request),
                        metadata={
                            'required_credits': product.credit_cost,
                            'available_credits': wallet.balance
                        }
                    )
                    return Response({'error': 'Insufficient credits'},
                                  status=status.HTTP_400_BAD_REQUEST)

                # Process transaction
                dispenser_product.current_inventory -= 1
                dispenser_product.save()

                wallet.balance -= product.credit_cost
                wallet.save()

                # Create transaction record
                transaction = Transaction.objects.create(
                    user=user,
                    dispenser=dispenser,
                    product=product,
                    row_number=data['row_number'],
                    credits_used=product.credit_cost,
                    status=Transaction.Status.SUCCESS
                )

                # Log successful transaction
                Log.objects.create(
                    level='info',
                    action='TRANSACTION_SUCCESS',
                    description=f'Transaction successful - {product.product_name} purchased',
                    user_id=user.id,
                    ip_address=self._get_client_ip(request),
                    metadata={
                        'transaction_id': str(transaction.id),
                        'credits_used': product.credit_cost,
                        'new_balance': wallet.balance
                    }
                )

                return Response({
                    'transaction_id': str(transaction.id),
                    'credits_used': product.credit_cost,
                    'new_balance': wallet.balance,
                    'product_name': product.product_name,
                    'status': 'success'
                }, status=status.HTTP_201_CREATED)

        except Exception as e:
            Log.objects.create(
                level='error',
                action='TRANSACTION_ERROR',
                description=f'Transaction processing error: {str(e)}',
                user_id=user.id,
                ip_address=self._get_client_ip(request),
                error_message=str(e),
                request_body=request.data
            )
            return Response({'error': 'Transaction processing failed'},
                          status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def user_transactions(self, request):
        """Get transactions for a specific user (admin can view any, users can view only their own)"""
        user_id = request.query_params.get('user_id')

        if user_id and request.user.is_admin:
            user = get_object_or_404(User, id=user_id)
            transactions = Transaction.objects.filter(user=user)
        else:
            transactions = Transaction.objects.filter(user=request.user)

        page = self.paginate_queryset(transactions)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(transactions, many=True)
        return Response(serializer.data)

    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        return x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR')