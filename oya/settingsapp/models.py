"""
Models for OYA system settings.
"""
from django.db import models


def logo_upload_path(instance, filename):
    """Upload path for organization logo."""
    ext = filename.split('.')[-1].lower()
    return f"settings/logo.{ext}"


def favicon_upload_path(instance, filename):
    """Upload path for organization favicon."""
    ext = filename.split('.')[-1].lower()
    return f"settings/favicon.{ext}"


class SystemSettings(models.Model):
    """
    Singleton model for system-wide settings.
    Only one row should ever exist in this table.
    """

    THEME_CHOICES = [
        ("LIGHT", "Light"),
        ("DARK", "Dark"),
        ("AUTO", "Auto"),
    ]

    id = models.BigAutoField(primary_key=True)

    # Financial settings
    yearly_dues = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=5000.00,
        verbose_name="Yearly Dues"
    )

    # Membership settings
    minimum_age = models.PositiveIntegerField(
        default=18,
        verbose_name="Minimum Age"
    )
    past_member_age = models.PositiveIntegerField(
        default=56,
        verbose_name="Past Member Age"
    )

    # Appearance settings
    primary_color = models.CharField(
        max_length=7,
        default="#1a237e",
        verbose_name="Primary Color"
    )
    accent_color = models.CharField(
        max_length=7,
        default="#ff6f00",
        verbose_name="Accent Color"
    )
    theme_mode = models.CharField(
        max_length=10,
        choices=THEME_CHOICES,
        default="LIGHT",
        verbose_name="Theme Mode"
    )

    # Association info
    association_name = models.CharField(
        max_length=255,
        default="Okpo Youths Association",
        verbose_name="Association Name"
    )
    motto = models.CharField(
        max_length=100,
        default="PEACE & PROGRESS",
        verbose_name="Motto"
    )

    # Branding
    logo = models.ImageField(
        upload_to=logo_upload_path,
        blank=True,
        null=True,
        verbose_name="Organization Logo",
        help_text="Recommended: PNG with transparent background, max 2MB. Used in header, login page, and emails."
    )
    favicon = models.ImageField(
        upload_to=favicon_upload_path,
        blank=True,
        null=True,
        verbose_name="Browser Favicon",
        help_text="Recommended: 32x32 or 64x64 ICO/PNG, max 1MB. Shown in browser tab."
    )

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "settingsapp_systemsettings"
        verbose_name = "System Settings"
        verbose_name_plural = "System Settings"

    def save(self, *args, **kwargs):
        """Ensure only one instance exists."""
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Prevent deletion of the singleton instance."""
        pass

    @classmethod
    def load(cls):
        """Load the singleton instance."""
        obj, created = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return "System Settings"

    @property
    def logo_url(self):
        """Return logo URL or empty string."""
        if self.logo and self.logo.name:
            return self.logo.url
        return ""

    @property
    def favicon_url(self):
        """Return favicon URL or empty string."""
        if self.favicon and self.favicon.name:
            return self.favicon.url
        return ""
