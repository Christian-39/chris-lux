"""
Core models for Chris Lux.
"""

from django.db import models
from django.urls import reverse


class NewsletterSubscriber(models.Model):
    """Newsletter subscription model."""
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Newsletter Subscriber'
        verbose_name_plural = 'Newsletter Subscribers'
        ordering = ['-subscribed_at']
    
    def __str__(self):
        return self.email


class ContactMessage(models.Model):
    """Contact form messages."""
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = 'Contact Message'
        verbose_name_plural = 'Contact Messages'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.subject}"


class Testimonial(models.Model):
    """Customer testimonials."""
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=100, blank=True)
    image = models.ImageField(upload_to='testimonials/', blank=True, null=True)
    content = models.TextField()
    rating = models.PositiveSmallIntegerField(default=5)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Testimonial'
        verbose_name_plural = 'Testimonials'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.rating} stars"


class FAQ(models.Model):
    """Frequently Asked Questions."""
    question = models.CharField(max_length=300)
    answer = models.TextField()
    category = models.CharField(max_length=50, default='General')
    order = models.PositiveSmallIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'FAQ'
        verbose_name_plural = 'FAQs'
        ordering = ['order', 'category']
    
    def __str__(self):
        return self.question


class Coupon(models.Model):
    """Discount coupons."""
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    discount_type = models.CharField(
        max_length=10,
        choices=[
            ('percentage', 'Percentage'),
            ('fixed', 'Fixed Amount'),
        ],
        default='percentage'
    )
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    minimum_order = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    usage_limit = models.PositiveIntegerField(default=0)  # 0 = unlimited
    usage_count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Coupon'
        verbose_name_plural = 'Coupons'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.code
    
    def is_valid(self):
        from django.utils import timezone
        now = timezone.now()
        if not self.is_active:
            return False
        if now < self.valid_from or now > self.valid_until:
            return False
        if self.usage_limit > 0 and self.usage_count >= self.usage_limit:
            return False
        return True
