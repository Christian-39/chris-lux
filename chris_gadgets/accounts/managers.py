"""
Custom User Manager
"""
from django.contrib.auth.models import BaseUserManager
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    """Custom user manager for email-based authentication"""
    
    def create_user(self, email, first_name, last_name, password=None, **extra_fields):
        """Create and save a regular user"""
        if not email:
            raise ValueError(_('The Email field must be set'))
        
        email = self.normalize_email(email)
        user = self.model(
            email=email,
            first_name=first_name,
            last_name=last_name,
            **extra_fields
        )
        
        if password:
            user.set_password(password)
        
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, first_name, last_name, password=None, **extra_fields):
        """Create and save a superuser"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('user_type', 'admin')
        extra_fields.setdefault('is_verified', True)
        extra_fields.setdefault('email_verified', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        
        return self.create_user(email, first_name, last_name, password, **extra_fields)
    
    def create_staff(self, email, first_name, last_name, password=None, **extra_fields):
        """Create and save a staff user"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('user_type', 'staff')
        extra_fields.setdefault('is_active', True)
        
        return self.create_user(email, first_name, last_name, password, **extra_fields)
    
    def active(self):
        """Return only active users"""
        return self.filter(is_active=True)
    
    def customers(self):
        """Return only customers"""
        return self.filter(user_type='customer')
    
    def admins(self):
        """Return only admins and staff"""
        return self.filter(user_type__in=['admin', 'staff'])
    
    def verified(self):
        """Return only verified users"""
        return self.filter(is_verified=True)
