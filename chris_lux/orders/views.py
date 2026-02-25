"""
Orders views for Chris Lux.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import View, DetailView
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string

import requests
import json

from chris_lux.cart.utils import get_or_create_cart
from .models import Order, OrderItem, Payment
from .forms import CheckoutForm


class CheckoutView(LoginRequiredMixin, View):
    """Checkout view."""
    template_name = 'orders/checkout.html'
    
    def get(self, request):
        cart = get_or_create_cart(request)
        
        if cart.items.count() == 0:
            messages.error(request, 'Your cart is empty.')
            return redirect('cart')
        
        # Pre-fill form with user data
        initial_data = {
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'email': request.user.email,
            'phone': request.user.phone,
            'address': request.user.address,
            'city': request.user.city,
            'state': request.user.state,
            'country': request.user.country or 'Nigeria',
            'postal_code': request.user.postal_code,
        }
        
        form = CheckoutForm(initial=initial_data)
        
        context = {
            'form': form,
            'cart': cart,
            'paystack_public_key': settings.PAYSTACK_PUBLIC_KEY,
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        cart = get_or_create_cart(request)
        
        if cart.items.count() == 0:
            messages.error(request, 'Your cart is empty.')
            return redirect('cart')
        
        form = CheckoutForm(request.POST)
        
        if form.is_valid():
            # Create order
            order = Order.objects.create(
                user=request.user,
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
                email=form.cleaned_data['email'],
                phone=form.cleaned_data['phone'],
                address=form.cleaned_data['address'],
                city=form.cleaned_data['city'],
                state=form.cleaned_data['state'],
                country=form.cleaned_data['country'],
                postal_code=form.cleaned_data['postal_code'],
                subtotal=cart.subtotal,
                discount_amount=cart.discount_amount,
                shipping_cost=cart.shipping_cost,
                total=cart.total,
                coupon_code=cart.coupon.code if cart.coupon else '',
                customer_note=form.cleaned_data.get('note', ''),
            )
            
            # Create order items
            for cart_item in cart.items.all():
                OrderItem.objects.create(
                    order=order,
                    product=cart_item.product,
                    variation=cart_item.variation,
                    product_name=cart_item.product.name,
                    variation_name=cart_item.variation.name if cart_item.variation else '',
                    quantity=cart_item.quantity,
                    unit_price=cart_item.unit_price,
                )
                
                # Update stock
                if cart_item.product.track_stock:
                    if cart_item.variation:
                        cart_item.variation.stock_quantity -= cart_item.quantity
                        cart_item.variation.save()
                    else:
                        cart_item.product.stock_quantity -= cart_item.quantity
                        cart_item.product.save()
            
            # Create payment record
            payment = Payment.objects.create(
                order=order,
                amount=order.total,
                reference=f"CLX{order.order_number}",
            )
            
            # Store order ID in session for verification
            request.session['pending_order_id'] = order.id
            
            # Clear cart
            cart.items.all().delete()
            cart.coupon = None
            cart.save()
            
            # Initialize Paystack payment
            if settings.PAYSTACK_SECRET_KEY:
                paystack_response = self.initialize_paystack_payment(order, payment)
                if paystack_response.get('status'):
                    return redirect(paystack_response['data']['authorization_url'])
            
            # If Paystack is not configured, show order success
            messages.success(request, 'Order placed successfully!')
            return redirect('order_success', order_number=order.order_number)
        
        context = {
            'form': form,
            'cart': cart,
            'paystack_public_key': settings.PAYSTACK_PUBLIC_KEY,
        }
        return render(request, self.template_name, context)
    
    def initialize_paystack_payment(self, order, payment):
        """Initialize Paystack payment."""
        url = "https://api.paystack.co/transaction/initialize"
        headers = {
            "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "email": order.email,
            "amount": int(order.total * 100),  # Paystack expects amount in kobo
            "reference": payment.reference,
            "callback_url": f"{settings.SITE_URL}/orders/payment/verify/",
            "metadata": {
                "order_id": order.id,
                "customer_name": order.full_name,
            }
        }
        
        try:
            response = requests.post(url, headers=headers, json=data)
            return response.json()
        except Exception as e:
            return {'status': False, 'message': str(e)}


def verify_payment(request):
    """Verify Paystack payment."""
    reference = request.GET.get('reference')
    
    if not reference:
        messages.error(request, 'Payment verification failed.')
        return redirect('cart')
    
    try:
        payment = Payment.objects.get(reference=reference)
        order = payment.order
        
        # Verify with Paystack
        if settings.PAYSTACK_SECRET_KEY:
            url = f"https://api.paystack.co/transaction/verify/{reference}"
            headers = {"Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}"}
            
            response = requests.get(url, headers=headers)
            result = response.json()
            
            if result.get('status') and result['data']['status'] == 'success':
                # Update payment and order
                payment.status = 'paid'
                payment.transaction_id = result['data'].get('id', '')
                payment.save()
                
                order.payment_status = 'paid'
                order.payment_reference = reference
                order.payment_transaction_id = result['data'].get('id', '')
                from django.utils import timezone
                order.paid_at = timezone.now()
                order.status = 'confirmed'
                order.save()
                
                # Send confirmation email
                send_order_confirmation_email(order)
                
                messages.success(request, 'Payment successful! Your order has been confirmed.')
                return redirect('order_success', order_number=order.order_number)
            else:
                payment.status = 'failed'
                payment.save()
                order.payment_status = 'failed'
                order.save()
                
                messages.error(request, 'Payment verification failed. Please try again.')
                return redirect('checkout')
        
    except Payment.DoesNotExist:
        messages.error(request, 'Payment not found.')
        return redirect('cart')


class OrderSuccessView(DetailView):
    """Order success page."""
    model = Order
    template_name = 'orders/order_success.html'
    context_object_name = 'order'
    slug_url_kwarg = 'order_number'
    slug_field = 'order_number'


class OrderDetailView(LoginRequiredMixin, DetailView):
    """Order detail view."""
    model = Order
    template_name = 'orders/order_detail.html'
    context_object_name = 'order'
    slug_url_kwarg = 'order_number'
    slug_field = 'order_number'
    
    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)


def send_order_confirmation_email(order):
    """Send order confirmation email."""
    subject = f'Order Confirmation - #{order.order_number}'
    
    # Render email template
    html_message = render_to_string('emails/order_confirmation.html', {
        'order': order,
        'site_name': settings.SITE_NAME,
    })
    
    plain_message = f"""
    Thank you for your order!
    
    Order Number: {order.order_number}
    Total: ₦{order.total}
    
    We will send you another email once your order has been shipped.
    
    If you have any questions, please contact us at {settings.CONTACT_EMAIL}
    """
    
    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[order.email],
            html_message=html_message,
            fail_silently=True,
        )
    except Exception as e:
        # Log error but don't fail the order
        print(f"Failed to send order confirmation email: {e}")
