"""
Admin configuration for settingsapp.
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import SystemSettings


@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    list_display = ["association_name", "yearly_dues", "minimum_age", "past_member_age", "updated_at"]
    readonly_fields = ["updated_at", "logo_preview", "favicon_preview"]

    fieldsets = (
        ("Organization Info", {
            "fields": ("association_name", "motto", "logo", "logo_preview", "favicon", "favicon_preview")
        }),
        ("Financial Settings", {
            "fields": ("yearly_dues", "minimum_age", "past_member_age")
        }),
        ("Appearance", {
            "fields": ("primary_color", "accent_color", "theme_mode")
        }),
    )

    def logo_preview(self, obj):
        if obj.logo and obj.logo.name:
            return format_html(
                '<img src="{}" style="max-height:80px;max-width:200px;border-radius:4px;" />',
                obj.logo.url
            )
        return "No logo uploaded"
    logo_preview.short_description = "Logo Preview"

    def favicon_preview(self, obj):
        if obj.favicon and obj.favicon.name:
            return format_html(
                '<img src="{}" style="max-height:32px;max-width:32px;border-radius:2px;" />',
                obj.favicon.url
            )
        return "No favicon uploaded"
    favicon_preview.short_description = "Favicon Preview"

    def has_add_permission(self, request):
        """Prevent adding new settings instances."""
        return not SystemSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        """Prevent deleting settings."""
        return False
