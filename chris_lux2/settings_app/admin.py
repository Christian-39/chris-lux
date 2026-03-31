"""
Admin configuration for settings app.
"""
from django.contrib import admin
from .models import SiteSettings, BankDetails, OrderStatus, EmailTemplate


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    """Admin for SiteSettings model."""
    
    list_display = ['site_name', 'currency', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('site_name', 'site_tagline', 'site_description', 'site_keywords')
        }),
        ('Branding', {
            'fields': ('logo', 'favicon')
        }),
        ('Contact', {
            'fields': ('contact_email', 'support_phone', 'whatsapp_number')
        }),
        ('Address', {
            'fields': ('business_address', 'business_city', 'business_country')
        }),
        ('Social Media', {
            'fields': (
                'facebook_url', 'instagram_url', 'twitter_url',
                'youtube_url', 'tiktok_url', 'pinterest_url'
            ),
            'classes': ('collapse',)
        }),
        ('Currency & Tax', {
            'fields': ('currency', 'currency_symbol', 'tax_rate')
        }),
        ('Shipping', {
            'fields': (
                'free_shipping_threshold',
                'standard_shipping_cost',
                'express_shipping_cost',
                'overnight_shipping_cost'
            )
        }),
        ('Order Settings', {
            'fields': ('order_prefix', 'auto_cancel_hours')
        }),
        ('Notifications', {
            'fields': (
                'admin_notification_email',
                'notify_on_new_order',
                'notify_on_payment',
                'notify_on_low_stock',
                'low_stock_threshold'
            )
        }),
        ('Theme', {
            'fields': ('primary_color', 'secondary_color', 'accent_color')
        }),
        ('Maintenance', {
            'fields': ('maintenance_mode', 'maintenance_message')
        }),
        ('Analytics', {
            'fields': ('google_analytics_id', 'facebook_pixel_id'),
            'classes': ('collapse',)
        }),
    )


@admin.register(BankDetails)
class BankDetailsAdmin(admin.ModelAdmin):
    """Admin for BankDetails model."""
    
    list_display = [
        'bank_name', 'account_name', 'account_number',
        'is_active', 'is_default', 'display_order'
    ]
    list_editable = ['is_active', 'is_default', 'display_order']
    search_fields = ['bank_name', 'account_name', 'account_number']


@admin.register(OrderStatus)
class OrderStatusAdmin(admin.ModelAdmin):
    """Admin for OrderStatus model."""
    
    list_display = ['name', 'slug', 'color', 'is_active', 'display_order']
    list_editable = ['color', 'is_active', 'display_order']
    search_fields = ['name', 'slug']


@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    """Admin for EmailTemplate model."""
    
    list_display = ['name', 'template_type', 'subject', 'is_active', 'updated_at']
    list_editable = ['is_active']
    search_fields = ['name', 'subject']
