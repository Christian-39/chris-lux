"""
Core models for Chris-Lux.
"""
from django.db import models


class Banner(models.Model):
    """Homepage banner model."""
    
    title = models.CharField(max_length=255)
    subtitle = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='banners/')
    link = models.URLField(blank=True)
    link_text = models.CharField(max_length=100, default='Shop Now')
    
    # Display settings
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['display_order', '-created_at']
    
    def __str__(self):
        return self.title


class Testimonial(models.Model):
    """Customer testimonial model."""
    
    name = models.CharField(max_length=255)
    title = models.CharField(max_length=255, blank=True)
    image = models.ImageField(upload_to='testimonials/', blank=True, null=True)
    content = models.TextField()
    rating = models.PositiveSmallIntegerField(
        choices=[(i, i) for i in range(1, 6)],
        default=5
    )
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['display_order', '-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.rating} stars"


class FAQ(models.Model):
    """Frequently asked questions model."""
    
    question = models.CharField(max_length=500)
    answer = models.TextField()
    category = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'FAQ'
        verbose_name_plural = 'FAQs'
        ordering = ['display_order', '-created_at']
    
    def __str__(self):
        return self.question[:100]


class ContactMessage(models.Model):
    """Contact form messages model."""
    
    name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    subject = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.subject}"


class NewsletterSubscriber(models.Model):
    """Newsletter subscribers model."""
    
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-subscribed_at']
    
    def __str__(self):
        return self.email
