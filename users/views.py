
# Create your views here.
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db import transaction
import jwt
from django.conf import settings
from datetime import datetime, timedelta
from .models import User, Wallet
from .serializers import UserSerializer, UserCreateSerializer, UserLoginSerializer, WalletSerializer
from .permissions import IsAdmin, IsOwnerOrAdmin
from logs.models import Log

class AuthViewSet(viewsets.ViewSet):
    permission_classes = [permissions.AllowAny]
    
    @action(detail=False, methods=['post'])
    def register(self, request):
        serializer = UserCreateSerializer(data=request.data)
        if serializer.is_valid():
            # Force customer type for public registration
            data = serializer.validated_data.copy()
            data['user_type'] = User.UserType.CUSTOMER
            data['account_verified'] = data.get('account_type') == User.AccountType.CORPORATE
            
            user = serializer.create(data)
            
            # Generate token
            token = self._generate_token(user)
            
            # Log the registration
            Log.objects.create(
                level='info',
                action='REGISTRATION_SUCCESS',
                description=f'Customer {user.phone_number} registered successfully',
                user_id=user.id,
                ip_address=self._get_client_ip(request),
                metadata={'account_type': user.account_type}
            )
            
            return Response({
                'message': 'User registered successfully',
                'token': token,
                'user': UserSerializer(user).data,
                'wallet': WalletSerializer(user.wallet).data if hasattr(user, 'wallet') else None
            }, status=status.HTTP_201_CREATED)
        
        # Log failed registration
        Log.objects.create(
            level='warn',
            action='REGISTRATION_FAILED',
            description=f'Registration failed for {request.data.get("phone_number")}',
            ip_address=self._get_client_ip(request),
            request_body=request.data,
            error_message=str(serializer.errors)
        )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def login(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            phone_number = serializer.validated_data.get('phone_number')
            email = serializer.validated_data.get('email')
            password = serializer.validated_data.get('password')
            
            # Find user
            try:
                if phone_number:
                    user = User.objects.get(phone_number=phone_number)
                else:
                    user = User.objects.get(email=email)
            except User.DoesNotExist:
                Log.objects.create(
                    level='warn',
                    action='LOGIN_FAILED',
                    description=f'Login failed - user not found',
                    ip_address=self._get_client_ip(request),
                    request_body={'phone_number': phone_number, 'email': email}
                )
                return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
            
            # Check password
            if not user.check_password(password):
                Log.objects.create(
                    level='warn',
                    action='LOGIN_FAILED',
                    description=f'Login failed - invalid password for {user.phone_number}',
                    user_id=user.id,
                    ip_address=self._get_client_ip(request)
                )
                return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
            
            # Check if user is active
            if not user.is_active:
                Log.objects.create(
                    level='warn',
                    action='LOGIN_FAILED',
                    description=f'Login failed - account deactivated for {user.phone_number}',
                    user_id=user.id,
                    ip_address=self._get_client_ip(request)
                )
                return Response({'error': 'Account is deactivated'}, status=status.HTTP_401_UNAUTHORIZED)
            
            # Generate token
            token = self._generate_token(user)
            
            # Log successful login
            Log.objects.create(
                level='info',
                action='LOGIN_SUCCESS',
                description=f'User {user.phone_number} logged in successfully',
                user_id=user.id,
                ip_address=self._get_client_ip(request),
                metadata={'user_type': user.user_type}
            )
            
            return Response({
                'message': 'Login successful',
                'token': token,
                'user': UserSerializer(user).data,
                'wallet': WalletSerializer(user.wallet).data if hasattr(user, 'wallet') else None
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def change_password(self, request):
        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')
        
        if not current_password or not new_password:
            return Response({'error': 'Both current and new password are required'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        user = request.user
        
        if not user.check_password(current_password):
            Log.objects.create(
                level='warn',
                action='PASSWORD_CHANGE_FAILED',
                description=f'Password change failed - incorrect current password',
                user_id=user.id,
                ip_address=self._get_client_ip(request)
            )
            return Response({'error': 'Current password is incorrect'}, 
                          status=status.HTTP_401_UNAUTHORIZED)
        
        user.set_password(new_password)
        user.save()
        
        Log.objects.create(
            level='info',
            action='PASSWORD_CHANGED',
            description=f'Password changed successfully for {user.phone_number}',
            user_id=user.id,
            ip_address=self._get_client_ip(request)
        )
        
        return Response({'message': 'Password updated successfully'})
    
    def _generate_token(self, user):
        payload = {
            'user_id': str(user.id),
            'exp': datetime.utcnow() + settings.JWT_EXPIRATION_DELTA,
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    
    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAdmin]
    
    def get_permissions(self):
        if self.action in ['retrieve', 'update', 'partial_update']:
            return [IsOwnerOrAdmin()]
        return super().get_permissions()
    
    def get_queryset(self):
        if self.request.user.is_admin:
            return User.objects.all()
        return User.objects.filter(id=self.request.user.id)
    
    @action(detail=False, methods=['post'], permission_classes=[IsAdmin])
    def create_user(self, request):
        """Admin endpoint to create users of any type"""
        serializer = UserCreateSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Auto-verify non-customer users
            if user.user_type != User.UserType.CUSTOMER:
                user.account_verified = True
                user.save()
            
            # Create wallet for customers
            if user.user_type == User.UserType.CUSTOMER:
                Wallet.objects.create(user=user)
            
            Log.objects.create(
                level='info',
                action='ADMIN_USER_CREATION',
                description=f'Admin created {user.user_type} user {user.phone_number}',
                user_id=user.id,
                admin_id=request.user.id,
                ip_address=self._get_client_ip(request)
            )
            
            return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAdmin])
    def add_credits(self, request, pk=None):
        user = self.get_object()
        credits = request.data.get('credits', 0)
        
        try:
            credits = int(credits)
            if credits <= 0:
                return Response({'error': 'Credits must be positive'}, 
                              status=status.HTTP_400_BAD_REQUEST)
        except (ValueError, TypeError):
            return Response({'error': 'Invalid credits value'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        wallet, created = Wallet.objects.get_or_create(user=user)
        wallet.balance += credits
        wallet.save()
        
        Log.objects.create(
            level='info',
            action='CREDITS_ADDED',
            description=f'Admin added {credits} credits to user {user.phone_number}',
            user_id=user.id,
            admin_id=request.user.id,
            ip_address=self._get_client_ip(request),
            metadata={'credits_added': credits, 'new_balance': wallet.balance}
        )
        
        return Response({
            'message': f'Added {credits} credits to user',
            'new_balance': wallet.balance
        })
    
    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        return x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR')