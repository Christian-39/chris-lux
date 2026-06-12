"""
Models for OYA system settings.
"""
from django.db import models


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
