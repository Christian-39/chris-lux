"""
Custom authentication backend for OYA.
"""
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.hashers import check_password
from .models import User


class SerialNumberAuthBackend(BaseBackend):
    """
    Authenticate using serial number and 6-digit PIN.
    """

    def authenticate(self, request, serial_number=None, pin=None, **kwargs):
        if serial_number is None or pin is None:
            return None
        
        try:
            user = User.objects.get(serial_number=serial_number.upper().strip())
        except User.DoesNotExist:
            return None
        
        # Check custom pin field first
        if user.pin and check_password(pin, user.pin):
            return user
        
        # Fallback: check Django's built-in password field (for superusers)
        if user.password and check_password(pin, user.password):
            return user
            
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None