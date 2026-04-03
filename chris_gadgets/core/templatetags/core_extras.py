"""
Core Template Tags and Filters
"""
from django import template
from products.models import Category, Brand
from core.models import TrustBadge

register = template.Library()


@register.simple_tag
def get_categories():
    """Get all active categories"""
    return Category.objects.filter(is_active=True, parent=None)


@register.simple_tag
def get_brands():
    """Get all active brands"""
    return Brand.objects.filter(is_active=True)


@register.simple_tag
def get_trust_badges():
    """Get all active trust badges"""
    return TrustBadge.objects.filter(is_active=True)


@register.filter
def multiply(value, arg):
    """Multiply two numbers"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0


@register.filter
def divide(value, arg):
    """Divide two numbers"""
    try:
        return float(value) / float(arg)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0


@register.filter
def percentage(value, total):
    """Calculate percentage"""
    try:
        return (float(value) / float(total)) * 100
    except (ValueError, TypeError, ZeroDivisionError):
        return 0
