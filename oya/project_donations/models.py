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

    class Meta:
        db_table = "project_donations_outside_donor"
        verbose_name = "Outside Donor"
        verbose_name_plural = "Outside Donors"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["full_name"]),
            models.Index(fields=["invited_by"]),
            models.Index(fields=["created_at"]),
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

    DONATION_TYPE_CHOICES = [
        ("MONEY", "Money"),
        ("MATERIAL", "Material"),
        ("LABOUR", "Labour"),
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
    donation_type = models.CharField(
        max_length=10,
        choices=DONATION_TYPE_CHOICES,
        default="MONEY",
        db_index=True,
        verbose_name="Donation Type"
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
    income = models.OneToOneField(
        "finance.Income",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="project_donation",
        verbose_name="Linked Income Record"
    )
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name="Amount",
        help_text="Required for Money donations."
    )
    receipt = models.FileField(
        upload_to="donations/receipts/%Y/%m/",
        blank=True,
        null=True,
        verbose_name="Receipt"
    )

    # ─── MATERIAL DONATION FIELDS ───
    material_name = models.CharField(max_length=255, blank=True, verbose_name="Material Name")
    quantity = models.CharField(max_length=100, blank=True, verbose_name="Quantity")

    # ─── LABOUR DONATION FIELDS ───
    labour_type = models.CharField(max_length=255, blank=True, verbose_name="Labour Type")
    number_of_days = models.PositiveIntegerField(null=True, blank=True, verbose_name="Number of Days")

    # ─── SHARED MATERIAL / LABOUR FIELDS ───
    estimated_value = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name="Estimated Value",
        help_text="Optional. Informational only unless treasury recording is enabled for Material."
    )
    remarks = models.TextField(blank=True, verbose_name="Remarks")
    update_treasury = models.BooleanField(
        default=False,
        verbose_name="Update Treasury?",
        help_text="Material donations only: if enabled, the estimated value is recorded as income."
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
            models.Index(fields=["donation_type"]),
            models.Index(fields=["invited_by"]),
        ]

    def __str__(self):
        donor = self.member or self.outside_donor or "Anonymous"
        if self.donation_type == "MONEY":
            return f"₦{self.amount:,.2f} from {donor} for {self.project.title}"
        elif self.donation_type == "MATERIAL":
            return f"{self.material_name} ({self.quantity}) from {donor} for {self.project.title}"
        return f"{self.labour_type} labour from {donor} for {self.project.title}"

    @property
    def donation_type_badge_class(self):
        return {
            "MONEY": "badge-success",
            "MATERIAL": "badge-info",
            "LABOUR": "badge-warning",
        }.get(self.donation_type, "badge-secondary")

    @property
    def display_value(self):
        """Human-readable value regardless of donation type, for donation history tables."""
        if self.donation_type == "MONEY":
            return f"₦{self.amount:,.2f}" if self.amount else "—"
        if self.donation_type == "MATERIAL":
            return f"{self.material_name} — {self.quantity}"
        if self.donation_type == "LABOUR":
            days = f"{self.number_of_days} day(s)" if self.number_of_days else ""
            return f"{self.labour_type} — {days}".strip(" —")
        return "—"

    def clean(self):
        if self.donor_type == "MEMBER" and not self.member:
            raise ValidationError({"member": "Please select a member for member donations."})
        if self.donor_type == "OUTSIDE" and not self.outside_donor:
            raise ValidationError({"outside_donor": "Please select an outside donor for outside donations."})
        if self.donor_type == "MEMBER" and self.outside_donor:
            raise ValidationError({"outside_donor": "Outside donor should not be set for member donations."})
        if self.donor_type == "OUTSIDE" and self.member:
            raise ValidationError({"member": "Member should not be set for outside donations."})

        if self.donation_type == "MONEY":
            if not self.amount or self.amount <= 0:
                raise ValidationError({"amount": "Amount is required and must be greater than zero for Money donations."})
        elif self.donation_type == "MATERIAL":
            if not self.material_name:
                raise ValidationError({"material_name": "Material name is required for Material donations."})
            if not self.quantity:
                raise ValidationError({"quantity": "Quantity is required for Material donations."})
            if self.update_treasury and (not self.estimated_value or self.estimated_value <= 0):
                raise ValidationError({"estimated_value": "Estimated value is required to update treasury for a Material donation."})
        elif self.donation_type == "LABOUR":
            if not self.labour_type:
                raise ValidationError({"labour_type": "Labour type is required for Labour donations."})
            if not self.number_of_days:
                raise ValidationError({"number_of_days": "Number of days is required for Labour donations."})
            # Labour never updates treasury, regardless of any stray flag value.
            self.update_treasury = False

    def save(self, *args, **kwargs):
        self.clean()
        # Auto-set invited_by for outside donors from their profile
        if self.donor_type == "OUTSIDE" and self.outside_donor and not self.invited_by:
            self.invited_by = self.outside_donor.invited_by
        super().save(*args, **kwargs)

