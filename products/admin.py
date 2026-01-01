from django.contrib import admin
from .models import Product

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('product_name', 'credit_cost', 'is_active', 'created_at')
    list_filter = ('is_active', 'credit_cost')
    search_fields = ('product_name',)
    readonly_fields = ('created_at', 'updated_at')