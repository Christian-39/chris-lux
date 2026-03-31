"""
Admin configuration for users app.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom User admin."""
    
    list_display = [
        'username', 'email', 'first_name', 'last_name',
        'phone', 'is_staff', 'is_active', 'created_at'
    ]
    list_filter = ['is_staff', 'is_active', 'is_admin', 'created_at']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'phone']
    ordering = ['-created_at']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('phone', 'profile_image', 'bio', 'date_of_birth')
        }),
        ('Address', {
            'fields': ('address', 'city', 'state', 'country', 'postal_code')
        }),
        ('Preferences', {
            'fields': ('dark_mode', 'email_notifications', 'sms_notifications')
        }),
        ('Role', {
            'fields': ('is_admin',)
        }),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Personal Info', {
            'fields': ('first_name', 'last_name', 'email', 'phone')
        }),
    )
