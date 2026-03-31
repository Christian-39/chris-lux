"""
Admin configuration for dashboard app.
"""
from django.contrib import admin
from .models import ActivityLog, DashboardWidget


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    """Admin for ActivityLog model."""
    
    list_display = [
        'user', 'action_type', 'description',
        'model_name', 'ip_address', 'created_at'
    ]
    list_filter = ['action_type', 'created_at']
    search_fields = ['user__username', 'description', 'model_name']
    readonly_fields = ['created_at']


@admin.register(DashboardWidget)
class DashboardWidgetAdmin(admin.ModelAdmin):
    """Admin for DashboardWidget model."""
    
    list_display = ['title', 'user', 'widget_type', 'position', 'is_visible']
    list_filter = ['widget_type', 'is_visible']
    search_fields = ['title', 'user__username']
