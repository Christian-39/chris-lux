"""
Context processors for OYA core.
"""
from django.conf import settings
from members.models import Member

def user_member(request):
    """Add user's member record to all template contexts."""
    if request.user.is_authenticated:
        try:
            member = Member.objects.get(serial_number=request.user.serial_number)
            return {'user_member': member}
        except Member.DoesNotExist:
            return {'user_member': None}
    return {'user_member': None}


def oya_settings(request):
    """Add OYA settings to template context."""
    return {
        "OYA_SETTINGS": settings.OYA_SETTINGS,
        "CURRENCY_SYMBOL": settings.OYA_SETTINGS["CURRENCY_SYMBOL"],
    }