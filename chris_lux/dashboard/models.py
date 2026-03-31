"""
Dashboard models for Chris-Lux.
"""
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class ActivityLog(models.Model):
    """Activity log for admin actions."""
    
    ACTION_TYPES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('view', 'View'),
        ('export', 'Export'),
        ('other', 'Other'),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='activity_logs'
    )
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES)
    description = models.TextField()
    model_name = models.CharField(max_length=100, blank=True)
    object_id = models.CharField(max_length=100, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'action_type']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.action_type} - {self.created_at}"


class DashboardWidget(models.Model):
    """Customizable dashboard widgets."""
    
    WIDGET_TYPES = [
        ('sales_chart', 'Sales Chart'),
        ('orders_summary', 'Orders Summary'),
        ('recent_orders', 'Recent Orders'),
        ('low_stock', 'Low Stock Alert'),
        ('top_products', 'Top Products'),
        ('customer_stats', 'Customer Statistics'),
        ('revenue_stats', 'Revenue Statistics'),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='dashboard_widgets'
    )
    widget_type = models.CharField(max_length=50, choices=WIDGET_TYPES)
    title = models.CharField(max_length=100)
    position = models.PositiveIntegerField(default=0)
    is_visible = models.BooleanField(default=True)
    settings = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['position', 'created_at']
    
    def __str__(self):
        return f"{self.title} - {self.user.username}"
