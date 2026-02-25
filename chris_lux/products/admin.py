"""
Products admin configuration.
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Product, ProductImage, Variation


class ProductImageInline(admin.TabularInline):
    """Product image inline."""
    model = ProductImage
    extra = 1
    fields = ['image', 'alt_text', 'is_primary', 'order']


class VariationInline(admin.TabularInline):
    """Product variation inline."""
    model = Variation
    extra = 1
    fields = ['variation_type', 'name', 'value', 'price_adjustment', 'stock_quantity', 'is_active']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'parent', 'product_count', 'is_featured', 'is_active', 'order']
    list_filter = ['is_featured', 'is_active', 'parent']
    search_fields = ['name', 'description']
    list_editable = ['is_featured', 'is_active', 'order']
    prepopulated_fields = {'slug': ('name',)}
    
    def product_count(self, obj):
        return obj.product_count
    product_count.short_description = 'Products'


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'sku', 'category', 'price', 'stock_quantity', 'is_in_stock', 'is_active', 'is_featured', 'created_at']
    list_filter = ['is_active', 'is_featured', 'is_best_seller', 'is_new', 'category', 'created_at']
    search_fields = ['name', 'sku', 'description']
    list_editable = ['price', 'is_active', 'is_featured']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at', 'updated_at']
    inlines = [ProductImageInline, VariationInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'sku', 'category', 'description', 'short_description')
        }),
        ('Pricing', {
            'fields': ('price', 'compare_at_price', 'cost_price')
        }),
        ('Inventory', {
            'fields': ('stock_quantity', 'track_stock', 'allow_backorders', 'has_variations')
        }),
        ('Shipping', {
            'fields': ('weight',)
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description', 'tags')
        }),
        ('Display Options', {
            'fields': ('is_active', 'is_featured', 'is_best_seller', 'is_new')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def is_in_stock(self, obj):
        return obj.is_in_stock
    is_in_stock.boolean = True
    is_in_stock.short_description = 'In Stock'
    
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('images', 'variations')


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ['product', 'image_preview', 'is_primary', 'order', 'created_at']
    list_filter = ['is_primary', 'created_at']
    search_fields = ['product__name', 'alt_text']
    list_editable = ['is_primary', 'order']
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height: 50px;" />', obj.image.url)
        return 'No Image'
    image_preview.short_description = 'Preview'


@admin.register(Variation)
class VariationAdmin(admin.ModelAdmin):
    list_display = ['product', 'variation_type', 'name', 'value', 'final_price', 'stock_quantity', 'is_active']
    list_filter = ['variation_type', 'is_active']
    search_fields = ['product__name', 'name', 'value']
    list_editable = ['stock_quantity', 'is_active']
    
    def final_price(self, obj):
        return obj.final_price
    final_price.short_description = 'Final Price'
