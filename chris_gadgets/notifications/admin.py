"""
Notifications Admin Configuration
"""
from django.contrib import admin
from .models import Notification, NotificationPreference, NotificationTemplate, BulkNotification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Notification Admin"""
    
    list_display = [
        'user', 'notification_type', 'title',
        'is_read', 'priority', 'created_at'
    ]
    list_filter = [
        'notification_type', 'is_read', 'priority',
        'send_email', 'send_sms', 'send_push', 'created_at'
    ]
    search_fields = ['user__email', 'title', 'message']
    raw_id_fields = ['user']
    date_hierarchy = 'created_at'
    
    readonly_fields = ['created_at', 'sent_at', 'read_at']


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    """Notification Preference Admin"""
    
    list_display = ['user', 'updated_at']
    search_fields = ['user__email', 'user__first_name', 'user__last_name']
    raw_id_fields = ['user']
    
    fieldsets = (
        ('Email Preferences', {
            'fields': (
                'email_order_updates', 'email_payment_updates',
                'email_promotions', 'email_product_updates',
                'email_messages', 'email_reviews', 'email_wishlist',
                'email_cart_reminders'
            )
        }),
        ('SMS Preferences', {
            'fields': (
                'sms_order_updates', 'sms_payment_updates',
                'sms_promotions', 'sms_delivery_updates'
            )
        }),
        ('Push Preferences', {
            'fields': (
                'push_order_updates', 'push_payment_updates',
                'push_promotions', 'push_messages', 'push_reviews',
                'push_wishlist', 'push_cart_reminders'
            )
        }),
        ('Quiet Hours', {
            'fields': (
                'quiet_hours_enabled', 'quiet_hours_start', 'quiet_hours_end'
            )
        }),
    )


@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    """Notification Template Admin"""
    
    list_display = ['name', 'template_type', 'is_active', 'updated_at']
    list_filter = ['template_type', 'is_active']
    search_fields = ['name', 'subject', 'content']
    
    fieldsets = (
        (None, {
            'fields': ('name', 'template_type', 'is_active')
        }),
        ('Content', {
            'fields': ('subject', 'content')
        }),
        ('Variables', {
            'fields': ('variables',),
            'description': 'List of variables available in this template'
        }),
    )


@admin.register(BulkNotification)
class BulkNotificationAdmin(admin.ModelAdmin):
    """Bulk Notification Admin"""
    
    list_display = [
        'title', 'notification_type', 'status',
        'recipients_count', 'sent_count', 'scheduled_at'
    ]
    list_filter = ['status', 'notification_type', 'send_as_email', 'send_as_sms']
    search_fields = ['title', 'message']
    filter_horizontal = ['target_specific_users']
    date_hierarchy = 'scheduled_at'
    
    readonly_fields = [
        'recipients_count', 'sent_count', 'failed_count',
        'sent_at', 'created_at', 'updated_at'
    ]
    
    actions = ['send_notifications']
    
    def send_notifications(self, request, queryset):
        from django.utils import timezone
        for notification in queryset.filter(status='draft'):
            notification.status = 'sending'
            notification.sent_at = timezone.now()
            notification.save()
            # Actual sending logic would be handled by a background task
    send_notifications.short_description = 'Send selected notifications'
