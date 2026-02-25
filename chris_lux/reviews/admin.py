"""
Reviews admin configuration.
"""

from django.contrib import admin
from .models import Review, ReviewImage, ReviewHelpful


class ReviewImageInline(admin.TabularInline):
    """Review image inline."""
    model = ReviewImage
    extra = 1


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['product', 'user', 'rating', 'is_approved', 'is_verified_purchase', 'helpful_count', 'created_at']
    list_filter = ['rating', 'is_approved', 'is_verified_purchase', 'created_at']
    search_fields = ['product__name', 'user__email', 'content']
    list_editable = ['is_approved']
    inlines = [ReviewImageInline]
    actions = ['approve_reviews', 'unapprove_reviews']
    
    def approve_reviews(self, request, queryset):
        queryset.update(is_approved=True)
    approve_reviews.short_description = "Approve selected reviews"
    
    def unapprove_reviews(self, request, queryset):
        queryset.update(is_approved=False)
    unapprove_reviews.short_description = "Unapprove selected reviews"


@admin.register(ReviewImage)
class ReviewImageAdmin(admin.ModelAdmin):
    list_display = ['review', 'created_at']
    list_filter = ['created_at']
    search_fields = ['review__product__name']


@admin.register(ReviewHelpful)
class ReviewHelpfulAdmin(admin.ModelAdmin):
    list_display = ['review', 'user', 'created_at']
    list_filter = ['created_at']
    search_fields = ['review__product__name', 'user__email']
