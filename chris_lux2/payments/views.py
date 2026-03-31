"""
Views for payments app.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import DetailView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.utils import timezone

from .models import PaymentReceipt, BankAccount
from orders.models import Order


@login_required
def upload_receipt(request, order_id):
    """Upload payment receipt."""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    if not order.can_upload_receipt():
        messages.error(request, 'Cannot upload receipt for this order.')
        return redirect('orders:order_detail', pk=order.id)
    
    if request.method == 'POST':
        receipt_file = request.FILES.get('receipt_file')
        amount_paid = request.POST.get('amount_paid')
        payment_date = request.POST.get('payment_date')
        reference_number = request.POST.get('reference_number', '')
        bank_name = request.POST.get('bank_name', '')
        sender_name = request.POST.get('sender_name', '')
        notes = request.POST.get('notes', '')
        
        if not receipt_file:
            messages.error(request, 'Please upload a receipt file.')
            return redirect('payments:upload_receipt', order_id=order.id)
        
        if not amount_paid or not payment_date:
            messages.error(request, 'Please provide amount paid and payment date.')
            return redirect('payments:upload_receipt', order_id=order.id)
        
        # Create receipt
        receipt = PaymentReceipt.objects.create(
            order=order,
            user=request.user,
            receipt_file=receipt_file,
            amount_paid=amount_paid,
            payment_date=payment_date,
            reference_number=reference_number,
            bank_name=bank_name,
            sender_name=sender_name,
            notes=notes,
        )
        
        # Update order status
        from orders.models import OrderStatusHistory
        old_status = order.status
        order.status = 'payment_uploaded'
        order.save()
        
        # Create status history
        OrderStatusHistory.objects.create(
            order=order,
            old_status=old_status,
            new_status='payment_uploaded',
            note='Payment receipt uploaded.',
        )
        
        # Create notification for admin
        from notifications.models import Notification
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        # Notify all admin users
        admin_users = User.objects.filter(is_staff=True)
        for admin in admin_users:
            Notification.objects.create(
                user=admin,
                notification_type='payment',
                title='New Payment Receipt',
                message=f'New receipt uploaded for order {order.order_number}.',
                order=order,
            )
        
        # Notify customer
        Notification.objects.create(
            user=request.user,
            notification_type='payment',
            title='Receipt Uploaded',
            message=f'Your payment receipt for order {order.order_number} has been uploaded and is pending verification.',
            order=order,
        )
        
        messages.success(
            request,
            'Receipt uploaded successfully! We will verify your payment shortly.'
        )
        return redirect('orders:order_detail', pk=order.id)
    
    # Get bank accounts for display
    bank_accounts = BankAccount.objects.filter(is_active=True)
    
    return render(request, 'payments/upload_receipt.html', {
        'order': order,
        'bank_accounts': bank_accounts,
    })


class ReceiptDetailView(LoginRequiredMixin, DetailView):
    """Display receipt details."""
    
    model = PaymentReceipt
    template_name = 'payments/receipt_detail.html'
    context_object_name = 'receipt'
    
    def get_queryset(self):
        # Users can only view their own receipts
        if not self.request.user.is_staff:
            return PaymentReceipt.objects.filter(user=self.request.user)
        return PaymentReceipt.objects.all()


class ReceiptListView(LoginRequiredMixin, ListView):
    """List user's receipts."""
    
    model = PaymentReceipt
    template_name = 'payments/receipt_list.html'
    context_object_name = 'receipts'
    paginate_by = 10
    
    def get_queryset(self):
        return PaymentReceipt.objects.filter(
            user=self.request.user
        ).select_related('order').order_by('-created_at')


# Admin views for receipt verification
class StaffRequiredMixin(UserPassesTestMixin):
    """Mixin to check if user is staff."""
    
    def test_func(self):
        return self.request.user.is_staff


class PendingReceiptsView(StaffRequiredMixin, ListView):
    """List pending receipts for admin review."""
    
    model = PaymentReceipt
    template_name = 'payments/admin/pending_receipts.html'
    context_object_name = 'receipts'
    paginate_by = 20
    
    def get_queryset(self):
        return PaymentReceipt.objects.filter(
            status='pending'
        ).select_related('order', 'user').order_by('-created_at')


class AllReceiptsView(StaffRequiredMixin, ListView):
    """List all receipts for admin."""
    
    model = PaymentReceipt
    template_name = 'payments/admin/all_receipts.html'
    context_object_name = 'receipts'
    paginate_by = 20
    
    def get_queryset(self):
        return PaymentReceipt.objects.all().select_related(
            'order', 'user', 'reviewed_by'
        ).order_by('-created_at')


@login_required
def approve_receipt(request, receipt_id):
    """Approve a payment receipt (admin only)."""
    if not request.user.is_staff:
        messages.error(request, 'Unauthorized action.')
        return redirect('core:home')
    
    receipt = get_object_or_404(PaymentReceipt, id=receipt_id)
    
    if request.method == 'POST':
        notes = request.POST.get('notes', '')
        receipt.approve(request.user, notes)
        messages.success(
            request,
            f'Receipt for order {receipt.order.order_number} has been approved.'
        )
    
    return redirect('payments:pending_receipts')


@login_required
def reject_receipt(request, receipt_id):
    """Reject a payment receipt (admin only)."""
    if not request.user.is_staff:
        messages.error(request, 'Unauthorized action.')
        return redirect('core:home')
    
    receipt = get_object_or_404(PaymentReceipt, id=receipt_id)
    
    if request.method == 'POST':
        reason = request.POST.get('reason', '')
        if not reason:
            messages.error(request, 'Please provide a rejection reason.')
            return redirect('payments:pending_receipts')
        
        receipt.reject(request.user, reason)
        messages.success(
            request,
            f'Receipt for order {receipt.order.order_number} has been rejected.'
        )
    
    return redirect('payments:pending_receipts')


@login_required
def receipt_history(request, order_id):
    """View receipt upload history for an order."""
    order = get_object_or_404(Order, id=order_id)
    
    # Check if user owns the order or is staff
    if order.user != request.user and not request.user.is_staff:
        messages.error(request, 'Unauthorized access.')
        return redirect('core:home')
    
    receipts = order.receipts.all().order_by('-created_at')
    
    return render(request, 'payments/receipt_history.html', {
        'order': order,
        'receipts': receipts,
    })
