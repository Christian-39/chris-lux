"""
Orders admin configuration.
"""

from django.contrib import admin
from django.utils.html import format_html
from .models import Order, OrderItem, Payment


class OrderItemInline(admin.TabularInline):
    """Order item inline."""
    model = OrderItem
    extra = 0
    readonly_fields = ['subtotal']


class PaymentInline(admin.TabularInline):
    """Payment inline."""
    model = Payment
    extra = 0
    readonly_fields = ['reference', 'amount', 'status', 'created_at']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'order_number', 'full_name', 'total', 'status_badge',
        'payment_status_badge', 'created_at'
    ]
    list_filter = ['status', 'payment_status', 'created_at']
    search_fields = ['order_number', 'email', 'first_name', 'last_name', 'phone']
    readonly_fields = ['order_number', 'created_at', 'updated_at']
    inlines = [OrderItemInline, PaymentInline]
    
    fieldsets = (
        ('Order Information', {
            'fields': ('order_number', 'user', 'status', 'payment_status')
        }),
        ('Customer Information', {
            'fields': ('first_name', 'last_name', 'email', 'phone')
        }),
        ('Shipping Address', {
            'fields': ('address', 'city', 'state', 'country', 'postal_code')
        }),
        ('Order Totals', {
            'fields': ('subtotal', 'discount_amount', 'shipping_cost', 'total', 'coupon_code')
        }),
        ('Payment Information', {
            'fields': ('payment_method', 'payment_reference', 'payment_transaction_id', 'paid_at')
        }),
        ('Shipping Information', {
            'fields': ('shipping_carrier', 'tracking_number', 'shipped_at', 'delivered_at')
        }),
        ('Notes', {
            'fields': ('customer_note', 'admin_note')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def status_badge(self, obj):
        colors = {
            'pending': 'warning',
            'confirmed': 'info',
            'processing': 'primary',
            'shipped': 'secondary',
            'delivered': 'success',
            'cancelled': 'danger',
            'refunded': 'dark',
        }
        return format_html(
            '<span class="badge badge-{}" style="padding: 5px 10px;">{}</span>',
            colors.get(obj.status, 'secondary'),
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def payment_status_badge(self, obj):
        colors = {
            'pending': 'warning',
            'paid': 'success',
            'failed': 'danger',
            'refunded': 'dark',
        }
        return format_html(
            '<span class="badge badge-{}" style="padding: 5px 10px;">{}</span>',
            colors.get(obj.payment_status, 'secondary'),
            obj.get_payment_status_display()
        )
    payment_status_badge.short_description = 'Payment'
    
    actions = ['mark_confirmed', 'mark_processing', 'mark_shipped', 'mark_delivered', 'mark_cancelled']
    
    def mark_confirmed(self, request, queryset):
        queryset.update(status='confirmed')
    mark_confirmed.short_description = "Mark selected orders as confirmed"
    
    def mark_processing(self, request, queryset):
        queryset.update(status='processing')
    mark_processing.short_description = "Mark selected orders as processing"
    
    def mark_shipped(self, request, queryset):
        from django.utils import timezone
        queryset.update(status='shipped', shipped_at=timezone.now())
    mark_shipped.short_description = "Mark selected orders as shipped"
    
    def mark_delivered(self, request, queryset):
        from django.utils import timezone
        queryset.update(status='delivered', delivered_at=timezone.now())
    mark_delivered.short_description = "Mark selected orders as delivered"
    
    def mark_cancelled(self, request, queryset):
        queryset.update(status='cancelled')
    mark_cancelled.short_description = "Mark selected orders as cancelled"


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['reference', 'order', 'amount', 'status', 'payment_method', 'created_at']
    list_filter = ['status', 'payment_method', 'created_at']
    search_fields = ['reference', 'order__order_number', 'transaction_id']
    readonly_fields = ['reference', 'created_at']
