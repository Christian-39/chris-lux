"""
Core admin configuration.
"""

from django.contrib import admin
from .models import NewsletterSubscriber, ContactMessage, Testimonial, FAQ, Coupon


@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ['email', 'is_active', 'subscribed_at']
    list_filter = ['is_active', 'subscribed_at']
    search_fields = ['email']
    actions = ['activate', 'deactivate']
    
    def activate(self, request, queryset):
        queryset.update(is_active=True)
    activate.short_description = "Activate selected subscribers"
    
    def deactivate(self, request, queryset):
        queryset.update(is_active=False)
    deactivate.short_description = "Deactivate selected subscribers"


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'subject', 'created_at', 'is_read']
    list_filter = ['is_read', 'created_at']
    search_fields = ['name', 'email', 'subject', 'message']
    readonly_fields = ['name', 'email', 'subject', 'message', 'created_at']
    
    def has_add_permission(self, request):
        return False


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ['name', 'location', 'rating', 'is_active', 'created_at']
    list_filter = ['is_active', 'rating', 'created_at']
    search_fields = ['name', 'content']
    list_editable = ['is_active']


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ['question', 'category', 'order', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['question', 'answer']
    list_editable = ['order', 'is_active']


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ['code', 'discount_type', 'discount_value', 'valid_from', 'valid_until', 'is_active']
    list_filter = ['discount_type', 'is_active', 'valid_from']
    search_fields = ['code', 'description']
    readonly_fields = ['usage_count', 'created_at']
    fieldsets = (
        (None, {
            'fields': ('code', 'description', 'is_active')
        }),
        ('Discount Details', {
            'fields': ('discount_type', 'discount_value', 'minimum_order')
        }),
        ('Validity', {
            'fields': ('valid_from', 'valid_until', 'usage_limit', 'usage_count')
        }),
    )
