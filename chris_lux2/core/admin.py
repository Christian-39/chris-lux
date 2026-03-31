"""
Admin configuration for core app.
"""
from django.contrib import admin
from .models import Banner, Testimonial, FAQ, ContactMessage, NewsletterSubscriber


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    """Admin for Banner model."""
    
    list_display = ['title', 'is_active', 'display_order', 'created_at']
    list_editable = ['is_active', 'display_order']
    search_fields = ['title', 'subtitle']


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    """Admin for Testimonial model."""
    
    list_display = ['name', 'title', 'rating', 'is_active', 'display_order']
    list_editable = ['is_active', 'display_order']
    search_fields = ['name', 'content']


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    """Admin for FAQ model."""
    
    list_display = ['question', 'category', 'is_active', 'display_order']
    list_editable = ['is_active', 'display_order']
    search_fields = ['question', 'answer']
    list_filter = ['category']


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    """Admin for ContactMessage model."""
    
    list_display = ['name', 'email', 'subject', 'is_read', 'created_at']
    list_filter = ['is_read', 'created_at']
    search_fields = ['name', 'email', 'subject', 'message']
    list_editable = ['is_read']
    readonly_fields = ['created_at']


@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    """Admin for NewsletterSubscriber model."""
    
    list_display = ['email', 'is_active', 'subscribed_at']
    list_filter = ['is_active', 'subscribed_at']
    search_fields = ['email']
    list_editable = ['is_active']
