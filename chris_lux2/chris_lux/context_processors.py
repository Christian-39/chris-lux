"""
Context processors for Chris-Lux.
"""
from settings_app.models import SiteSettings
from notifications.models import Notification
from orders.models import Cart


def site_settings(request):
    """Add site settings to all templates."""
    try:
        settings = SiteSettings.objects.first()
        if not settings:
            settings = SiteSettings.objects.create()
    except:
        settings = None
    
    return {
        'site_settings': settings,
    }


def notifications(request):
    """Add unread notifications count to all templates."""
    unread_count = 0
    recent_notifications = []
    
    if request.user.is_authenticated:
        unread_count = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).count()
        recent_notifications = Notification.objects.filter(
            user=request.user
        ).select_related('order').order_by('-created_at')[:5]
    
    return {
        'unread_notifications_count': unread_count,
        'recent_notifications': recent_notifications,
    }


def cart_count(request):
    """Add cart item count to all templates."""
    cart_items_count = 0
    cart_total = 0
    
    if request.user.is_authenticated:
        try:
            cart = Cart.objects.filter(user=request.user).first()
            if cart:
                cart_items_count = cart.items.count()
                cart_total = cart.get_total()
        except:
            pass
    else:
        # For anonymous users, use session
        cart_data = request.session.get('cart', {})
        cart_items_count = sum(item.get('quantity', 0) for item in cart_data.values())
    
    return {
        'cart_items_count': cart_items_count,
        'cart_total': cart_total,
    }
