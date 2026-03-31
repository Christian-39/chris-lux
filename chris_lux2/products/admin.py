"""
Admin configuration for products app.
"""
from django.contrib import admin
from .models import Category, Product, ProductImage, ProductVideo, ProductReview, Wishlist


class ProductImageInline(admin.TabularInline):
    """Inline admin for product images."""
    model = ProductImage
    extra = 1
    fields = ['image', 'alt_text', 'is_primary', 'display_order']


class ProductVideoInline(admin.TabularInline):
    """Inline admin for product videos."""
    model = ProductVideo
    extra = 1
    fields = ['video', 'thumbnail', 'title', 'display_order']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Admin for Category model."""
    
    list_display = ['name', 'slug', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Admin for Product model."""
    
    list_display = [
        'name', 'sku', 'product_type', 'category', 'price',
        'stock_quantity', 'is_active', 'is_featured', 'created_at'
    ]
    list_filter = [
        'product_type', 'category', 'is_active', 'is_featured',
        'is_new_arrival', 'is_bestseller', 'hair_texture', 'hair_origin'
    ]
    search_fields = ['name', 'sku', 'description', 'meta_keywords']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['price', 'stock_quantity', 'is_active', 'is_featured']
    inlines = [ProductImageInline, ProductVideoInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'sku', 'description', 'short_description')
        }),
        ('Categorization', {
            'fields': ('product_type', 'category')
        }),
        ('Hair Specifications', {
            'fields': ('hair_texture', 'hair_origin', 'length')
        }),
        ('Pricing', {
            'fields': ('price', 'compare_at_price', 'cost_per_item')
        }),
        ('Inventory', {
            'fields': ('stock_quantity', 'track_inventory')
        }),
        ('Status', {
            'fields': ('is_active', 'is_featured', 'is_new_arrival', 'is_bestseller')
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description', 'meta_keywords'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    """Admin for ProductReview model."""
    
    list_display = ['product', 'user', 'rating', 'is_approved', 'created_at']
    list_filter = ['rating', 'is_approved', 'created_at']
    search_fields = ['product__name', 'user__username', 'comment']
    list_editable = ['is_approved']


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    """Admin for Wishlist model."""
    
    list_display = ['user', 'product', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'product__name']
