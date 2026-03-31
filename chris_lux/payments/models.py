"""
Payment models for Chris-Lux.
"""
from django.db import models
from django.urls import reverse
from django.utils import timezone


class PaymentReceipt(models.Model):
    """Payment receipt model for bank transfers."""
    
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    order = models.ForeignKey(
        'orders.Order',
        on_delete=models.CASCADE,
        related_name='receipts'
    )
    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='payment_receipts'
    )
    
    # Receipt file
    receipt_file = models.FileField(
        upload_to='receipts/%Y/%m/',
        help_text='Upload payment receipt (image or PDF)'
    )
    
    # Payment details
    amount_paid = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text='Amount shown on receipt'
    )
    payment_date = models.DateField(
        help_text='Date of payment'
    )
    reference_number = models.CharField(
        max_length=255,
        blank=True,
        help_text='Bank reference or transaction number'
    )
    bank_name = models.CharField(
        max_length=255,
        blank=True,
        help_text='Bank used for transfer'
    )
    sender_name = models.CharField(
        max_length=255,
        blank=True,
        help_text='Name on the bank account'
    )
    notes = models.TextField(
        blank=True,
        help_text='Additional notes about the payment'
    )
    
    # Verification
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    reviewed_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_receipts'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order', 'status']),
            models.Index(fields=['user', 'status']),
        ]
    
    def __str__(self):
        return f"Receipt for Order {self.order.order_number}"
    
    def get_absolute_url(self):
        return reverse('payments:receipt_detail', kwargs={'pk': self.pk})
    
    @property
    def is_pending(self):
        return self.status == 'pending'
    
    @property
    def is_approved(self):
        return self.status == 'approved'
    
    @property
    def is_rejected(self):
        return self.status == 'rejected'
    
    def approve(self, reviewed_by, notes=''):
        """Approve the receipt."""
        from orders.models import OrderStatusHistory
        from notifications.models import Notification
        
        self.status = 'approved'
        self.reviewed_by = reviewed_by
        self.reviewed_at = timezone.now()
        self.save()
        
        # Update order status
        old_status = self.order.status
        self.order.status = 'verified'
        self.order.paid_at = timezone.now()
        self.order.save()
        
        # Create status history
        OrderStatusHistory.objects.create(
            order=self.order,
            old_status=old_status,
            new_status='verified',
            changed_by=reviewed_by,
            note=f'Payment verified. {notes}',
        )
        
        # Create notification
        Notification.objects.create(
            user=self.user,
            notification_type='payment',
            title='Payment Verified',
            message=f'Your payment for order {self.order.order_number} has been verified.',
            order=self.order,
        )
    
    def reject(self, reviewed_by, reason):
        """Reject the receipt."""
        from orders.models import OrderStatusHistory
        from notifications.models import Notification
        
        self.status = 'rejected'
        self.reviewed_by = reviewed_by
        self.reviewed_at = timezone.now()
        self.rejection_reason = reason
        self.save()
        
        # Create status history
        OrderStatusHistory.objects.create(
            order=self.order,
            old_status=self.order.status,
            new_status=self.order.status,
            changed_by=reviewed_by,
            note=f'Receipt rejected: {reason}',
        )
        
        # Create notification
        Notification.objects.create(
            user=self.user,
            notification_type='payment',
            title='Payment Receipt Rejected',
            message=f'Your payment receipt for order {self.order.order_number} was rejected. Reason: {reason}',
            order=self.order,
        )


class PaymentMethod(models.Model):
    """Available payment methods."""
    
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['display_order', 'name']
    
    def __str__(self):
        return self.name


class BankAccount(models.Model):
    """Bank account details for transfers."""
    
    name = models.CharField(max_length=255, help_text='Bank name')
    account_name = models.CharField(max_length=255, help_text='Account holder name')
    account_number = models.CharField(max_length=100, help_text='Account number')
    routing_number = models.CharField(
        max_length=100,
        blank=True,
        help_text='Routing/Swift code'
    )
    bank_address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    display_order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['display_order', 'name']
        verbose_name_plural = 'Bank accounts'
    
    def __str__(self):
        return f"{self.name} - {self.account_name}"
    
    def save(self, *args, **kwargs):
        if self.is_default:
            BankAccount.objects.filter(is_default=True).update(is_default=False)
        super().save(*args, **kwargs)
