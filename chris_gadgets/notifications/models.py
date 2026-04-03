"""
Notifications Models - User Notifications System
"""
from django.db import models
from django.conf import settings
import uuid


class Notification(models.Model):
    """User Notification Model"""
    
    # Notification Types
    TYPE_CHOICES = [
        ('order', 'Order Update'),
        ('payment', 'Payment Update'),
        ('product', 'Product Update'),
        ('promotion', 'Promotion'),
        ('message', 'Message'),
        ('system', 'System'),
        ('review', 'Review'),
        ('wishlist', 'Wishlist'),
        ('cart', 'Cart'),
    ]
    
    # Priority Levels
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    
    # Notification Content
    notification_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default='system'
    )
    title = models.CharField(max_length=255)
    message = models.TextField()
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='medium'
    )
    
    # Linking
    link = models.URLField(blank=True, null=True)
    link_text = models.CharField(max_length=100, blank=True, null=True)
    related_object_id = models.CharField(max_length=100, blank=True, null=True)
    related_object_type = models.CharField(max_length=50, blank=True, null=True)
    
    # Status
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(blank=True, null=True)
    is_sent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(blank=True, null=True)
    
    # Delivery Methods
    send_email = models.BooleanField(default=False)
    send_sms = models.BooleanField(default=False)
    send_push = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Notifications'
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.title}"
    
    def mark_as_read(self):
        """Mark notification as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = models.DateTimeField().auto_now
            self.save(update_fields=['is_read', 'read_at'])
    
    @property
    def icon_class(self):
        """Get icon class based on notification type"""
        icons = {
            'order': 'shopping-bag',
            'payment': 'credit-card',
            'product': 'box',
            'promotion': 'tag',
            'message': 'message-circle',
            'system': 'bell',
            'review': 'star',
            'wishlist': 'heart',
            'cart': 'shopping-cart',
        }
        return icons.get(self.notification_type, 'bell')
    
    @property
    def priority_class(self):
        """Get CSS class based on priority"""
        classes = {
            'low': 'secondary',
            'medium': 'info',
            'high': 'warning',
            'urgent': 'danger',
        }
        return classes.get(self.priority, 'info')


class NotificationPreference(models.Model):
    """User Notification Preferences"""
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notification_preferences'
    )
    
    # Email Preferences
    email_order_updates = models.BooleanField(default=True)
    email_payment_updates = models.BooleanField(default=True)
    email_promotions = models.BooleanField(default=True)
    email_product_updates = models.BooleanField(default=False)
    email_messages = models.BooleanField(default=True)
    email_reviews = models.BooleanField(default=True)
    email_wishlist = models.BooleanField(default=True)
    email_cart_reminders = models.BooleanField(default=True)
    
    # SMS Preferences
    sms_order_updates = models.BooleanField(default=True)
    sms_payment_updates = models.BooleanField(default=True)
    sms_promotions = models.BooleanField(default=False)
    sms_delivery_updates = models.BooleanField(default=True)
    
    # Push Preferences
    push_order_updates = models.BooleanField(default=True)
    push_payment_updates = models.BooleanField(default=True)
    push_promotions = models.BooleanField(default=True)
    push_messages = models.BooleanField(default=True)
    push_reviews = models.BooleanField(default=True)
    push_wishlist = models.BooleanField(default=True)
    push_cart_reminders = models.BooleanField(default=True)
    
    # Quiet Hours
    quiet_hours_enabled = models.BooleanField(default=False)
    quiet_hours_start = models.TimeField(blank=True, null=True)
    quiet_hours_end = models.TimeField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = 'Notification Preferences'
    
    def __str__(self):
        return f"{self.user.get_full_name()} - Preferences"


class NotificationTemplate(models.Model):
    """Notification Templates for Admin"""
    
    TEMPLATE_TYPE_CHOICES = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('push', 'Push Notification'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    template_type = models.CharField(
        max_length=20,
        choices=TEMPLATE_TYPE_CHOICES
    )
    subject = models.CharField(max_length=255, blank=True, null=True)
    content = models.TextField()
    variables = models.JSONField(
        default=list,
        help_text="List of available variables for this template"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.template_type})"


class BulkNotification(models.Model):
    """Bulk Notifications sent by Admin"""
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sending', 'Sending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    message = models.TextField()
    notification_type = models.CharField(
        max_length=20,
        choices=Notification.TYPE_CHOICES,
        default='system'
    )
    
    # Target Audience
    target_all_users = models.BooleanField(default=False)
    target_user_types = models.JSONField(default=list, blank=True)
    target_specific_users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name='bulk_notifications'
    )
    
    # Delivery Methods
    send_as_email = models.BooleanField(default=False)
    send_as_sms = models.BooleanField(default=False)
    send_as_notification = models.BooleanField(default=True)
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )
    recipients_count = models.PositiveIntegerField(default=0)
    sent_count = models.PositiveIntegerField(default=0)
    failed_count = models.PositiveIntegerField(default=0)
    
    # Scheduling
    scheduled_at = models.DateTimeField(blank=True, null=True)
    sent_at = models.DateTimeField(blank=True, null=True)
    
    # Creator
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='created_bulk_notifications'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} ({self.status})"
