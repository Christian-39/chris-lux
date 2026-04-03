"""
Orders Views - Cart, Checkout, and Order Management
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.db import transaction
from django.utils import timezone
from decimal import Decimal

from .models import Cart, CartItem, Order, OrderItem, OrderStatusHistory
from products.models import Product, Coupon, FlashSale
from accounts.models import Address


def get_or_create_cart(request):
    """Get or create cart for user or session"""
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
    else:
        session_id = request.session.session_key
        if not session_id:
            request.session.create()
            session_id = request.session.session_key
        cart, created = Cart.objects.get_or_create(
            session_id=session_id,
            user=None
        )
    return cart


def cart_view(request):
    """Shopping Cart View"""
    cart = get_or_create_cart(request)
    cart_items = cart.items.select_related('product').all()
    
    # Check for flash sales and update prices
    for item in cart_items:
        flash_sale = FlashSale.objects.filter(
            product=item.product,
            is_active=True,
            starts_at__lte=timezone.now(),
            ends_at__gte=timezone.now()
        ).first()
        
        if flash_sale and flash_sale.is_live:
            item.flash_price = flash_sale.sale_price
        else:
            item.flash_price = None
    
    context = {
        'cart': cart,
        'cart_items': cart_items,
        'subtotal': cart.subtotal,
    }
    
    return render(request, 'orders/cart.html', context)


@require_POST
def add_to_cart_view(request, product_slug):
    """Add to Cart View"""
    product = get_object_or_404(Product, slug=product_slug, is_active=True)
    quantity = int(request.POST.get('quantity', 1))
    
    # Check stock
    if product.quantity < quantity:
        messages.error(request, f'Sorry, only {product.quantity} items available.')
        return redirect('products:product_detail', slug=product_slug)
    
    cart = get_or_create_cart(request)
    
    # Add or update cart item
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'quantity': quantity}
    )
    
    if not created:
        cart_item.quantity += quantity
        cart_item.save()
    
    messages.success(
        request,
        f'{product.name} has been added to your cart.'
    )
    
    next_url = request.POST.get('next')
    if next_url:
        return redirect(next_url)
    
    return redirect('orders:cart')


@require_POST
def update_cart_item_view(request, item_id):
    """Update Cart Item Quantity"""
    cart = get_or_create_cart(request)
    cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
    
    quantity = int(request.POST.get('quantity', 1))
    
    if quantity <= 0:
        cart_item.delete()
        messages.success(request, 'Item removed from cart.')
    else:
        # Check stock
        if cart_item.product.quantity < quantity:
            messages.error(
                request,
                f'Sorry, only {cart_item.product.quantity} items available.'
            )
        else:
            cart_item.quantity = quantity
            cart_item.save()
            messages.success(request, 'Cart updated.')
    
    return redirect('orders:cart')


@require_POST
def remove_from_cart_view(request, item_id):
    """Remove from Cart View"""
    cart = get_or_create_cart(request)
    cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
    cart_item.delete()
    
    messages.success(request, 'Item removed from cart.')
    return redirect('orders:cart')


def clear_cart_view(request):
    """Clear Cart View"""
    cart = get_or_create_cart(request)
    cart.clear()
    messages.success(request, 'Cart cleared.')
    return redirect('orders:cart')


@login_required
def checkout_view(request):
    """Checkout View"""
    cart = get_or_create_cart(request)
    
    if cart.item_count == 0:
        messages.error(request, 'Your cart is empty.')
        return redirect('orders:cart')
    
    # Get user's addresses
    addresses = request.user.addresses.filter(is_active=True)
    default_address = addresses.filter(is_default=True).first()
    
    # Calculate totals
    subtotal = cart.subtotal
    shipping_cost = Decimal('2000')  # Default shipping
    if subtotal >= 50000:
        shipping_cost = Decimal('0')  # Free shipping over ₦50,000
    
    # Check for coupon
    coupon_code = request.session.get('coupon_code')
    discount_amount = Decimal('0')
    coupon = None
    
    if coupon_code:
        try:
            coupon = Coupon.objects.get(
                code=coupon_code,
                is_active=True,
                valid_from__lte=timezone.now(),
                valid_until__gte=timezone.now()
            )
            if coupon.is_valid:
                discount_amount = coupon.calculate_discount(subtotal)
        except Coupon.DoesNotExist:
            del request.session['coupon_code']
    
    total = subtotal + shipping_cost - discount_amount
    
    if request.method == 'POST':
        address_id = request.POST.get('address_id')
        customer_note = request.POST.get('customer_note', '')
        
        if not address_id:
            messages.error(request, 'Please select a delivery address.')
            return redirect('orders:checkout')
        
        address = get_object_or_404(Address, id=address_id, user=request.user)
        
        # Create order
        with transaction.atomic():
            order = Order.objects.create(
                user=request.user,
                status='pending',
                payment_status='pending',
                shipping_name=address.full_name,
                shipping_phone=address.phone_number,
                shipping_address=address.street_address,
                shipping_city=address.city,
                shipping_state=address.state,
                shipping_lga=address.lga,
                shipping_landmark=address.landmark,
                shipping_postal_code=address.postal_code,
                subtotal=subtotal,
                shipping_cost=shipping_cost,
                discount_amount=discount_amount,
                total=total,
                coupon=coupon,
                coupon_code=coupon_code,
                customer_note=customer_note
            )
            
            # Create order items
            for cart_item in cart.items.all():
                product = cart_item.product
                
                # Check for flash sale price
                flash_sale = FlashSale.objects.filter(
                    product=product,
                    is_active=True,
                    starts_at__lte=timezone.now(),
                    ends_at__gte=timezone.now()
                ).first()
                
                if flash_sale and flash_sale.is_live:
                    unit_price = flash_sale.sale_price
                else:
                    unit_price = product.price
                
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    product_name=product.name,
                    product_sku=product.sku,
                    product_image=product.primary_image.image.url if product.primary_image else None,
                    quantity=cart_item.quantity,
                    unit_price=unit_price,
                    total_price=unit_price * cart_item.quantity
                )
                
                # Update product stock
                product.quantity -= cart_item.quantity
                product.sales_count += cart_item.quantity
                product.save()
            
            # Clear cart
            cart.clear()
            
            # Clear coupon
            if 'coupon_code' in request.session:
                del request.session['coupon_code']
            
            # Update coupon usage
            if coupon:
                coupon.usage_count += 1
                coupon.save()
            
            messages.success(
                request,
                f'Order placed successfully! Your order number is {order.order_number}.'
            )
            
            return redirect('payments:payment', order_id=order.id)
    
    context = {
        'cart': cart,
        'addresses': addresses,
        'default_address': default_address,
        'subtotal': subtotal,
        'shipping_cost': shipping_cost,
        'discount_amount': discount_amount,
        'total': total,
        'coupon_code': coupon_code,
    }
    
    return render(request, 'orders/checkout.html', context)


@login_required
def apply_coupon_view(request):
    """Apply Coupon View"""
    if request.method == 'POST':
        code = request.POST.get('coupon_code', '').strip()
        
        if not code:
            messages.error(request, 'Please enter a coupon code.')
            return redirect('orders:checkout')
        
        try:
            coupon = Coupon.objects.get(
                code=code,
                is_active=True
            )
            
            if not coupon.is_valid:
                messages.error(request, 'This coupon has expired or reached its usage limit.')
                return redirect('orders:checkout')
            
            # Store coupon in session
            request.session['coupon_code'] = code
            messages.success(request, f'Coupon "{code}" applied successfully!')
            
        except Coupon.DoesNotExist:
            messages.error(request, 'Invalid coupon code.')
    
    return redirect('orders:checkout')


@login_required
def remove_coupon_view(request):
    """Remove Coupon View"""
    if 'coupon_code' in request.session:
        del request.session['coupon_code']
        messages.success(request, 'Coupon removed.')
    
    return redirect('orders:checkout')


@login_required
def order_detail_view(request, order_id):
    """Order Detail View"""
    order = get_object_or_404(
        Order.objects.select_related('payment'),
        id=order_id,
        user=request.user
    )
    
    context = {
        'order': order,
        'items': order.items.all(),
    }
    
    return render(request, 'orders/order_detail.html', context)


@login_required
def cancel_order_view(request, order_id):
    """Cancel Order View"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    if not order.can_cancel:
        messages.error(request, 'This order cannot be cancelled.')
        return redirect('orders:order_detail', order_id=order.id)
    
    if request.method == 'POST':
        reason = request.POST.get('cancellation_reason', '')
        
        order.status = 'cancelled'
        order.save()
        
        # Restore product stock
        for item in order.items.all():
            product = item.product
            product.quantity += item.quantity
            product.sales_count -= item.quantity
            product.save()
        
        # Create status history
        OrderStatusHistory.objects.create(
            order=order,
            status='cancelled',
            notes=f'Cancelled by customer. Reason: {reason}'
        )
        
        messages.success(request, 'Order cancelled successfully.')
        return redirect('accounts:order_history')
    
    return render(request, 'orders/cancel_order.html', {'order': order})


