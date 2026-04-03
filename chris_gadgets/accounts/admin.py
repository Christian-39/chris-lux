"""
Accounts Admin Configuration
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import User, Address, UserActivity, UserSession


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom User Admin"""
    
    list_display = [
        'email', 'first_name', 'last_name', 'phone_number',
        'user_type', 'is_active', 'is_verified', 'date_joined',
        'profile_preview'
    ]
    list_filter = [
        'user_type', 'is_active', 'is_verified', 'email_verified',
        'gender', 'date_joined'
    ]
    search_fields = ['email', 'first_name', 'last_name', 'phone_number']
    ordering = ['-date_joined']
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {
            'fields': (
                'first_name', 'last_name', 'phone_number',
                'profile_image', 'date_of_birth', 'gender'
            )
        }),
        ('Permissions', {
            'fields': (
                'user_type', 'is_active', 'is_staff', 'is_superuser',
                'groups', 'user_permissions'
            )
        }),
        ('Verification', {
            'fields': ('is_verified', 'email_verified', 'phone_verified')
        }),
        ('Preferences', {
            'fields': (
                'theme_preference', 'newsletter_subscribed',
                'sms_notifications', 'email_notifications', 'push_notifications'
            )
        }),
        ('Important Dates', {
            'fields': ('last_login', 'last_activity', 'date_joined')
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email', 'first_name', 'last_name',
                'password1', 'password2', 'user_type'
            ),
        }),
    )
    
    readonly_fields = ['last_login', 'last_activity', 'date_joined']
    
    def profile_preview(self, obj):
        """Display profile image preview"""
        if obj.profile_image:
            return format_html(
                '<img src="{}" style="width: 40px; height: 40px; border-radius: 50%; object-fit: cover;" />',
                obj.profile_image.url
            )
        return format_html(
            '<div style="width: 40px; height: 40px; border-radius: 50%; background: #ccc; display: flex; align-items: center; justify-content: center; font-weight: bold;">{}</div>',
            obj.initials
        )
    profile_preview.short_description = 'Profile'


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    """Address Admin"""
    
    list_display = [
        'full_name', 'user', 'address_type', 'city',
        'state', 'phone_number', 'is_default', 'is_active'
    ]
    list_filter = ['address_type', 'state', 'is_default', 'is_active']
    search_fields = [
        'full_name', 'user__email', 'user__first_name',
        'user__last_name', 'street_address', 'city'
    ]
    raw_id_fields = ['user']


@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    """User Activity Admin"""
    
    list_display = ['user', 'activity_type', 'description', 'created_at']
    list_filter = ['activity_type', 'created_at']
    search_fields = ['user__email', 'user__first_name', 'user__last_name']
    raw_id_fields = ['user']
    date_hierarchy = 'created_at'
    readonly_fields = ['user', 'activity_type', 'description', 'ip_address', 'user_agent', 'created_at']
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    """User Session Admin"""
    
    list_display = [
        'user', 'device_info', 'ip_address',
        'is_active', 'created_at', 'last_activity'
    ]
    list_filter = ['is_active', 'created_at']
    search_fields = ['user__email', 'device_info', 'ip_address']
    raw_id_fields = ['user']
    readonly_fields = [
        'user', 'session_key', 'ip_address', 'user_agent',
        'device_info', 'location', 'created_at', 'last_activity'
    ]
    
    def has_add_permission(self, request):
        return False
