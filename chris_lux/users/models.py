"""
User models for Chris-Lux.
"""
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    """Custom User model with additional fields."""
    
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    profile_image = models.ImageField(
        upload_to='profiles/',
        blank=True,
        null=True,
        default='profiles/default-avatar.png'
    )
    bio = models.TextField(blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    
    # Address fields
    address = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    
    # Preferences
    dark_mode = models.BooleanField(default=False)
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=False)
    
    # User type
    is_admin = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Required fields
    REQUIRED_FIELDS = ['email', 'first_name', 'last_name']
    
    class Meta:
        ordering = ['-date_joined']
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.username})"
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.username
    
    def get_short_name(self):
        return self.first_name or self.username
    
    @property
    def orders_count(self):
        return self.orders.count()
    
    @property
    def total_spent(self):
        from orders.models import Order
        total = Order.objects.filter(
            user=self,
            status__in=['delivered', 'verified']
        ).aggregate(
            total=models.Sum('total_amount')
        )['total']
        return total or 0
