"""
Cart utility functions.
"""

from .models import Cart


def get_or_create_cart(request):
    """Get or create cart for user or session."""
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
    else:
        session_id = request.session.session_key
        if not session_id:
            request.session.create()
            session_id = request.session.session_key
        cart, created = Cart.objects.get_or_create(session_id=session_id, user=None)
    
    return cart


def merge_carts(user, session_cart):
    """Merge session cart into user cart on login."""
    if not session_cart or session_cart.items.count() == 0:
        return
    
    user_cart, created = Cart.objects.get_or_create(user=user)
    
    for item in session_cart.items.all():
        # Check if same item exists in user cart
        existing_item = user_cart.items.filter(
            product=item.product,
            variation=item.variation
        ).first()
        
        if existing_item:
            existing_item.quantity += item.quantity
            existing_item.save()
        else:
            item.cart = user_cart
            item.save()
    
    # Delete session cart
    session_cart.delete()


def get_cart_item_count(request):
    """Get cart item count for display in header."""
    cart = get_or_create_cart(request)
    return cart.item_count
