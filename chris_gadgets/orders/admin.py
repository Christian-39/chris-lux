"""
Orders Admin Configuration
"""
from django.contrib import admin
from .models import (
    Cart, CartItem, Order, OrderItem,
    OrderStatusHistory, SavedCart, FrequentlyBoughtTogether
)


class CartItemInline(admin.TabularInline):
    """Cart Item Inline"""
    model = CartItem
    extra = 0
    raw_id_fields = ['product']
    readonly_fields = ['subtotal']


class OrderItemInline(admin.TabularInline):
    """Order Item Inline"""
    model = OrderItem
    extra = 0
    raw_id_fields = ['product']
    readonly_fields = ['total_price']


class OrderStatusHistoryInline(admin.TabularInline):
    """Order Status History Inline"""
    model = OrderStatusHistory
    extra = 0
    readonly_fields = ['status', 'notes', 'created_by', 'created_at']
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    """Cart Admin"""
    
    list_display = ['user', 'session_id', 'item_count', 'subtotal', 'updated_at']
    search_fields = ['user__email', 'session_id']
    raw_id_fields = ['user']
    inlines = [CartItemInline]
    readonly_fields = ['subtotal', 'total']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Order Admin"""
    
    list_display = [
        'order_number', 'user', 'status', 'payment_status',
        'item_count', 'total', 'created_at'
    ]
    list_filter = [
        'status', 'payment_status', 'created_at',
        'shipping_state'
    ]
    search_fields = [
        'order_number', 'user__email', 'user__first_name',
        'user__last_name', 'shipping_name', 'tracking_number'
    ]
    raw_id_fields = ['user', 'coupon']
    inlines = [OrderItemInline, OrderStatusHistoryInline]
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Order Information', {
            'fields': ('order_number', 'user', 'status', 'payment_status')
        }),
        ('Shipping Address', {
            'fields': (
                'shipping_name', 'shipping_phone', 'shipping_address',
                'shipping_city', 'shipping_state', 'shipping_lga',
                'shipping_landmark', 'shipping_postal_code'
            )
        }),
        ('Pricing', {
            'fields': (
                'subtotal', 'shipping_cost', 'discount_amount',
                'tax_amount', 'total', 'coupon', 'coupon_code'
            )
        }),
        ('Tracking', {
            'fields': (
                'tracking_number', 'shipping_carrier',
                'shipped_at', 'delivered_at'
            )
        }),
        ('Notes', {
            'fields': ('customer_note', 'admin_note')
        }),
    )
    
    readonly_fields = ['order_number', 'created_at', 'updated_at']
    actions = ['mark_as_confirmed', 'mark_as_shipped', 'mark_as_delivered']
    
    def mark_as_confirmed(self, request, queryset):
        for order in queryset:
            order.status = 'confirmed'
            order.save()
            OrderStatusHistory.objects.create(
                order=order,
                status='confirmed',
                notes='Status changed by admin',
                created_by=request.user
            )
    mark_as_confirmed.short_description = 'Mark selected orders as confirmed'
    
    def mark_as_shipped(self, request, queryset):
        from django.utils import timezone
        for order in queryset:
            order.status = 'shipped'
            order.shipped_at = timezone.now()
            order.save()
            OrderStatusHistory.objects.create(
                order=order,
                status='shipped',
                notes='Status changed by admin',
                created_by=request.user
            )
    mark_as_shipped.short_description = 'Mark selected orders as shipped'
    
    def mark_as_delivered(self, request, queryset):
        from django.utils import timezone
        for order in queryset:
            order.status = 'delivered'
            order.delivered_at = timezone.now()
            order.save()
            OrderStatusHistory.objects.create(
                order=order,
                status='delivered',
                notes='Status changed by admin',
                created_by=request.user
            )
    mark_as_delivered.short_description = 'Mark selected orders as delivered'


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    """Order Item Admin"""
    
    list_display = [
        'order', 'product_name', 'quantity',
        'unit_price', 'total_price'
    ]
    search_fields = ['order__order_number', 'product_name', 'product_sku']
    raw_id_fields = ['order', 'product']


@admin.register(OrderStatusHistory)
class OrderStatusHistoryAdmin(admin.ModelAdmin):
    """Order Status History Admin"""
    
    list_display = ['order', 'status', 'created_by', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['order__order_number']
    raw_id_fields = ['order', 'created_by']
    date_hierarchy = 'created_at'
    readonly_fields = ['order', 'status', 'notes', 'created_by', 'created_at']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(SavedCart)
class SavedCartAdmin(admin.ModelAdmin):
    """Saved Cart Admin"""
    
    list_display = ['user', 'name', 'total', 'created_at']
    search_fields = ['user__email', 'name']
    raw_id_fields = ['user']


@admin.register(FrequentlyBoughtTogether)
class FrequentlyBoughtTogetherAdmin(admin.ModelAdmin):
    """Frequently Bought Together Admin"""
    
    list_display = [
        'primary_product', 'related_product',
        'frequency', 'discount_percentage', 'is_active'
    ]
    search_fields = [
        'primary_product__name', 'related_product__name'
    ]
    raw_id_fields = ['primary_product', 'related_product']
