"""
Custom User model for OYA.
Uses serial number as username and 6-digit PIN as password.
"""
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone
from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    """Custom User model with serial number authentication."""

    ROLE_CHOICES = [
        ("ADMIN", "Admin"),
        ("EXECUTIVE", "Executive"),
        ("FLOOR_MEMBER", "Floor Member"),
    ]

    id = models.BigAutoField(primary_key=True)
    serial_number = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Serial Number"
    )
    pin = models.CharField(max_length=128, verbose_name="PIN")
    full_name = models.CharField(max_length=255, verbose_name="Full Name")
    phone = models.CharField(max_length=20, blank=True, verbose_name="Phone")
    state = models.CharField(max_length=100, blank=True, verbose_name="State")
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default="ADMIN",
        verbose_name="Role"
    )
    photo = models.ImageField(
        upload_to="users/photos/%Y/%m/",
        blank=True,
        null=True,
        verbose_name="Photo"
    )
    is_active = models.BooleanField(default=True, verbose_name="Active")
    is_staff = models.BooleanField(default=True, verbose_name="Staff")
is_superuser = models.BooleanField(default=True, verbose_name="Superuser")
    date_joined = models.DateTimeField(default=timezone.now, verbose_name="Date Joined")

    objects = UserManager()

    USERNAME_FIELD = "serial_number"
    REQUIRED_FIELDS = ["full_name", "pin"]

    class Meta:
        db_table = "accounts_user"
        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ["-date_joined"]

    def __str__(self):
        return f"{self.serial_number} - {self.full_name}"

    def get_full_name(self):
        """Return the user's full name."""
        return self.full_name or self.serial_number

    def get_short_name(self):
        """Return the user's short name."""
        return self.full_name or self.serial_number

    def set_pin(self, raw_pin):
        """Set a 6-digit PIN as password."""
        from django.contrib.auth.hashers import make_password
        self.pin = make_password(raw_pin)
        self._password = raw_pin

    def check_pin(self, raw_pin):
        """Check if the provided PIN is correct."""
        from django.contrib.auth.hashers import check_password
        return check_password(raw_pin, self.pin)

    def has_admin_access(self):
        """Check if user has admin access."""
        return self.role == "ADMIN" or self.is_superuser

    def has_executive_access(self):
        """Check if user has executive access."""
        return self.role in ["ADMIN", "EXECUTIVE"] or self.is_superuser

    def is_floor_member(self):
        """Check if user is a floor member."""
        return self.role == "FLOOR_MEMBER"

    def get_initials(self):
        """Get user initials from full name."""
        names = self.full_name.split()
        if len(names) >= 2:
            return f"{names[0][0]}{names[1][0]}".upper()
        return self.full_name[:2].upper()
    
    @property
    def member(self):
        """Get the associated Member record based on matching serial number."""
        from members.models import Member
        try:
            return Member.objects.get(serial_number=self.serial_number)
        except Member.DoesNotExist:
            return None