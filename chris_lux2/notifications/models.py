"""
Notification models for Chris-Lux.
"""
from django.db import models
from django.urls import reverse
from django.utils import timezone


class Notification(models.Model):
    """Notification model for user notifications."""
    
    NOTIFICATION_TYPES = [
        ('order', 'Order'),
        ('payment', 'Payment'),
        ('shipping', 'Shipping'),
        ('promotion', 'Promotion'),
        ('system', 'System'),
    ]
    
    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    notification_type = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TYPES
    )
    
    # Content
    title = models.CharField(max_length=255)
    message = models.TextField()
    
    # Related objects
    order = models.ForeignKey(
        'orders.Order',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications'
    )
    
    # Status
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['user', 'notification_type']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.user.username}"
    
    def mark_as_read(self):
        """Mark notification as read."""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])
    
    def mark_as_unread(self):
        """Mark notification as unread."""
        if self.is_read:
            self.is_read = False
            self.read_at = None
            self.save(update_fields=['is_read', 'read_at'])
    
    @property
    def icon_class(self):
        """Get icon class based on notification type."""
        icons = {
            'order': 'shopping-bag',
            'payment': 'credit-card',
            'shipping': 'truck',
            'promotion': 'tag',
            'system': 'info',
        }
        return icons.get(self.notification_type, 'bell')
    
    @property
    def color_class(self):
        """Get color class based on notification type."""
        colors = {
            'order': 'primary',
            'payment': 'success',
            'shipping': 'info',
            'promotion': 'warning',
            'system': 'secondary',
        }
        return colors.get(self.notification_type, 'secondary')


class NotificationPreference(models.Model):
    """User notification preferences."""
    
    user = models.OneToOneField(
        'users.User',
        on_delete=models.CASCADE,
        related_name='notification_preferences'
    )
    
    # Email notifications
    email_order_updates = models.BooleanField(default=True)
    email_payment_updates = models.BooleanField(default=True)
    email_shipping_updates = models.BooleanField(default=True)
    email_promotions = models.BooleanField(default=True)
    email_newsletter = models.BooleanField(default=True)
    
    # SMS notifications
    sms_order_updates = models.BooleanField(default=False)
    sms_payment_updates = models.BooleanField(default=False)
    sms_shipping_updates = models.BooleanField(default=False)
    
    # In-app notifications
    app_order_updates = models.BooleanField(default=True)
    app_payment_updates = models.BooleanField(default=True)
    app_shipping_updates = models.BooleanField(default=True)
    app_promotions = models.BooleanField(default=True)
    
    # Frequency
    FREQUENCY_CHOICES = [
        ('immediate', 'Immediate'),
        ('daily', 'Daily Digest'),
        ('weekly', 'Weekly Digest'),
    ]
    email_frequency = models.CharField(
        max_length=20,
        choices=FREQUENCY_CHOICES,
        default='immediate'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = 'Notification preferences'
    
    def __str__(self):
        return f"Notification preferences for {self.user.username}"
