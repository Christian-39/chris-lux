"""
Custom middleware for Chris-Lux.
"""
from notifications.models import Notification


class NotificationMiddleware:
    """Middleware to mark notifications as read when visiting specific pages."""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        return response
    
    def process_view(self, request, view_func, view_args, view_kwargs):
        """Mark notifications as read when user views order details."""
        if request.user.is_authenticated:
            # Check if this is an order detail view
            if hasattr(view_func, 'view_class'):
                view_name = view_func.view_class.__name__
                if view_name == 'OrderDetailView' and 'pk' in view_kwargs:
                    order_id = view_kwargs['pk']
                    # Mark notifications for this order as read
                    Notification.objects.filter(
                        user=request.user,
                        order_id=order_id,
                        is_read=False
                    ).update(is_read=True)
        return None
