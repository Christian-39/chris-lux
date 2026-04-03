"""
Core Models - Site Settings, SEO, Analytics
"""
from django.db import models
from django.core.validators import URLValidator
from django.conf import settings
import uuid


class SiteSetting(models.Model):
    """Site-wide Settings Model"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Basic Info
    site_name = models.CharField(max_length=100, default='Gadgets Store')
    site_tagline = models.CharField(
        max_length=255,
        default='Your One-Stop Shop for Gadgets & Accessories'
    )
    site_description = models.TextField(
        blank=True,
        null=True,
        help_text="Short description for SEO"
    )
    
    # Contact Info
    contact_email = models.EmailField(default='support@gadgetsstore.com')
    contact_phone = models.CharField(max_length=17, default='+2348012345678')
    contact_phone_secondary = models.CharField(
        max_length=17,
        blank=True,
        null=True
    )
    whatsapp_number = models.CharField(max_length=17, default='+2348012345678')
    
    # Address
    business_address = models.TextField(blank=True, null=True)
    business_hours = models.CharField(
        max_length=255,
        default='Mon - Sat: 9:00 AM - 6:00 PM'
    )
    
    # Social Media
    facebook_url = models.URLField(blank=True, null=True)
    twitter_url = models.URLField(blank=True, null=True)
    instagram_url = models.URLField(blank=True, null=True)
    youtube_url = models.URLField(blank=True, null=True)
    linkedin_url = models.URLField(blank=True, null=True)
    
    # Currency
    default_currency = models.CharField(max_length=10, default='₦')
    currency_code = models.CharField(max_length=10, default='NGN')
    currency_position = models.CharField(
        max_length=10,
        choices=[('before', 'Before Amount'), ('after', 'After Amount')],
        default='before'
    )
    
    # Shipping & Tax
    free_shipping_threshold = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=50000
    )
    flat_shipping_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=2000
    )
    tax_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Tax rate as percentage"
    )
    
    # Logo & Favicon
    logo = models.ImageField(upload_to='site/', blank=True, null=True)
    logo_dark = models.ImageField(
        upload_to='site/',
        blank=True,
        null=True,
        help_text="Logo for dark mode"
    )
    favicon = models.ImageField(upload_to='site/', blank=True, null=True)
    
    # Theme Colors
    primary_color = models.CharField(max_length=7, default='#2563eb')
    secondary_color = models.CharField(max_length=7, default='#1e40af')
    accent_color = models.CharField(max_length=7, default='#f59e0b')
    
    # Features
    enable_reviews = models.BooleanField(default=True)
    enable_wishlist = models.BooleanField(default=True)
    enable_compare = models.BooleanField(default=True)
    enable_guest_checkout = models.BooleanField(default=True)
    enable_newsletter = models.BooleanField(default=True)
    enable_live_chat = models.BooleanField(default=True)
    enable_whatsapp = models.BooleanField(default=True)
    
    # Maintenance
    maintenance_mode = models.BooleanField(default=False)
    maintenance_message = models.TextField(
        blank=True,
        null=True,
        default="We're currently performing maintenance. Please check back soon."
    )
    
    # Analytics
    google_analytics_id = models.CharField(max_length=50, blank=True, null=True)
    facebook_pixel_id = models.CharField(max_length=50, blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Site Setting'
        verbose_name_plural = 'Site Settings'
    
    def __str__(self):
        return 'Site Settings'
    
    def save(self, *args, **kwargs):
        # Ensure only one instance exists
        if not self.pk and SiteSetting.objects.exists():
            # Update existing instance
            existing = SiteSetting.objects.first()
            self.pk = existing.pk
        super().save(*args, **kwargs)
    
    @classmethod
    def get_settings(cls):
        """Get or create site settings"""
        settings, created = cls.objects.get_or_create(pk=1)
        return settings


class SEOSetting(models.Model):
    """SEO Settings for Pages"""
    
    PAGE_CHOICES = [
        ('home', 'Home Page'),
        ('products', 'Products Page'),
        ('about', 'About Page'),
        ('contact', 'Contact Page'),
        ('faq', 'FAQ Page'),
        ('terms', 'Terms & Conditions'),
        ('privacy', 'Privacy Policy'),
        ('shipping', 'Shipping Info'),
        ('returns', 'Returns Policy'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    page = models.CharField(max_length=50, choices=PAGE_CHOICES, unique=True)
    title = models.CharField(max_length=255)
    description = models.TextField()
    keywords = models.CharField(max_length=500, blank=True, null=True)
    og_image = models.ImageField(upload_to='seo/', blank=True, null=True)
    canonical_url = models.URLField(blank=True, null=True)
    robots_meta = models.CharField(
        max_length=100,
        default='index, follow',
        help_text="e.g., 'index, follow' or 'noindex, nofollow'"
    )
    structured_data = models.JSONField(
        default=dict,
        blank=True,
        help_text="JSON-LD structured data"
    )
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'SEO Setting'
        verbose_name_plural = 'SEO Settings'
    
    def __str__(self):
        return f"{self.get_page_display()} SEO"


class Banner(models.Model):
    """Homepage Banners/Promo Banners"""
    
    POSITION_CHOICES = [
        ('hero', 'Hero Banner'),
        ('top', 'Top Bar'),
        ('middle', 'Middle Section'),
        ('bottom', 'Bottom Section'),
        ('sidebar', 'Sidebar'),
        ('popup', 'Popup'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    subtitle = models.CharField(max_length=500, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    
    # Media
    image = models.ImageField(upload_to='banners/')
    image_mobile = models.ImageField(
        upload_to='banners/',
        blank=True,
        null=True,
        help_text="Mobile version of banner"
    )
    
    # Link
    link = models.URLField(blank=True, null=True)
    link_text = models.CharField(max_length=100, default='Shop Now')
    open_in_new_tab = models.BooleanField(default=False)
    
    # Position & Display
    position = models.CharField(
        max_length=20,
        choices=POSITION_CHOICES,
        default='hero'
    )
    display_order = models.PositiveIntegerField(default=0)
    
    # Styling
    background_color = models.CharField(max_length=7, blank=True, null=True)
    text_color = models.CharField(max_length=7, blank=True, null=True)
    button_color = models.CharField(max_length=7, blank=True, null=True)
    
    # Schedule
    starts_at = models.DateTimeField(blank=True, null=True)
    ends_at = models.DateTimeField(blank=True, null=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Tracking
    view_count = models.PositiveIntegerField(default=0)
    click_count = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['position', 'display_order', '-created_at']
    
    def __str__(self):
        return self.title
    
    @property
    def click_through_rate(self):
        """Calculate click-through rate"""
        if self.view_count > 0:
            return (self.click_count / self.view_count) * 100
        return 0


class Testimonial(models.Model):
    """Customer Testimonials"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer_name = models.CharField(max_length=255)
    customer_title = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="e.g., 'Verified Buyer' or 'Loyal Customer'"
    )
    customer_image = models.ImageField(
        upload_to='testimonials/',
        blank=True,
        null=True
    )
    rating = models.PositiveSmallIntegerField(
        choices=[(i, i) for i in range(1, 6)],
        default=5
    )
    content = models.TextField()
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-is_featured', 'display_order', '-created_at']
    
    def __str__(self):
        return f"{self.customer_name} - {self.rating}★"


