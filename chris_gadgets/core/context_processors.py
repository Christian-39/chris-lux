"""
Core Context Processors - Global Template Variables
"""
from .models import SiteSetting
from orders.models import Cart
from products.models import Wishlist
from notifications.models import Notification


def site_settings(request):
    """Add site settings to all templates"""
    settings = SiteSetting.get_settings()
    return {
        'site_settings': settings,
        'SITE_NAME': settings.site_name,
        'SITE_CURRENCY': settings.default_currency,
    }


def cart_count(request):
    """Add cart item count to all templates"""
    count = 0
    
    if request.user.is_authenticated:
        try:
            cart = Cart.objects.get(user=request.user)
            count = cart.item_count
        except Cart.DoesNotExist:
            pass
    else:
        # Handle session-based cart
        cart_data = request.session.get('cart', {})
        count = sum(item.get('quantity', 0) for item in cart_data.values())
    
    return {'cart_count': count}


def wishlist_count(request):
    """Add wishlist count to all templates"""
    count = 0
    
    if request.user.is_authenticated:
        count = Wishlist.objects.filter(user=request.user).count()
    
    return {'wishlist_count': count}


def notification_count(request):
    """Add unread notification count to all templates"""
    count = 0
    
    if request.user.is_authenticated:
        count = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).count()
    
    return {'notification_count': count}


def theme_context(request):
    """Add theme preference to all templates"""
    theme = 'system'
    
    if hasattr(request, 'theme'):
        theme = request.theme
    elif request.user.is_authenticated:
        theme = request.user.theme_preference
    else:
        theme = request.session.get('theme', 'system')
    
    return {
        'theme': theme,
        'is_dark_mode': theme == 'dark' or (theme == 'system' and request.META.get('HTTP_SEC_CH_PREFERS_COLOR_SCHEME') == 'dark'),
    }
