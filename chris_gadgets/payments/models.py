"""
Payments Models - Bank Transfer Payment System with Receipt Upload
"""
from django.db import models
from django.utils import timezone
from django.conf import settings
import uuid


class Payment(models.Model):
    """Payment Model for Bank Transfer"""
    
    # Payment Status
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('awaiting_verification', 'Awaiting Verification'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
        ('refunded', 'Refunded'),
    ]
    
    # Payment Method (only bank transfer for now)
    METHOD_CHOICES = [
        ('bank_transfer', 'Bank Transfer'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payment_reference = models.CharField(max_length=50, unique=True, blank=True)
    order = models.OneToOneField(
        'orders.Order',
        on_delete=models.CASCADE,
        related_name='payment'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='payments'
    )
    
    # Payment Details
    method = models.CharField(
        max_length=20,
        choices=METHOD_CHOICES,
        default='bank_transfer'
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(
        max_length=25,
        choices=STATUS_CHOICES,
        default='pending'
    )
    
    # Bank Transfer Details
    bank_name = models.CharField(max_length=100, blank=True, null=True)
    account_name = models.CharField(max_length=255, blank=True, null=True)
    account_number = models.CharField(max_length=50, blank=True, null=True)
    transfer_reference = models.CharField(max_length=100, blank=True, null=True)
    transfer_date = models.DateTimeField(blank=True, null=True)
    
    # Receipt Upload
    receipt = models.ImageField(
        upload_to='receipts/%Y/%m/',
        blank=True,
        null=True
    )
    receipt_uploaded_at = models.DateTimeField(blank=True, null=True)
    
    # QR Code for Payment
    qr_code = models.ImageField(
        upload_to='qr_codes/%Y/%m/',
        blank=True,
        null=True
    )
    
    # Verification
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='verified_payments'
    )
    verified_at = models.DateTimeField(blank=True, null=True)
    verification_notes = models.TextField(blank=True, null=True)
    rejection_reason = models.TextField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Payment #{self.payment_reference} - {self.status}"
    
    def save(self, *args, **kwargs):
        if not self.payment_reference:
            # Generate payment reference
            today = timezone.now().strftime('%Y%m%d')
            last_payment = Payment.objects.filter(
                payment_reference__startswith=f"PAY-{today}"
            ).order_by('-payment_reference').first()
            
            if last_payment:
                last_number = int(last_payment.payment_reference.split('-')[-1])
                new_number = last_number + 1
            else:
                new_number = 1
            
            self.payment_reference = f"PAY-{today}-{new_number:04d}"
        
        super().save(*args, **kwargs)
    
    @property
    def status_display_class(self):
        """Get CSS class for status badge"""
        status_classes = {
            'pending': 'warning',
            'awaiting_verification': 'info',
            'verified': 'success',
            'rejected': 'danger',
            'refunded': 'secondary',
        }
        return status_classes.get(self.status, 'secondary')
    
    @property
    def can_upload_receipt(self):
        """Check if receipt can be uploaded"""
        return self.status in ['pending', 'rejected']
    
    @property
    def is_verified(self):
        """Check if payment is verified"""
        return self.status == 'verified'


class BankAccount(models.Model):
    """Bank Account Details for Payments"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bank_name = models.CharField(max_length=100)
    account_name = models.CharField(max_length=255)
    account_number = models.CharField(max_length=50)
    branch = models.CharField(max_length=100, blank=True, null=True)
    swift_code = models.CharField(max_length=20, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    display_order = models.PositiveIntegerField(default=0)
    instructions = models.TextField(
        blank=True,
        null=True,
        help_text="Additional payment instructions"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['is_default', 'display_order', 'bank_name']
    
    def __str__(self):
        return f"{self.bank_name} - {self.account_number}"
    
    def save(self, *args, **kwargs):
        if self.is_default:
            BankAccount.objects.filter(is_default=True).update(is_default=False)
        super().save(*args, **kwargs)


class PaymentVerificationLog(models.Model):
    """Payment Verification Activity Log"""
    
    ACTION_CHOICES = [
        ('uploaded', 'Receipt Uploaded'),
        ('verified', 'Payment Verified'),
        ('rejected', 'Payment Rejected'),
        ('resent', 'Verification Resent'),
        ('viewed', 'Payment Viewed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    payment = models.ForeignKey(
        Payment,
        on_delete=models.CASCADE,
        related_name='verification_logs'
    )
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True
    )
    notes = models.TextField(blank=True, null=True)
    old_status = models.CharField(max_length=20, blank=True, null=True)
    new_status = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.payment.payment_reference} - {self.action}"


class Refund(models.Model):
    """Refund Model"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
    ]
    
    REASON_CHOICES = [
        ('defective', 'Defective Product'),
        ('wrong_item', 'Wrong Item Received'),
        ('not_as_described', 'Not as Described'),
        ('changed_mind', 'Changed Mind'),
        ('other', 'Other'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    refund_reference = models.CharField(max_length=50, unique=True, blank=True)
    payment = models.ForeignKey(
        Payment,
        on_delete=models.CASCADE,
        related_name='refunds'
    )
    order = models.ForeignKey(
        'orders.Order',
        on_delete=models.CASCADE,
        related_name='refunds'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='refunds'
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    reason = models.CharField(max_length=20, choices=REASON_CHOICES)
    reason_details = models.TextField(blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    processed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='processed_refunds'
    )
    processed_at = models.DateTimeField(blank=True, null=True)
    admin_notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Refund #{self.refund_reference}"
    
    def save(self, *args, **kwargs):
        if not self.refund_reference:
            today = timezone.now().strftime('%Y%m%d')
            last_refund = Refund.objects.filter(
                refund_reference__startswith=f"REF-{today}"
            ).order_by('-refund_reference').first()
            
            if last_refund:
                last_number = int(last_refund.refund_reference.split('-')[-1])
                new_number = last_number + 1
            else:
                new_number = 1
            
            self.refund_reference = f"REF-{today}-{new_number:04d}"
        
        super().save(*args, **kwargs)
