from django import template

register = template.Library()

@register.filter
def index_of(value, arg):
    """
    Returns the index of a substring in a string.
    Usage: {% with current_index=status_order|index_of:order.status %}
    """
    try:
        # Splits the string 'pending,processing,shipped,delivered' into a list
        status_list = value.split(',')
        return status_list.index(arg)
    except (ValueError, AttributeError):
        return -1

@register.filter
def status_color(status):
    """Maps order status to Bootstrap color classes."""
    colors = {
        'pending': 'warning',
        'processing': 'info',
        'shipped': 'primary',
        'delivered': 'success',
        'cancelled': 'danger',
        'returned': 'secondary',
    }
    return colors.get(status, 'secondary')

@register.filter
def payment_status_color(status):
    """Maps payment status to Bootstrap color classes."""
    colors = {
        'pending': 'warning',
        'paid': 'success',
        'failed': 'danger',
        'refunded': 'info',
    }
    return colors.get(status, 'secondary')