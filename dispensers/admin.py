from django.contrib import admin
from .models import Dispenser, DispenserProduct

class DispenserProductInline(admin.TabularInline):
    model = DispenserProduct
    extra = 0
    readonly_fields = ('created_at', 'updated_at')
    fields = ('row_number', 'product', 'current_inventory', 'max_capacity')

@admin.register(Dispenser)
class DispenserAdmin(admin.ModelAdmin):
    list_display = ('location_name', 'ble_beacon_id', 'install_date', 'created_at')
    list_filter = ('install_date',)
    search_fields = ('location_name', 'ble_beacon_id')
    readonly_fields = ('install_date', 'created_at', 'updated_at')
    inlines = [DispenserProductInline]

@admin.register(DispenserProduct)
class DispenserProductAdmin(admin.ModelAdmin):
    list_display = ('dispenser', 'row_number', 'product', 'current_inventory', 'max_capacity')
    list_filter = ('dispenser', 'row_number')
    search_fields = ('dispenser__location_name', 'product__product_name')
    readonly_fields = ('created_at', 'updated_at')