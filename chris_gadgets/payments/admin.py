"""
Payments Admin Configuration
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import Payment, BankAccount, PaymentVerificationLog, Refund


class PaymentVerificationLogInline(admin.TabularInline):
    """Payment Verification Log Inline"""
    model = PaymentVerificationLog
    extra = 0
    readonly_fields = ['action', 'performed_by', 'notes', 'old_status', 'new_status', 'created_at']
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """Payment Admin"""
    
    list_display = [
        'payment_reference', 'order', 'user', 'amount',
        'status', 'receipt_preview', 'created_at'
    ]
    list_filter = ['status', 'method', 'created_at']
    search_fields = [
        'payment_reference', 'order__order_number',
        'user__email', 'transfer_reference'
    ]
    raw_id_fields = ['order', 'user', 'verified_by']
    inlines = [PaymentVerificationLogInline]
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Payment Information', {
            'fields': ('payment_reference', 'order', 'user', 'method', 'amount', 'status')
        }),
        ('Bank Transfer Details', {
            'fields': (
                'bank_name', 'account_name', 'account_number',
                'transfer_reference', 'transfer_date'
            )
        }),
        ('Receipt', {
            'fields': ('receipt', 'receipt_uploaded_at')
        }),
        ('QR Code', {
            'fields': ('qr_code',)
        }),
        ('Verification', {
            'fields': (
                'verified_by', 'verified_at', 'verification_notes', 'rejection_reason'
            )
        }),
    )
    
    readonly_fields = [
        'payment_reference', 'created_at', 'updated_at',
        'receipt_uploaded_at', 'verified_at'
    ]
    
    actions = ['verify_payments', 'reject_payments']
    
    def receipt_preview(self, obj):
        if obj.receipt:
            return format_html(
                '<a href="{}" target="_blank"><img src="{}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 4px;" /></a>',
                obj.receipt.url, obj.receipt.url
            )
        return '-'
    receipt_preview.short_description = 'Receipt'
    
    def verify_payments(self, request, queryset):
        from django.utils import timezone
        for payment in queryset:
            old_status = payment.status
            payment.status = 'verified'
            payment.verified_by = request.user
            payment.verified_at = timezone.now()
            payment.save()
            
            # Update order payment status
            payment.order.payment_status = 'verified'
            payment.order.save()
            
            PaymentVerificationLog.objects.create(
                payment=payment,
                action='verified',
                performed_by=request.user,
                old_status=old_status,
                new_status='verified'
            )
    verify_payments.short_description = 'Verify selected payments'
    
    def reject_payments(self, request, queryset):
        for payment in queryset:
            old_status = payment.status
            payment.status = 'rejected'
            payment.save()
            
            PaymentVerificationLog.objects.create(
                payment=payment,
                action='rejected',
                performed_by=request.user,
                old_status=old_status,
                new_status='rejected'
            )
    reject_payments.short_description = 'Reject selected payments'


@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    """Bank Account Admin"""
    
    list_display = [
        'bank_name', 'account_name', 'account_number',
        'is_active', 'is_default', 'display_order'
    ]
    list_filter = ['is_active', 'is_default']
    search_fields = ['bank_name', 'account_name', 'account_number']
    list_editable = ['is_active', 'is_default', 'display_order']


@admin.register(PaymentVerificationLog)
class PaymentVerificationLogAdmin(admin.ModelAdmin):
    """Payment Verification Log Admin"""
    
    list_display = [
        'payment', 'action', 'performed_by',
        'old_status', 'new_status', 'created_at'
    ]
    list_filter = ['action', 'created_at']
    search_fields = ['payment__payment_reference']
    raw_id_fields = ['payment', 'performed_by']
    date_hierarchy = 'created_at'
    readonly_fields = [
        'payment', 'action', 'performed_by', 'notes',
        'old_status', 'new_status', 'created_at'
    ]
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    """Refund Admin"""
    
    list_display = [
        'refund_reference', 'order', 'user', 'amount',
        'reason', 'status', 'created_at'
    ]
    list_filter = ['status', 'reason', 'created_at']
    search_fields = [
        'refund_reference', 'order__order_number', 'user__email'
    ]
    raw_id_fields = ['payment', 'order', 'user', 'processed_by']
    date_hierarchy = 'created_at'
    
    readonly_fields = ['refund_reference', 'created_at', 'updated_at']
    actions = ['process_refunds', 'reject_refunds']
    
    def process_refunds(self, request, queryset):
        from django.utils import timezone
        for refund in queryset:
            refund.status = 'completed'
            refund.processed_by = request.user
            refund.processed_at = timezone.now()
            refund.save()
    process_refunds.short_description = 'Process selected refunds'
    
    def reject_refunds(self, request, queryset):
        from django.utils import timezone
        for refund in queryset:
            refund.status = 'rejected'
            refund.processed_by = request.user
            refund.processed_at = timezone.now()
            refund.save()
    reject_refunds.short_description = 'Reject selected refunds'
