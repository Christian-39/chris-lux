"""
Admin configuration for settingsapp.
"""
from django.contrib import admin
from .models import SystemSettings


@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    list_display = ["association_name", "yearly_dues", "minimum_age", "past_member_age", "updated_at"]
    readonly_fields = ["updated_at"]

    def has_add_permission(self, request):
        """Prevent adding new settings instances."""
        return not SystemSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        """Prevent deleting settings."""
        return False
