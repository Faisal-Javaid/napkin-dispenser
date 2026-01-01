from django.contrib import admin
from .models import Log

@admin.register(Log)
class LogAdmin(admin.ModelAdmin):
    list_display = ('action', 'level', 'user', 'ip_address', 'timestamp')
    list_filter = ('level', 'action', 'timestamp')
    search_fields = ('action', 'description', 'user__phone_number', 'ip_address')
    readonly_fields = ('timestamp',)
    date_hierarchy = 'timestamp'