class Pledge(BaseModel):
    """
    A commitment by a member to donate a specific amount to a project,
    to be paid immediately or over time via one or more PledgePayments
    (Feature 6).
    """

    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("PARTIALLY_PAID", "Partially Paid"),
        ("COMPLETED", "Completed"),
        ("CANCELLED", "Cancelled"),
    ]

    member = models.ForeignKey(
        "members.Member",
        on_delete=models.PROTECT,
        related_name="pledges",
        verbose_name="Member"
    )
    project = models.ForeignKey(
        "projects.Project",
        on_delete=models.CASCADE,
        related_name="pledges",
        verbose_name="Project"
    )
    pledged_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        verbose_name="Pledged Amount"
    )
    due_date = models.DateField(null=True, blank=True, verbose_name="Due Date")
    notes = models.TextField(blank=True, verbose_name="Notes")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="PENDING",
        db_index=True,
        verbose_name="Status"
    )
    created_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pledges_recorded",
        verbose_name="Recorded By"
    )

    class Meta:
        db_table = "project_donations_pledge"
        verbose_name = "Pledge"
        verbose_name_plural = "Pledges"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["member"]),
            models.Index(fields=["project"]),
            models.Index(fields=["status"]),
            models.Index(fields=["due_date"]),
        ]

    def __str__(self):
        return f"₦{self.pledged_amount:,.2f} pledge by {self.member} for {self.project.title}"

    def clean(self):
        if self.pledged_amount is not None and self.pledged_amount <= 0:
            raise ValidationError({"pledged_amount": "Pledged amount must be greater than zero."})

    @property
    def total_paid(self):
        from django.db.models import Sum
        return self.payments.aggregate(total=Sum("amount"))["total"] or Decimal("0")

    @property
    def outstanding_balance(self):
        return max(self.pledged_amount - self.total_paid, Decimal("0"))

    @property
    def is_overdue(self):
        return bool(
            self.due_date
            and self.due_date < timezone.now().date()
            and self.status not in ("COMPLETED", "CANCELLED")
        )

    def recalculate_status(self):
        """Recompute status from actual payments. Never overrides CANCELLED."""
        if self.status == "CANCELLED":
            return
        total = self.total_paid
        if total <= 0:
            new_status = "PENDING"
        elif total < self.pledged_amount:
            new_status = "PARTIALLY_PAID"
        else:
            new_status = "COMPLETED"
        if new_status != self.status:
            Pledge.objects.filter(pk=self.pk).update(status=new_status)
            self.status = new_status


class PledgePayment(models.Model):
    """
    A single payment (partial or full) against a Pledge (Feature 7).
    Each payment automatically creates a linked, confirmed money Donation
    (which in turn syncs to Finance via the existing Donation treasury
    signal) — this reuses the single existing accounting pipeline instead
    of duplicating it, satisfying Feature 8's "prevent duplicate
    accounting" requirement.
    """

    id = models.BigAutoField(primary_key=True)
    pledge = models.ForeignKey(
        Pledge,
        on_delete=models.CASCADE,
        related_name="payments",
        verbose_name="Pledge"
    )
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        verbose_name="Payment Amount"
    )
    payment_date = models.DateField(default=timezone.now, verbose_name="Payment Date")
    payment_method = models.CharField(
        max_length=20,
        choices=Donation.PAYMENT_METHOD_CHOICES,
        default="CASH",
        verbose_name="Payment Method"
    )
    reference_number = models.CharField(max_length=255, blank=True, verbose_name="Reference Number")
    notes = models.TextField(blank=True, verbose_name="Notes")
    recorded_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pledge_payments_recorded",
        verbose_name="Recorded By"
    )
    donation = models.OneToOneField(
        Donation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="source_pledge_payment",
        verbose_name="Linked Donation Record"
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "project_donations_pledge_payment"
        verbose_name = "Pledge Payment"
        verbose_name_plural = "Pledge Payments"
        ordering = ["-payment_date", "-created_at"]
        indexes = [
            models.Index(fields=["pledge"]),
            models.Index(fields=["payment_date"]),
        ]

    def __str__(self):
        return f"₦{self.amount:,.2f} payment on pledge #{self.pledge_id}"

    def clean(self):
        if self.amount is not None and self.amount <= 0:
            raise ValidationError({"amount": "Payment amount must be greater than zero."})
        if self.pledge_id and self.pledge.status == "CANCELLED":
            raise ValidationError("Cannot record a payment against a cancelled pledge.")
