"""
Admin configuration for notifications app.
"""
from django.contrib import admin
from .models import Notification, NotificationPreference


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Admin for Notification model."""
    
    list_display = [
        'title', 'user', 'notification_type', 'is_read',
        'created_at'
    ]
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['title', 'message', 'user__username']
    list_editable = ['is_read']
    readonly_fields = ['created_at', 'read_at']


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    """Admin for NotificationPreference model."""
    
    list_display = ['user', 'email_frequency', 'updated_at']
    search_fields = ['user__username']
