"""
Admin configuration for orders app.
"""
from django.contrib import admin
from .models import Cart, CartItem, Order, OrderItem, OrderStatusHistory, Coupon


class OrderItemInline(admin.TabularInline):
    """Inline admin for order items."""
    model = OrderItem
    extra = 0
    readonly_fields = ['product_name', 'product_sku', 'price', 'quantity']


class OrderStatusHistoryInline(admin.TabularInline):
    """Inline admin for order status history."""
    model = OrderStatusHistory
    extra = 0
    readonly_fields = ['old_status', 'new_status', 'changed_by', 'note', 'created_at']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Admin for Order model."""
    
    list_display = [
        'order_number', 'user', 'status', 'total_amount',
        'items_count', 'created_at'
    ]
    list_filter = ['status', 'shipping_method', 'created_at']
    search_fields = ['order_number', 'user__username', 'user__email', 'tracking_number']
    list_editable = ['status']
    readonly_fields = ['order_number', 'created_at', 'updated_at']
    inlines = [OrderItemInline, OrderStatusHistoryInline]
    
    fieldsets = (
        ('Order Information', {
            'fields': ('order_number', 'user', 'status')
        }),
        ('Pricing', {
            'fields': ('subtotal', 'shipping_cost', 'tax', 'discount', 'total_amount')
        }),
        ('Shipping', {
            'fields': (
                'shipping_method', 'shipping_address', 'shipping_city',
                'shipping_state', 'shipping_country', 'shipping_postal_code',
                'tracking_number'
            )
        }),
        ('Contact', {
            'fields': ('email', 'phone')
        }),
        ('Notes', {
            'fields': ('customer_note', 'admin_note')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'paid_at', 'shipped_at', 'delivered_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    """Admin for Coupon model."""
    
    list_display = [
        'code', 'discount_type', 'discount_value',
        'minimum_order', 'uses_count', 'max_uses', 'is_active'
    ]
    list_filter = ['discount_type', 'is_active']
    search_fields = ['code', 'description']


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    """Admin for Cart model."""
    
    list_display = ['id', 'user', 'session_id', 'item_count', 'updated_at']
    search_fields = ['user__username', 'session_id']


@admin.register(OrderStatusHistory)
class OrderStatusHistoryAdmin(admin.ModelAdmin):
    """Admin for OrderStatusHistory model."""
    
    list_display = ['order', 'old_status', 'new_status', 'changed_by', 'created_at']
    list_filter = ['new_status', 'created_at']
    search_fields = ['order__order_number']
