from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Wallet

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('phone_number', 'email', 'user_type', 'account_type','subscription_type',
                    'subscription_end_date',
                    'account_verified', 'is_active', 'created_at')
    list_filter = ('user_type', 'account_type', 'account_verified','subscription_type', 'is_active')
    search_fields = ('phone_number', 'email')
    ordering = ('-created_at',)

    fieldsets = (
        (None, {'fields': ('phone_number', 'password')}),
        ('Personal Info', {'fields': ('email',)}),
        ('Account Info', {'fields': ('user_type', 'account_type',
                                    'subscription_type',
                                    'subscription_start_date', 'subscription_end_date',
                                    'account_verified')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser',
                                   'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'created_at', 'updated_at')}),
    )

    readonly_fields = ('created_at', 'updated_at')
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone_number', 'email', 'password1', 'password2',
                      'user_type', 'account_type','subscription_type', 'account_verified'),
        }),
    )

@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ('user', 'balance', 'subscription_end_date', 'created_at')
    list_filter = ('subscription_end_date',)
    search_fields = ('user__phone_number', 'user__email')
    readonly_fields = ('created_at', 'updated_at')