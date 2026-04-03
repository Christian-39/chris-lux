"""
Products Admin Configuration
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Category, Brand, Product, ProductImage, ProductReview,
    Wishlist, RecentlyViewed, Coupon, FlashSale
)


class ProductImageInline(admin.TabularInline):
    """Product Image Inline"""
    model = ProductImage
    extra = 1
    fields = ['image', 'alt_text', 'is_primary', 'display_order']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Category Admin"""
    
    list_display = [
        'name', 'parent', 'product_count', 'is_active',
        'is_featured', 'display_order'
    ]
    list_filter = ['is_active', 'is_featured', 'parent']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['display_order', 'is_active', 'is_featured']


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    """Brand Admin"""
    
    list_display = [
        'name', 'product_count', 'is_active',
        'is_featured', 'logo_preview'
    ]
    list_filter = ['is_active', 'is_featured']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    
    def logo_preview(self, obj):
        if obj.logo:
            return format_html(
                '<img src="{}" style="width: 50px; height: 50px; object-fit: contain;" />',
                obj.logo.url
            )
        return '-'
    logo_preview.short_description = 'Logo'


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Product Admin"""
    
    list_display = [
        'name', 'sku', 'category', 'brand', 'price',
        'quantity', 'stock_status', 'is_active',
        'is_featured', 'created_at', 'image_preview'
    ]
    list_filter = [
        'is_active', 'is_featured', 'is_new_arrival', 'is_hot_deal',
        'stock_status', 'condition', 'category', 'brand'
    ]
    search_fields = ['name', 'sku', 'description']
    prepopulated_fields = {'slug': ('name',)}
    raw_id_fields = ['category', 'brand']
    inlines = [ProductImageInline]
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('sku', 'name', 'slug', 'category', 'brand')
        }),
        ('Pricing', {
            'fields': ('price', 'compare_at_price', 'cost_price')
        }),
        ('Inventory', {
            'fields': ('quantity', 'low_stock_threshold', 'stock_status', 'condition')
        }),
        ('Description', {
            'fields': ('short_description', 'description', 'key_highlights', 'specifications')
        }),
        ('Media', {
            'fields': ('video_url', 'video_file')
        }),
        ('Status', {
            'fields': ('is_active', 'is_featured', 'is_new_arrival', 'is_hot_deal')
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description', 'meta_keywords'),
            'classes': ('collapse',)
        }),
        ('Analytics', {
            'fields': ('view_count', 'sales_count', 'wishlist_count'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['view_count', 'sales_count', 'wishlist_count']
    
    def image_preview(self, obj):
        if obj.primary_image:
            return format_html(
                '<img src="{}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 4px;" />',
                obj.primary_image.image.url
            )
        return '-'
    image_preview.short_description = 'Image'


@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    """Product Review Admin"""
    
    list_display = [
        'product', 'user', 'rating', 'is_approved',
        'is_verified_purchase', 'helpful_count', 'created_at'
    ]
    list_filter = ['rating', 'is_approved', 'is_verified_purchase', 'created_at']
    search_fields = ['product__name', 'user__email', 'comment']
    raw_id_fields = ['product', 'user']
    list_editable = ['is_approved']
    actions = ['approve_reviews', 'reject_reviews']
    
    def approve_reviews(self, request, queryset):
        queryset.update(is_approved=True)
    approve_reviews.short_description = 'Approve selected reviews'
    
    def reject_reviews(self, request, queryset):
        queryset.update(is_approved=False)
    reject_reviews.short_description = 'Reject selected reviews'


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    """Wishlist Admin"""
    
    list_display = ['user', 'product', 'created_at']
    search_fields = ['user__email', 'product__name']
    raw_id_fields = ['user', 'product']


@admin.register(RecentlyViewed)
class RecentlyViewedAdmin(admin.ModelAdmin):
    """Recently Viewed Admin"""
    
    list_display = ['user', 'product', 'viewed_at']
    search_fields = ['user__email', 'product__name']
    raw_id_fields = ['user', 'product']
    date_hierarchy = 'viewed_at'


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    """Coupon Admin"""
    
    list_display = [
        'code', 'discount_type', 'discount_value',
        'usage_limit', 'usage_count', 'is_active', 'is_valid'
    ]
    list_filter = ['discount_type', 'is_active']
    search_fields = ['code', 'description']
    filter_horizontal = ['applicable_products', 'applicable_categories']
    
    def is_valid(self, obj):
        return obj.is_valid
    is_valid.boolean = True


@admin.register(FlashSale)
class FlashSaleAdmin(admin.ModelAdmin):
    """Flash Sale Admin"""
    
    list_display = [
        'product', 'sale_price', 'discount_percentage',
        'quantity_limit', 'quantity_sold', 'is_live',
        'starts_at', 'ends_at'
    ]
    list_filter = ['is_active']
    search_fields = ['product__name']
    raw_id_fields = ['product']
    
    def is_live(self, obj):
        return obj.is_live
    is_live.boolean = True
