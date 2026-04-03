"""
Core Middleware - Theme and Activity Tracking
"""
from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin


class ThemeMiddleware(MiddlewareMixin):
    """Middleware to handle theme preferences"""
    
    def process_request(self, request):
        # Set theme based on user preference or system default
        if request.user.is_authenticated:
            theme = request.user.theme_preference
        else:
            theme = request.session.get('theme', 'system')
        
        request.theme = theme


class LastActivityMiddleware(MiddlewareMixin):
    """Middleware to track user last activity"""
    
    def process_request(self, request):
        if request.user.is_authenticated:
            # Update last activity every 5 minutes to reduce DB writes
            from datetime import timedelta
            
            last_activity = request.user.last_activity
            if last_activity is None or (timezone.now() - last_activity) > timedelta(minutes=5):
                request.user.last_activity = timezone.now()
                request.user.save(update_fields=['last_activity'])
