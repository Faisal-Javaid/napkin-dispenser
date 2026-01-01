from rest_framework import serializers
from .models import Log

class LogSerializer(serializers.ModelSerializer):
    class Meta:
        model = Log
        fields = ['id', 'level', 'action', 'description', 'user_id',
                  'ip_address', 'user_agent', 'request_method', 'request_url',
                  'request_body', 'response_status', 'response_body',
                  'error_message', 'error_stack', 'metadata', 'timestamp']
        read_only_fields = fields

class LogStatsSerializer(serializers.Serializer):
    level = serializers.CharField()
    count = serializers.IntegerField()

class ActionStatsSerializer(serializers.Serializer):
    action = serializers.CharField()
    count = serializers.IntegerField()