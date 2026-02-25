"""
Cart context processors.
"""

from .utils import get_or_create_cart


def cart_context(request):
    """Add cart to all templates."""
    cart = get_or_create_cart(request)
    return {
        'cart': cart,
        'cart_count': cart.item_count,
    }
