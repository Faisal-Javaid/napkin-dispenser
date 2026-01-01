from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Product
from .serializers import ProductSerializer
from users.permissions import IsAdmin

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdmin()]
        return [permissions.AllowAny()]
    
    def get_queryset(self):
        if self.request.user.is_authenticated and self.request.user.is_admin:
            return Product.objects.all()
        return Product.objects.filter(is_active=True)
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get only active products (public endpoint)"""
        products = Product.objects.filter(is_active=True)
        serializer = self.get_serializer(products, many=True)
        return Response(serializer.data)