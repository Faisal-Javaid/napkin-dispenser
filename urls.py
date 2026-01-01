
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from users.views import AuthViewSet, UserViewSet
from products.views import ProductViewSet
from dispensers.views import DispenserViewSet
from transactions.views import TransactionViewSet
from logs.views import LogViewSet

router = DefaultRouter()
router.register(r'auth', AuthViewSet, basename='auth')
router.register(r'users', UserViewSet, basename='user')
router.register(r'products', ProductViewSet, basename='product')
router.register(r'dispensers', DispenserViewSet, basename='dispenser')
router.register(r'transactions', TransactionViewSet, basename='transaction')
router.register(r'logs', LogViewSet, basename='log')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include(router.urls)),
]