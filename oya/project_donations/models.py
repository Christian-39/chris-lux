"""
Models for OYA Project Donations.
"""
from django.db import models, transaction
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal
from core.models import BaseModel


class OutsideDonor(BaseModel):
    """Outside donor model for non-member contributors."""

    GENDER_CHOICES = [
        ("MALE", "Male"),
        ("FEMALE", "Female"),
        ("OTHER", "Other"),
    ]

    full_name = models.CharField(max_length=255, verbose_name="Full Name")
    profile_picture = models.ImageField(
        upload_to="donors/photos/%Y/%m/",
        blank=True,
        null=True,
        verbose_name="Profile Picture"
    )
    phone_number = models.CharField(max_length=20, blank=True, verbose_name="Phone Number")
    address = models.TextField(blank=True, verbose_name="Address")
    gender = models.CharField(
        max_length=10,
        choices=GENDER_CHOICES,
        blank=True,
        verbose_name="Gender"
    )
    occupation = models.CharField(max_length=100, blank=True, verbose_name="Occupation")
    notes = models.TextField(blank=True, verbose_name="Notes")
    invited_by = models.ForeignKey(
        "members.Member",
        on_delete=models.PROTECT,
        related_name="invited_outside_donors",
        verbose_name="Invited By",
        help_text="The OYA member who introduced this donor."
    )
    date_added = models.DateTimeField(default=timezone.now, verbose_name="Date Added")

    class Meta:
        db_table = "project_donations_outside_donor"
        verbose_name = "Outside Donor"
        verbose_name_plural = "Outside Donors"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["full_name"]),
            models.Index(fields=["invited_by"]),
            models.Index(fields=["date_added"]),
        ]

    def __str__(self):
        return self.full_name

    @property
    def total_donations(self):
        from django.db.models import Sum
        return self.donations.filter(status="CONFIRMED").aggregate(
            total=Sum("amount")
        )["total"] or Decimal("0")

    @property
    def donation_count(self):
        return self.donations.filter(status="CONFIRMED").count()

    @property
    def projects_supported(self):
        return self.donations.filter(status="CONFIRMED").values("project").distinct().count()

    @property
    def profile_picture_url(self):
        if self.profile_picture:
            return self.profile_picture.url
        return ""


class Donation(BaseModel):
    """Donation model for project fundraising contributions."""

    DONOR_TYPE_CHOICES = [
        ("MEMBER", "OYA Member"),
        ("OUTSIDE", "Outside Donor"),
    ]

    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("CONFIRMED", "Confirmed"),
        ("CANCELLED", "Cancelled"),
    ]

    PAYMENT_METHOD_CHOICES = [
        ("CASH", "Cash"),
        ("BANK_TRANSFER", "Bank Transfer"),
        ("MOBILE_MONEY", "Mobile Money"),
        ("CHECK", "Check"),
        ("OTHER", "Other"),
    ]

    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.CASCADE,
        related_name="donations",
        verbose_name="Project"
    )
    donor_type = models.CharField(
        max_length=10,
        choices=DONOR_TYPE_CHOICES,
        verbose_name="Donor Type"
    )
    member = models.ForeignKey(
        "members.Member",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="project_donations",
        verbose_name="Member"
    )
    outside_donor = models.ForeignKey(
        OutsideDonor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="donations",
        verbose_name="Outside Donor"
    )
    invited_by = models.ForeignKey(
        "members.Member",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="facilitated_donations",
        verbose_name="Invited By"
    )
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        verbose_name="Amount"
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        default="CASH",
        verbose_name="Payment Method"
    )
    reference_number = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Reference Number"
    )
    narration = models.TextField(
        blank=True,
        verbose_name="Narration"
    )
    recorded_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="donations_recorded",
        verbose_name="Recorded By"
    )
    donation_date = models.DateField(
        default=timezone.now,
        verbose_name="Donation Date"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="CONFIRMED",
        verbose_name="Status"
    )

    class Meta:
        db_table = "project_donations_donation"
        verbose_name = "Donation"
        verbose_name_plural = "Donations"
        ordering = ["-donation_date", "-created_at"]
        indexes = [
            models.Index(fields=["project"]),
            models.Index(fields=["member"]),
            models.Index(fields=["outside_donor"]),
            models.Index(fields=["donation_date"]),
            models.Index(fields=["status"]),
            models.Index(fields=["donor_type"]),
            models.Index(fields=["invited_by"]),
        ]

    def __str__(self):
        donor = self.member or self.outside_donor or "Anonymous"
        return f"₦{self.amount:,.2f} from {donor} for {self.project.title}"

    def clean(self):
        if self.donor_type == "MEMBER" and not self.member:
            raise ValidationError({"member": "Please select a member for member donations."})
        if self.donor_type == "OUTSIDE" and not self.outside_donor:
            raise ValidationError({"outside_donor": "Please select an outside donor for outside donations."})
        if self.donor_type == "MEMBER" and self.outside_donor:
            raise ValidationError({"outside_donor": "Outside donor should not be set for member donations."})
        if self.donor_type == "OUTSIDE" and self.member:
            raise ValidationError({"member": "Member should not be set for outside donations."})

    def save(self, *args, **kwargs):
        self.clean()
        # Auto-set invited_by for outside donors from their profile
        if self.donor_type == "OUTSIDE" and self.outside_donor and not self.invited_by:
            self.invited_by = self.outside_donor.invited_by
        with transaction.atomic():
            super().save(*args, **kwargs)
            if self.project:
                self.project.update_fundraising_stats()

    def delete(self, *args, **kwargs):
        project = self.project
        with transaction.atomic():
            super().delete(*args, **kwargs)
            if project:
                project.update_fundraising_stats()