class TrustBadge(models.Model):
    """Trust Badges for Footer/Checkout"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=100)
    description = models.CharField(max_length=255)
    icon = models.CharField(
        max_length=50,
        help_text="FontAwesome icon class"
    )
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['display_order']
    
    def __str__(self):
        return self.title


class PageContent(models.Model):
    """Dynamic Page Content"""
    
    PAGE_CHOICES = [
        ('about', 'About Us'),
        ('terms', 'Terms & Conditions'),
        ('privacy', 'Privacy Policy'),
        ('shipping', 'Shipping Information'),
        ('returns', 'Returns & Refunds'),
        ('faq', 'FAQ'),
        ('careers', 'Careers'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    page = models.CharField(max_length=50, choices=PAGE_CHOICES, unique=True)
    title = models.CharField(max_length=255)
    content = models.TextField()
    last_updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True
    )
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['page']
    
    def __str__(self):
        return self.title


class ActivityLog(models.Model):
    """System Activity Log"""
    
    ACTION_CHOICES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('export', 'Export'),
        ('import', 'Import'),
        ('other', 'Other'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    model_name = models.CharField(max_length=100, blank=True, null=True)
    object_id = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField()
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.action} - {self.model_name or 'System'}"


class NewsletterSubscriber(models.Model):
    """Newsletter Subscribers"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)
    unsubscribed_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        ordering = ['-subscribed_at']
    
    def __str__(self):
        return self.email
