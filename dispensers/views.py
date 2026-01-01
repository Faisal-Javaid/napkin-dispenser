from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from .models import Dispenser, DispenserProduct
from .serializers import DispenserSerializer, DispenserProductSerializer
from users.permissions import IsAdmin, IsAdminOrMaintenance
from logs.models import Log
from products.models import Product

class DispenserViewSet(viewsets.ModelViewSet):
    queryset = Dispenser.objects.all().prefetch_related('rows', 'rows__product')
    serializer_class = DispenserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdmin()]
        return [IsAuthenticated()]
    
    def get_queryset(self):
        # All authenticated users can view dispensers
        return Dispenser.objects.all().prefetch_related('rows', 'rows__product')
    
    @action(detail=False, methods=['get'])
    def nearby(self, request):
        """Get nearby dispensers (simplified for MVP)"""
        lat = request.query_params.get('lat')
        lng = request.query_params.get('lng')
        
        # In production, implement geospatial query
        # For MVP, return all dispensers
        dispensers = self.get_queryset()
        serializer = self.get_serializer(dispensers, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdminOrMaintenance])
    def add_product(self, request, pk=None):
        """Add or update product in dispenser row"""
        dispenser = self.get_object()
        row_number = request.data.get('row_number')
        product_id = request.data.get('product_id')
        max_capacity = request.data.get('max_capacity', 0)
        current_inventory = request.data.get('current_inventory', max_capacity)
        
        try:
            row_number = int(row_number)
            if not 1 <= row_number <= 4:
                return Response({'error': 'Row number must be between 1 and 4'}, 
                              status=status.HTTP_400_BAD_REQUEST)
        except (ValueError, TypeError):
            return Response({'error': 'Invalid row number'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        # Get product if provided
        product = None
        if product_id:
            try:
                product = Product.objects.get(id=product_id, is_active=True)
            except Product.DoesNotExist:
                return Response({'error': 'Product not found or inactive'}, 
                              status=status.HTTP_404_NOT_FOUND)
        
        try:
            with transaction.atomic():
                dispenser_product, created = DispenserProduct.objects.update_or_create(
                    dispenser=dispenser,
                    row_number=row_number,
                    defaults={
                        'product': product,
                        'max_capacity': max_capacity,
                        'current_inventory': current_inventory
                    }
                )
                
                action_type = 'added' if created else 'updated'
                Log.objects.create(
                    level='info',
                    action='DISPENSER_PRODUCT_UPDATED',
                    description=f'Product {action_type} to dispenser {dispenser.location_name} row {row_number}',
                    user_id=request.user.id,
                    ip_address=self._get_client_ip(request),
                    metadata={
                        'dispenser_id': str(dispenser.id),
                        'row_number': row_number,
                        'product_id': str(product.id) if product else None,
                        'max_capacity': max_capacity,
                        'current_inventory': current_inventory
                    }
                )
                
                serializer = DispenserProductSerializer(dispenser_product)
                return Response(serializer.data, 
                              status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
                
        except Exception as e:
            Log.objects.create(
                level='error',
                action='DISPENSER_PRODUCT_UPDATE_ERROR',
                description=f'Failed to update dispenser product: {str(e)}',
                user_id=request.user.id,
                ip_address=self._get_client_ip(request),
                error_message=str(e)
            )
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        return x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR')