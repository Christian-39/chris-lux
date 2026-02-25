"""
Cart views for Chris Lux.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.views import View

from chris_lux.products.models import Product, Variation
from .models import Cart, CartItem
from .utils import get_or_create_cart


class CartView(View):
    """Cart detail view."""
    template_name = 'cart/cart.html'
    
    def get(self, request):
        cart = get_or_create_cart(request)
        return render(request, self.template_name, {'cart': cart})


@require_POST
def add_to_cart(request):
    """Add item to cart via AJAX."""
    product_id = request.POST.get('product_id')
    variation_id = request.POST.get('variation_id')
    quantity = int(request.POST.get('quantity', 1))
    
    if not product_id:
        return JsonResponse({'success': False, 'message': 'Product ID is required.'})
    
    try:
        product = Product.objects.get(id=product_id, is_active=True)
    except Product.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Product not found.'})
    
    # Check if product has variations and one is selected
    if product.has_variations and not variation_id:
        return JsonResponse({
            'success': False,
            'message': 'Please select a variation.'
        })
    
    variation = None
    if variation_id:
        try:
            variation = Variation.objects.get(id=variation_id, product=product, is_active=True)
        except Variation.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Variation not found.'})
    
    # Get or create cart
    cart = get_or_create_cart(request)
    
    # Check if item already exists in cart
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        variation=variation,
        defaults={'quantity': quantity}
    )
    
    if not created:
        cart_item.quantity += quantity
        cart_item.save()
    
    return JsonResponse({
        'success': True,
        'message': f'{product.name} added to cart.',
        'cart_count': cart.item_count,
        'cart_total': float(cart.total)
    })


@require_POST
def update_cart_item(request):
    """Update cart item quantity via AJAX."""
    item_id = request.POST.get('item_id')
    quantity = int(request.POST.get('quantity', 1))
    
    if not item_id:
        return JsonResponse({'success': False, 'message': 'Item ID is required.'})
    
    try:
        cart_item = CartItem.objects.get(id=item_id, cart=get_or_create_cart(request))
    except CartItem.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Cart item not found.'})
    
    if quantity <= 0:
        cart_item.delete()
        message = 'Item removed from cart.'
    else:
        cart_item.quantity = quantity
        cart_item.save()
        message = 'Cart updated.'
    
    cart = get_or_create_cart(request)
    
    return JsonResponse({
        'success': True,
        'message': message,
        'cart_count': cart.item_count,
        'cart_subtotal': float(cart.subtotal),
        'cart_total': float(cart.total),
        'item_subtotal': float(cart_item.subtotal) if quantity > 0 else 0
    })


@require_POST
def remove_from_cart(request):
    """Remove item from cart via AJAX."""
    item_id = request.POST.get('item_id')
    
    if not item_id:
        return JsonResponse({'success': False, 'message': 'Item ID is required.'})
    
    try:
        cart_item = CartItem.objects.get(id=item_id, cart=get_or_create_cart(request))
        cart_item.delete()
    except CartItem.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Cart item not found.'})
    
    cart = get_or_create_cart(request)
    
    return JsonResponse({
        'success': True,
        'message': 'Item removed from cart.',
        'cart_count': cart.item_count,
        'cart_subtotal': float(cart.subtotal),
        'cart_total': float(cart.total)
    })


@require_POST
def apply_coupon(request):
    """Apply coupon to cart."""
    coupon_code = request.POST.get('coupon_code', '').strip().upper()
    
    if not coupon_code:
        messages.error(request, 'Please enter a coupon code.')
        return redirect('cart')
    
    cart = get_or_create_cart(request)
    success, message = cart.apply_coupon(coupon_code)
    
    if success:
        messages.success(request, message)
    else:
        messages.error(request, message)
    
    return redirect('cart')


def remove_coupon(request):
    """Remove coupon from cart."""
    cart = get_or_create_cart(request)
    cart.remove_coupon()
    messages.success(request, 'Coupon removed.')
    return redirect('cart')


def get_cart_summary(request):
    """Get cart summary for AJAX requests."""
    cart = get_or_create_cart(request)
    return JsonResponse({
        'cart_count': cart.item_count,
        'cart_subtotal': float(cart.subtotal),
        'cart_total': float(cart.total)
    })
