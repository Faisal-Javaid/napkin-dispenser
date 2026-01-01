from django.db import models
import uuid

class Log(models.Model):
    class Level(models.TextChoices):
        INFO = 'info', 'Info'
        WARN = 'warn', 'Warning'
        ERROR = 'error', 'Error'
        DEBUG = 'debug', 'Debug'
        SECURITY = 'security', 'Security'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    level = models.CharField(max_length=20, choices=Level.choices, default=Level.INFO)
    action = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    user = models.ForeignKey('users.User', on_delete=models.SET_NULL, 
                           null=True, blank=True, related_name='logs')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    request_method = models.CharField(max_length=10, null=True, blank=True)
    request_url = models.TextField(null=True, blank=True)
    request_body = models.JSONField(null=True, blank=True)
    response_status = models.IntegerField(null=True, blank=True)
    response_body = models.JSONField(null=True, blank=True)
    error_message = models.TextField(null=True, blank=True)
    error_stack = models.TextField(null=True, blank=True)
    metadata = models.JSONField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['level']),
            models.Index(fields=['action']),
            models.Index(fields=['timestamp']),
            models.Index(fields=['user', 'timestamp']),
        ]
    
    def __str__(self):
        return f'[{self.level}] {self.action} - {self.timestamp}'