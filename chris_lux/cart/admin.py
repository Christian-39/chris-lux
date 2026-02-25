"""
Cart admin configuration.
"""

from django.contrib import admin
from .models import Cart, CartItem


class CartItemInline(admin.TabularInline):
    """Cart item inline."""
    model = CartItem
    extra = 0
    readonly_fields = ['subtotal']
    autocomplete_fields = ['product', 'variation']


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'item_count', 'subtotal', 'total', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__email', 'session_id']
    readonly_fields = ['subtotal', 'discount_amount', 'shipping_cost', 'total']
    inlines = [CartItemInline]
    
    def subtotal(self, obj):
        return obj.subtotal
    subtotal.short_description = 'Subtotal'
    
    def total(self, obj):
        return obj.total
    total.short_description = 'Total'


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['cart', 'product', 'variation', 'quantity', 'unit_price', 'subtotal', 'added_at']
    list_filter = ['added_at']
    search_fields = ['cart__user__email', 'product__name']
    autocomplete_fields = ['cart', 'product', 'variation']
    
    def unit_price(self, obj):
        return obj.unit_price
    unit_price.short_description = 'Unit Price'
    
    def subtotal(self, obj):
        return obj.subtotal
    subtotal.short_description = 'Subtotal'
