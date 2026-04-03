"""
Payments Views - Bank Transfer Payment System
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.utils import timezone
from django.conf import settings
import qrcode
import qrcode.image.svg
from io import BytesIO
import base64

from .models import Payment, BankAccount, PaymentVerificationLog
from orders.models import Order


@login_required
def payment_view(request, order_id):
    """Payment Page View"""
    order = get_object_or_404(
        Order.objects.select_related('payment'),
        id=order_id,
        user=request.user
    )
    
    # Check if payment already exists
    payment, created = Payment.objects.get_or_create(
        order=order,
        defaults={
            'user': request.user,
            'amount': order.total,
            'status': 'pending'
        }
    )
    
    # Get bank accounts
    bank_accounts = BankAccount.objects.filter(is_active=True)
    
    # Generate QR code for payment
    if not payment.qr_code:
        qr_data = f"Order: {order.order_number}\nAmount: ₦{order.total}\nReference: {payment.payment_reference}"
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(qr_data)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        
        # Save QR code
        from django.core.files.base import ContentFile
        payment.qr_code.save(
            f'qr_{payment.payment_reference}.png',
            ContentFile(buffer.getvalue())
        )
    
    context = {
        'order': order,
        'payment': payment,
        'bank_accounts': bank_accounts,
        'site_settings': settings,
    }
    
    return render(request, 'payments/payment.html', context)


@login_required
def upload_receipt_view(request, payment_id):
    """Upload Payment Receipt View"""
    payment = get_object_or_404(
        Payment,
        id=payment_id,
        user=request.user
    )
    
    if not payment.can_upload_receipt:
        messages.error(request, 'You cannot upload a receipt for this payment.')
        return redirect('payments:payment', order_id=payment.order.id)
    
    if request.method == 'POST':
        receipt = request.FILES.get('receipt')
        bank_name = request.POST.get('bank_name')
        transfer_reference = request.POST.get('transfer_reference')
        transfer_date = request.POST.get('transfer_date')
        
        if not receipt:
            messages.error(request, 'Please upload a receipt image.')
            return redirect('payments:upload_receipt', payment_id=payment.id)
        
        # Validate file type
        allowed_types = ['image/jpeg', 'image/png', 'image/jpg', 'application/pdf']
        if receipt.content_type not in allowed_types:
            messages.error(request, 'Please upload a valid image or PDF file.')
            return redirect('payments:upload_receipt', payment_id=payment.id)
        
        # Validate file size (max 5MB)
        if receipt.size > 5 * 1024 * 1024:
            messages.error(request, 'File size should not exceed 5MB.')
            return redirect('payments:upload_receipt', payment_id=payment.id)
        
        # Update payment
        old_status = payment.status
        payment.receipt = receipt
        payment.bank_name = bank_name
        payment.transfer_reference = transfer_reference
        if transfer_date:
            payment.transfer_date = timezone.datetime.strptime(transfer_date, '%Y-%m-%d')
        payment.status = 'awaiting_verification'
        payment.receipt_uploaded_at = timezone.now()
        payment.save()
        
        # Update order payment status
        payment.order.payment_status = 'awaiting_verification'
        payment.order.save()
        
        # Log verification
        PaymentVerificationLog.objects.create(
            payment=payment,
            action='uploaded',
            old_status=old_status,
            new_status='awaiting_verification'
        )
        
        messages.success(
            request,
            'Receipt uploaded successfully! We will verify your payment shortly.'
        )
        return redirect('accounts:order_history')
    
    context = {
        'payment': payment,
    }
    
    return render(request, 'payments/upload_receipt.html', context)


@login_required
def payment_status_view(request, payment_id):
    """Check Payment Status View"""
    payment = get_object_or_404(Payment, id=payment_id, user=request.user)
    
    context = {
        'payment': payment,
        'order': payment.order,
    }
    
    return render(request, 'payments/payment_status.html', context)


@login_required
def download_qr_code_view(request, payment_id):
    """Download QR Code View"""
    payment = get_object_or_404(Payment, id=payment_id, user=request.user)
    
    if payment.qr_code:
        from django.http import FileResponse
        return FileResponse(
            payment.qr_code.open(),
            as_attachment=True,
            filename=f'payment_qr_{payment.payment_reference}.png'
        )
    
    messages.error(request, 'QR code not available.')
    return redirect('payments:payment', order_id=payment.order.id)


@login_required
def resend_verification_view(request, payment_id):
    """Resend Payment Verification Request"""
    payment = get_object_or_404(Payment, id=payment_id, user=request.user)
    
    if payment.status != 'rejected':
        messages.error(request, 'This payment cannot be resubmitted.')
        return redirect('payments:payment_status', payment_id=payment.id)
    
    old_status = payment.status
    payment.status = 'pending'
    payment.rejection_reason = None
    payment.save()
    
    # Update order
    payment.order.payment_status = 'pending'
    payment.order.save()
    
    # Log
    PaymentVerificationLog.objects.create(
        payment=payment,
        action='resent',
        old_status=old_status,
        new_status='pending'
    )
    
    messages.success(request, 'You can now upload a new receipt.')
    return redirect('payments:upload_receipt', payment_id=payment.id)


# AJAX Views
@require_POST
def check_payment_status_ajax(request):
    """Check payment status via AJAX"""
    payment_id = request.POST.get('payment_id')
    
    try:
        payment = Payment.objects.get(id=payment_id, user=request.user)
        
        return JsonResponse({
            'success': True,
            'status': payment.status,
            'status_display': payment.get_status_display(),
            'status_class': payment.status_display_class,
            'is_verified': payment.is_verified,
        })
    
    except Payment.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Payment not found'
        })


def get_payment_instructions(request):
    """Get payment instructions"""
    bank_accounts = BankAccount.objects.filter(is_active=True)
    
    instructions = []
    for account in bank_accounts:
        instructions.append({
            'bank_name': account.bank_name,
            'account_name': account.account_name,
            'account_number': account.account_number,
            'instructions': account.instructions,
        })
    
    return JsonResponse({
        'success': True,
        'accounts': instructions,
    })