@login_required
def track_order_view(request, order_id):
    """Track Order View"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    if not order.can_track:
        messages.error(request, 'This order cannot be tracked yet.')
        return redirect('orders:order_detail', order_id=order.id)
    
    status_history = order.status_history.all()
    
    context = {
        'order': order,
        'status_history': status_history,
    }
    
    return render(request, 'orders/track_order.html', context)


# AJAX Views
@require_POST
def update_cart_quantity_ajax(request):
    """Update cart quantity via AJAX"""
    item_id = request.POST.get('item_id')
    quantity = int(request.POST.get('quantity', 1))
    
    cart = get_or_create_cart(request)
    
    try:
        cart_item = CartItem.objects.get(id=item_id, cart=cart)
        
        if quantity <= 0:
            cart_item.delete()
            item_total = 0
        else:
            if cart_item.product.quantity < quantity:
                return JsonResponse({
                    'success': False,
                    'message': f'Only {cart_item.product.quantity} items available'
                })
            
            cart_item.quantity = quantity
            cart_item.save()
            
            # Check for flash sale
            flash_sale = FlashSale.objects.filter(
                product=cart_item.product,
                is_active=True,
                starts_at__lte=timezone.now(),
                ends_at__gte=timezone.now()
            ).first()
            
            if flash_sale and flash_sale.is_live:
                price = flash_sale.sale_price
            else:
                price = cart_item.product.price
            
            item_total = price * quantity
        
        return JsonResponse({
            'success': True,
            'item_total': str(item_total),
            'cart_total': str(cart.subtotal),
            'cart_count': cart.item_count
        })
    
    except CartItem.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Item not found'
        })


@require_POST
def remove_cart_item_ajax(request):
    """Remove cart item via AJAX"""
    item_id = request.POST.get('item_id')
    
    cart = get_or_create_cart(request)
    
    try:
        cart_item = CartItem.objects.get(id=item_id, cart=cart)
        cart_item.delete()
        
        return JsonResponse({
            'success': True,
            'cart_total': str(cart.subtotal),
            'cart_count': cart.item_count
        })
    
    except CartItem.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Item not found'
        })
