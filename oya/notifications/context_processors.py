"""
Context processors for notifications.
"""
from django.db import models as db_models


def unread_notifications(request):
    """Add unread notification count to template context."""
    if request.user.is_authenticated:
        from .models import Notification
        count = Notification.objects.filter(
            db_models.Q(recipient=request.user) | db_models.Q(is_global=True),
            is_read=False
        ).count()
        return {"unread_notification_count": count}
    return {"unread_notification_count": 0}
