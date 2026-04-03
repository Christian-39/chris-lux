"""
Core Admin Configuration
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import (
    SiteSetting, SEOSetting, Banner, Testimonial,
    TrustBadge, PageContent, ActivityLog, NewsletterSubscriber
)


@admin.register(SiteSetting)
class SiteSettingAdmin(admin.ModelAdmin):
    """Site Setting Admin"""
    
    list_display = ['site_name', 'contact_email', 'contact_phone', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'site_name', 'site_tagline', 'site_description'
            )
        }),
        ('Contact Information', {
            'fields': (
                'contact_email', 'contact_phone', 'contact_phone_secondary',
                'whatsapp_number', 'business_address', 'business_hours'
            )
        }),
        ('Social Media', {
            'fields': (
                'facebook_url', 'twitter_url', 'instagram_url',
                'youtube_url', 'linkedin_url'
            )
        }),
        ('Currency Settings', {
            'fields': (
                'default_currency', 'currency_code', 'currency_position'
            )
        }),
        ('Shipping & Tax', {
            'fields': (
                'free_shipping_threshold', 'flat_shipping_rate', 'tax_rate'
            )
        }),
        ('Logo & Branding', {
            'fields': ('logo', 'logo_dark', 'favicon')
        }),
        ('Theme Colors', {
            'fields': ('primary_color', 'secondary_color', 'accent_color')
        }),
        ('Features', {
            'fields': (
                'enable_reviews', 'enable_wishlist', 'enable_compare',
                'enable_guest_checkout', 'enable_newsletter',
                'enable_live_chat', 'enable_whatsapp'
            )
        }),
        ('Maintenance', {
            'fields': ('maintenance_mode', 'maintenance_message')
        }),
        ('Analytics', {
            'fields': ('google_analytics_id', 'facebook_pixel_id')
        }),
    )
    
    def has_add_permission(self, request):
        # Only allow one instance
        if self.model.objects.exists():
            return False
        return super().has_add_permission(request)


@admin.register(SEOSetting)
class SEOSettingAdmin(admin.ModelAdmin):
    """SEO Setting Admin"""
    
    list_display = ['page', 'title', 'updated_at']
    list_filter = ['page']
    search_fields = ['title', 'description', 'keywords']


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    """Banner Admin"""
    
    list_display = [
        'title', 'position', 'is_active',
        'display_order', 'view_count', 'click_count', 'click_through_rate'
    ]
    list_filter = ['position', 'is_active']
    search_fields = ['title', 'subtitle', 'description']
    list_editable = ['display_order', 'is_active']
    date_hierarchy = 'created_at'
    
    def click_through_rate(self, obj):
        return f"{obj.click_through_rate:.2f}%"
    click_through_rate.short_description = 'CTR'


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    """Testimonial Admin"""
    
    list_display = [
        'customer_name', 'rating', 'is_featured',
        'is_active', 'display_order', 'created_at'
    ]
    list_filter = ['rating', 'is_featured', 'is_active']
    search_fields = ['customer_name', 'content']
    list_editable = ['is_featured', 'is_active', 'display_order']


@admin.register(TrustBadge)
class TrustBadgeAdmin(admin.ModelAdmin):
    """Trust Badge Admin"""
    
    list_display = ['title', 'description', 'is_active', 'display_order']
    list_filter = ['is_active']
    search_fields = ['title', 'description']
    list_editable = ['is_active', 'display_order']


@admin.register(PageContent)
class PageContentAdmin(admin.ModelAdmin):
    """Page Content Admin"""
    
    list_display = ['page', 'title', 'updated_at']
    search_fields = ['title', 'content']


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    """Activity Log Admin"""
    
    list_display = [
        'action', 'model_name', 'user', 'description', 'created_at'
    ]
    list_filter = ['action', 'created_at']
    search_fields = ['description', 'user__email']
    date_hierarchy = 'created_at'
    readonly_fields = [
        'user', 'action', 'model_name', 'object_id',
        'description', 'ip_address', 'user_agent', 'created_at'
    ]
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    """Newsletter Subscriber Admin"""
    
    list_display = ['email', 'name', 'is_active', 'subscribed_at']
    list_filter = ['is_active', 'subscribed_at']
    search_fields = ['email', 'name']
    date_hierarchy = 'subscribed_at'
    actions = ['export_subscribers', 'deactivate_subscribers']
    
    def export_subscribers(self, request, queryset):
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="subscribers.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Email', 'Name', 'Subscribed At'])
        
        for subscriber in queryset:
            writer.writerow([
                subscriber.email,
                subscriber.name or '',
                subscriber.subscribed_at
            ])
        
        return response
    export_subscribers.short_description = 'Export selected subscribers'
    
    def deactivate_subscribers(self, request, queryset):
        from django.utils import timezone
        queryset.update(is_active=False, unsubscribed_at=timezone.now())
    deactivate_subscribers.short_description = 'Deactivate selected subscribers'
