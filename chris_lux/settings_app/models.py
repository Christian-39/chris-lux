"""
Settings models for Chris-Lux.
"""
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class SiteSettings(models.Model):
    """Site-wide settings model."""
    
    # Basic Info
    site_name = models.CharField(max_length=255, default='Chris-Lux')
    site_tagline = models.CharField(
        max_length=255,
        default='Premium Hair Extensions & Wigs'
    )
    site_description = models.TextField(
        blank=True,
        help_text='Meta description for SEO'
    )
    site_keywords = models.CharField(
        max_length=500,
        blank=True,
        help_text='Meta keywords for SEO (comma separated)'
    )
    
    # Branding
    logo = models.ImageField(
        upload_to='site/',
        blank=True,
        null=True,
        help_text='Site logo'
    )
    favicon = models.ImageField(
        upload_to='site/',
        blank=True,
        null=True,
        help_text='Site favicon'
    )
    
    # Contact
    contact_email = models.EmailField(default='support@chris-lux.com')
    support_phone = models.CharField(max_length=20, blank=True)
    whatsapp_number = models.CharField(max_length=20, blank=True)
    
    # Address
    business_address = models.TextField(blank=True)
    business_city = models.CharField(max_length=100, blank=True)
    business_country = models.CharField(max_length=100, blank=True)
    
    # Social Media
    facebook_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)
    youtube_url = models.URLField(blank=True)
    tiktok_url = models.URLField(blank=True)
    pinterest_url = models.URLField(blank=True)
    
    # Currency
    CURRENCY_CHOICES = [
        ('USD', 'US Dollar ($)'),
        ('EUR', 'Euro (€)'),
        ('GBP', 'British Pound (£)'),
        ('CAD', 'Canadian Dollar (C$)'),
        ('AUD', 'Australian Dollar (A$)'),
        ('NGN', 'Nigerian Naira (₦)'),
    ]
    currency = models.CharField(
        max_length=3,
        choices=CURRENCY_CHOICES,
        default='USD'
    )
    currency_symbol = models.CharField(max_length=10, default='$')
    
    # Tax
    tax_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text='Tax rate percentage'
    )
    
    # Shipping
    free_shipping_threshold = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text='Minimum order for free shipping (0 to disable)'
    )
    standard_shipping_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=15.00
    )
    express_shipping_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=25.00
    )
    overnight_shipping_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=50.00
    )
    
    # Order Settings
    order_prefix = models.CharField(max_length=10, default='CL')
    auto_cancel_hours = models.PositiveIntegerField(
        default=48,
        help_text='Hours after which pending orders are auto-cancelled'
    )
    
    # Notification Settings
    admin_notification_email = models.EmailField(
        blank=True,
        help_text='Email to receive admin notifications'
    )
    notify_on_new_order = models.BooleanField(default=True)
    notify_on_payment = models.BooleanField(default=True)
    notify_on_low_stock = models.BooleanField(default=True)
    low_stock_threshold = models.PositiveIntegerField(default=5)
    
    # Theme Settings
    primary_color = models.CharField(max_length=7, default='#6B21A8')
    secondary_color = models.CharField(max_length=7, default='#1F2937')
    accent_color = models.CharField(max_length=7, default='#F59E0B')
    
    # Maintenance
    maintenance_mode = models.BooleanField(default=False)
    maintenance_message = models.TextField(
        blank=True,
        default='We are currently performing maintenance. Please check back soon.'
    )
    
    # Analytics
    google_analytics_id = models.CharField(max_length=50, blank=True)
    facebook_pixel_id = models.CharField(max_length=50, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Site Settings'
        verbose_name_plural = 'Site Settings'
    
    def __str__(self):
        return 'Site Settings'
    
    def save(self, *args, **kwargs):
        # Ensure only one instance exists
        if not self.pk and SiteSettings.objects.exists():
            # Update existing instance
            existing = SiteSettings.objects.first()
            self.pk = existing.pk
        super().save(*args, **kwargs)
    
    @classmethod
    def get_settings(cls):
        """Get or create site settings."""
        settings = cls.objects.first()
        if not settings:
            settings = cls.objects.create()
        return settings


class BankDetails(models.Model):
    """Bank account details for payments."""
    
    bank_name = models.CharField(max_length=255)
    account_name = models.CharField(max_length=255)
    account_number = models.CharField(max_length=100)
    routing_number = models.CharField(max_length=100, blank=True)
    swift_code = models.CharField(max_length=50, blank=True)
    bank_address = models.TextField(blank=True)
    
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    display_order = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = 'Bank Details'
        ordering = ['display_order', 'bank_name']
    
    def __str__(self):
        return f"{self.bank_name} - {self.account_name}"
    
    def save(self, *args, **kwargs):
        if self.is_default:
            BankDetails.objects.filter(is_default=True).update(is_default=False)
        super().save(*args, **kwargs)


class OrderStatus(models.Model):
    """Custom order statuses."""
    
    name = models.CharField(max_length=50)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    color = models.CharField(
        max_length=7,
        default='#6B7280',
        help_text='Hex color code for status badge'
    )
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    display_order = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = 'Order Statuses'
        ordering = ['display_order', 'name']
    
    def __str__(self):
        return self.name


class EmailTemplate(models.Model):
    """Email templates for notifications."""
    
    TEMPLATE_TYPES = [
        ('order_confirmation', 'Order Confirmation'),
        ('payment_received', 'Payment Received'),
        ('payment_verified', 'Payment Verified'),
        ('order_shipped', 'Order Shipped'),
        ('order_delivered', 'Order Delivered'),
        ('order_cancelled', 'Order Cancelled'),
        ('welcome', 'Welcome Email'),
        ('password_reset', 'Password Reset'),
    ]
    
    name = models.CharField(max_length=100)
    template_type = models.CharField(
        max_length=50,
        choices=TEMPLATE_TYPES,
        unique=True
    )
    subject = models.CharField(max_length=255)
    body_html = models.TextField()
    body_text = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name
