"""
Admin configuration for payments app.
"""
from django.contrib import admin
from .models import PaymentReceipt, PaymentMethod, BankAccount


@admin.register(PaymentReceipt)
class PaymentReceiptAdmin(admin.ModelAdmin):
    """Admin for PaymentReceipt model."""
    
    list_display = [
        'id', 'order', 'user', 'amount_paid', 'status',
        'reviewed_by', 'created_at'
    ]
    list_filter = ['status', 'payment_date', 'created_at']
    search_fields = [
        'order__order_number', 'user__username',
        'reference_number', 'bank_name'
    ]
    list_editable = ['status']
    readonly_fields = ['created_at', 'updated_at', 'reviewed_at']
    
    fieldsets = (
        ('Receipt Information', {
            'fields': ('order', 'user', 'receipt_file')
        }),
        ('Payment Details', {
            'fields': (
                'amount_paid', 'payment_date', 'reference_number',
                'bank_name', 'sender_name', 'notes'
            )
        }),
        ('Verification', {
            'fields': (
                'status', 'reviewed_by', 'reviewed_at', 'rejection_reason'
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    """Admin for PaymentMethod model."""
    
    list_display = ['name', 'is_active', 'display_order', 'created_at']
    list_editable = ['is_active', 'display_order']
    search_fields = ['name', 'description']


@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    """Admin for BankAccount model."""
    
    list_display = [
        'name', 'account_name', 'account_number',
        'is_active', 'is_default', 'display_order'
    ]
    list_editable = ['is_active', 'is_default', 'display_order']
    search_fields = ['name', 'account_name', 'account_number']
