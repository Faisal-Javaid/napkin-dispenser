from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta
from .models import Log
from .serializers import LogSerializer, LogStatsSerializer, ActionStatsSerializer
from users.permissions import IsAdmin

class LogViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = LogSerializer
    permission_classes = [IsAdmin]
    queryset = Log.objects.all().select_related('user').order_by('-timestamp')
    
    def get_queryset(self):
        queryset = Log.objects.all().select_related('user')
        
        # Apply filters
        level = self.request.query_params.get('level')
        if level:
            queryset = queryset.filter(level=level)
        
        action = self.request.query_params.get('action')
        if action:
            queryset = queryset.filter(action=action)
        
        user_id = self.request.query_params.get('user_id')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        start_date = self.request.query_params.get('start_date')
        if start_date:
            queryset = queryset.filter(timestamp__gte=start_date)
        
        end_date = self.request.query_params.get('end_date')
        if end_date:
            queryset = queryset.filter(timestamp__lte=end_date)
        
        return queryset.order_by('-timestamp')
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get log statistics"""
        # Level statistics
        level_stats = Log.objects.values('level').annotate(
            count=Count('id')
        ).order_by('level')
        
        # Top actions
        action_stats = Log.objects.values('action').annotate(
            count=Count('id')
        ).order_by('-count')[:10]
        
        # Recent activity
        last_24h = timezone.now() - timedelta(days=1)
        recent_stats = {
            'total_logs': Log.objects.count(),
            'last_24h': Log.objects.filter(timestamp__gte=last_24h).count(),
            'errors_last_24h': Log.objects.filter(
                timestamp__gte=last_24h,
                level=Log.Level.ERROR
            ).count(),
        }
        
        return Response({
            'levels': LogStatsSerializer(level_stats, many=True).data,
            'top_actions': ActionStatsSerializer(action_stats, many=True).data,
            'recent_activity': recent_stats
        })