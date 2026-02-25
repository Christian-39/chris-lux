"""
Context processors for Chris Lux.
"""

from django.conf import settings
from chris_lux.products.models import Category


def site_settings(request):
    """Add site settings to all templates."""
    return {
        'SITE_NAME': settings.SITE_NAME,
        'SITE_TAGLINE': settings.SITE_TAGLINE,
        'CONTACT_EMAIL': settings.CONTACT_EMAIL,
        'CONTACT_PHONE': settings.CONTACT_PHONE,
        'WHATSAPP_NUMBER': settings.WHATSAPP_NUMBER,
        'SHIPPING_FEE': settings.SHIPPING_FEE,
        'FREE_SHIPPING_THRESHOLD': settings.FREE_SHIPPING_THRESHOLD,
        'PAYSTACK_PUBLIC_KEY': settings.PAYSTACK_PUBLIC_KEY,
    }


def navigation_categories(request):
    """Add categories to navigation."""
    return {
        'nav_categories': Category.objects.filter(is_active=True, parent=None)[:6]
    }
