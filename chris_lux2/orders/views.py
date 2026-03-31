"""
Views for orders app.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import DetailView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.utils import timezone
from decimal import Decimal

from .models import Cart, CartItem, Order, OrderItem, OrderStatusHistory, Coupon
from products.models import Product


def get_or_create_cart(request):
    """Get or create cart for user or session."""
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


@login_required
def cart_view(request):
    """Display shopping cart."""
    cart = get_or_create_cart(request)
    cart_items = cart.items.select_related('product').all()
    
    return render(request, 'orders/cart.html', {
        'cart': cart,
        'cart_items': cart_items,
    })


@login_required
def add_to_cart(request, slug):
    """Add product to cart."""
    product = get_object_or_404(Product, slug=slug, is_active=True)
    
    if not product.is_in_stock:
        messages.error(request, 'Sorry, this product is out of stock.')
        return redirect('products:product_detail', slug=slug)
    
    cart = get_or_create_cart(request)
    
    quantity = int(request.POST.get('quantity', 1))
    
    # Check if item already in cart
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'quantity': quantity}
    )
    
    if not created:
        # Update quantity
        new_quantity = cart_item.quantity + quantity
        if product.track_inventory and new_quantity > product.stock_quantity:
            messages.error(
                request,
                f'Sorry, only {product.stock_quantity} items available.'
            )
            return redirect('products:product_detail', slug=slug)
        cart_item.quantity = new_quantity
        cart_item.save()
        messages.success(
            request,
            f'Updated quantity for {product.name} in your cart.'
        )
    else:
        messages.success(
            request,
            f'{product.name} has been added to your cart.'
        )
    
    # Redirect to cart or continue shopping
    next_url = request.POST.get('next', 'orders:cart')
    return redirect(next_url)


@login_required
def update_cart_item(request, item_id):
    """Update cart item quantity."""
    cart_item = get_object_or_404(CartItem, id=item_id)
    
    # Verify cart belongs to user
    if request.user.is_authenticated and cart_item.cart.user != request.user:
        messages.error(request, 'Unauthorized action.')
        return redirect('orders:cart')
    
    quantity = int(request.POST.get('quantity', 1))
    
    if quantity <= 0:
        cart_item.delete()
        messages.success(request, 'Item removed from cart.')
    else:
        product = cart_item.product
        if product.track_inventory and quantity > product.stock_quantity:
            messages.error(
                request,
                f'Sorry, only {product.stock_quantity} items available.'
            )
        else:
            cart_item.quantity = quantity
            cart_item.save()
            messages.success(request, 'Cart updated successfully.')
    
    return redirect('orders:cart')


@login_required
def remove_from_cart(request, item_id):
    """Remove item from cart."""
    cart_item = get_or_404(CartItem, id=item_id)
    
    # Verify cart belongs to user
    if request.user.is_authenticated and cart_item.cart.user != request.user:
        messages.error(request, 'Unauthorized action.')
        return redirect('orders:cart')
    
    product_name = cart_item.product.name
    cart_item.delete()
    messages.success(request, f'{product_name} removed from cart.')
    
    return redirect('orders:cart')


@login_required
def clear_cart(request):
    """Clear all items from cart."""
    cart = get_or_create_cart(request)
    cart.clear()
    messages.success(request, 'Your cart has been cleared.')
    return redirect('orders:cart')


@login_required
def checkout_view(request):
    """Display checkout page."""
    cart = get_or_create_cart(request)
    cart_items = cart.items.select_related('product').all()
    
    if not cart_items:
        messages.error(request, 'Your cart is empty.')
        return redirect('products:product_list')
    
    # Get user's saved address
    user = request.user
    
    return render(request, 'orders/checkout.html', {
        'cart': cart,
        'cart_items': cart_items,
        'user': user,
    })


@login_required
def apply_coupon(request):
    """Apply coupon code."""
    if request.method == 'POST':
        code = request.POST.get('coupon_code', '').strip()
        
        try:
            coupon = Coupon.objects.get(code__iexact=code, is_active=True)
            
            if not coupon.is_valid():
                messages.error(request, 'This coupon has expired or reached its usage limit.')
                return redirect('orders:checkout')
            
            # Store coupon in session
            request.session['applied_coupon'] = {
                'code': coupon.code,
                'discount_type': coupon.discount_type,
                'discount_value': str(coupon.discount_value),
            }
            
            messages.success(request, f'Coupon "{coupon.code}" applied successfully!')
            
        except Coupon.DoesNotExist:
            messages.error(request, 'Invalid coupon code.')
    
    return redirect('orders:checkout')


@login_required
def remove_coupon(request):
    """Remove applied coupon."""
    if 'applied_coupon' in request.session:
        del request.session['applied_coupon']
        messages.success(request, 'Coupon removed.')
    return redirect('orders:checkout')


@login_required
def place_order(request):
    """Place order."""
    if request.method != 'POST':
        return redirect('orders:checkout')
    
    cart = get_or_create_cart(request)
    cart_items = cart.items.select_related('product').all()
    
    if not cart_items:
        messages.error(request, 'Your cart is empty.')
        return redirect('products:product_list')
    
    # Get shipping details
    email = request.POST.get('email', request.user.email)
    phone = request.POST.get('phone', request.user.phone)
    
    shipping_address = request.POST.get('shipping_address', request.user.address)
    shipping_city = request.POST.get('shipping_city', request.user.city)
    shipping_state = request.POST.get('shipping_state', request.user.state)
    shipping_country = request.POST.get('shipping_country', request.user.country)
    shipping_postal_code = request.POST.get('shipping_postal_code', request.user.postal_code)
    
    shipping_method = request.POST.get('shipping_method', 'standard')
    customer_note = request.POST.get('customer_note', '')
    
    # Calculate costs
    subtotal = cart.get_total()
    
    # Shipping cost
    shipping_costs = {
        'standard': 15.00,
        'express': 25.00,
        'overnight': 50.00,
    }
    shipping_cost = shipping_costs.get(shipping_method, 15.00)
    
    # Tax (assuming 8%)
    tax = subtotal * Decimal('0.08')
    
    # Apply coupon discount
    discount = Decimal('0')
    coupon_code = None
    if 'applied_coupon' in request.session:
        coupon_data = request.session['applied_coupon']
        try:
            coupon = Coupon.objects.get(code=coupon_data['code'])
            if coupon.is_valid():
                discount = coupon.calculate_discount(subtotal)
                coupon_code = coupon.code
                coupon.uses_count += 1
                coupon.save()
        except Coupon.DoesNotExist:
            pass
    
    # Create order
    with transaction.atomic():
        order = Order.objects.create(
            user=request.user,
            subtotal=subtotal,
            shipping_cost=shipping_cost,
            tax=tax,
            discount=discount,
            shipping_method=shipping_method,
            shipping_address=shipping_address,
            shipping_city=shipping_city,
            shipping_state=shipping_state,
            shipping_country=shipping_country,
            shipping_postal_code=shipping_postal_code,
            email=email,
            phone=phone,
            customer_note=customer_note,
        )
        
        # Create order items
        for cart_item in cart_items:
            product = cart_item.product
            
            # Check stock
            if product.track_inventory:
                if cart_item.quantity > product.stock_quantity:
                    messages.error(
                        request,
                        f'Sorry, {product.name} is no longer available in the requested quantity.'
                    )
                    order.delete()
                    return redirect('orders:cart')
                
                # Reduce stock
                product.stock_quantity -= cart_item.quantity
                product.save()
            
            OrderItem.objects.create(
                order=order,
                product=product,
                product_name=product.name,
                product_sku=product.sku,
                price=product.price,
                quantity=cart_item.quantity,
            )
        
        # Clear cart
        cart.clear()
        
        # Clear coupon from session
        if 'applied_coupon' in request.session:
            del request.session['applied_coupon']
        
        # Create status history
        OrderStatusHistory.objects.create(
            order=order,
            new_status='pending_payment',
            note='Order placed, awaiting payment.',
        )
        
        # Create notification
        from notifications.models import Notification
        Notification.objects.create(
            user=request.user,
            notification_type='order',
            title='Order Placed',
            message=f'Your order {order.order_number} has been placed successfully.',
            order=order,
        )
    
    messages.success(
        request,
        f'Order placed successfully! Your order number is {order.order_number}'
    )
    
    return redirect('orders:order_confirmation', order_id=order.id)


@login_required
def order_confirmation(request, order_id):
    """Display order confirmation page."""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    return render(request, 'orders/order_confirmation.html', {
        'order': order,
    })


class OrderDetailView(LoginRequiredMixin, DetailView):
    """Display order details."""
    
    model = Order
    template_name = 'orders/order_detail.html'
    context_object_name = 'order'
    
    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).prefetch_related(
            'items', 'status_history', 'receipts'
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order = self.get_object()
        
        # Get site settings for bank details
        from settings_app.models import SiteSettings
        site_settings = SiteSettings.objects.first()
        context['site_settings'] = site_settings
        
        return context


class OrderListView(LoginRequiredMixin, ListView):
    """Display user's orders."""
    
    model = Order
    template_name = 'orders/order_list.html'
    context_object_name = 'orders'
    paginate_by = 10
    
    def get_queryset(self):
        return Order.objects.filter(
            user=self.request.user
        ).prefetch_related('items').order_by('-created_at')


@login_required
def cancel_order(request, order_id):
    """Cancel an order."""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    
    if not order.can_cancel():
        messages.error(request, 'This order cannot be cancelled.')
        return redirect('orders:order_detail', pk=order.id)
    
    old_status = order.status
    order.status = 'cancelled'
    order.save()
    
    # Restore stock
    for item in order.items.all():
        if item.product and item.product.track_inventory:
            item.product.stock_quantity += item.quantity
            item.product.save()
    
    # Create status history
    OrderStatusHistory.objects.create(
        order=order,
        old_status=old_status,
        new_status='cancelled',
        changed_by=request.user,
        note='Order cancelled by customer.',
    )
    
    # Create notification
    from notifications.models import Notification
    Notification.objects.create(
        user=request.user,
        notification_type='order',
        title='Order Cancelled',
        message=f'Your order {order.order_number} has been cancelled.',
        order=order,
    )
    
    messages.success(request, 'Order cancelled successfully.')
    return redirect('orders:order_detail', pk=order.id)


from decimal import Decimal
