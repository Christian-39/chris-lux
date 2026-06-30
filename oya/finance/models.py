"""
Models for OYA finance.
"""
from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from core.models import BaseModel


class Income(BaseModel):
    """Income model for tracking association revenue."""

    INCOME_TYPE_CHOICES = [
        ("DUES", "Yearly Dues"),
        ("DONATION", "Donation / Contribution"),
        ("EVENT", "Event Fee"),
        ("OTHER", "Other"),
    ]

    id = models.BigAutoField(primary_key=True)
    income_type = models.CharField(
        max_length=20,
        choices=INCOME_TYPE_CHOICES,
        default="DONATION",
        verbose_name="Income Type",
        db_index=True,
    )
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        verbose_name="Amount"
    )
    reason = models.CharField(max_length=255, verbose_name="Reason")
    paid_by = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Paid By"
    )
    created_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="incomes_created",
        verbose_name="Created By"
    )

    class Meta:
        db_table = "finance_income"
        verbose_name = "Income"
        verbose_name_plural = "Income"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["created_at"]),
            models.Index(fields=["income_type"]),
        ]

    def __str__(self):
        return f"\u20a6{self.amount:,.2f} - {self.reason}"


class DuesPayment(BaseModel):
    """
    Tracks yearly dues payments per member.
    Platform started 2020. Dues = \u20a65,000/year (fixed).
    """
    YEARLY_DUES_AMOUNT = 5000

    id = models.BigAutoField(primary_key=True)
    member = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="dues_payments",
        verbose_name="Member",
        limit_choices_to={"is_active": True},
    )
    year = models.PositiveIntegerField(
        verbose_name="Dues Year",
        help_text="The calendar year this dues payment covers.",
        db_index=True,
    )
    amount_paid = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=YEARLY_DUES_AMOUNT,
        verbose_name="Amount Paid",
    )
    income = models.OneToOneField(
        Income,
        on_delete=models.CASCADE,
        related_name="dues_payment",
        verbose_name="Linked Income Record",
        null=True,
        blank=True,
    )
    notes = models.TextField(
        blank=True,
        verbose_name="Notes",
        help_text="e.g., 'Paid in cash at meeting', 'Bank transfer ref: XYZ'",
    )
    recorded_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="dues_recorded",
        verbose_name="Recorded By",
    )

    class Meta:
        db_table = "finance_dues_payment"
        verbose_name = "Dues Payment"
        verbose_name_plural = "Dues Payments"
        ordering = ["-year", "member__full_name"]
        unique_together = ["member", "year"]
        constraints = [
            models.CheckConstraint(
                check=models.Q(year__gte=2020),
                name="year_gte_2020",
            ),
        ]

    def __str__(self):
        return f"{self.member.get_full_name()} \u2014 {self.year} Dues"

    def clean(self):
        if self.year < 2020:
            raise ValidationError({"year": "Dues year cannot be before platform creation (2020)."})
        if self.amount_paid != self.YEARLY_DUES_AMOUNT:
            raise ValidationError({"amount_paid": f"Yearly dues must be exactly \u20a6{self.YEARLY_DUES_AMOUNT:,}."})

    @property
    def status(self):
        return "PAID" if self.amount_paid >= self.YEARLY_DUES_AMOUNT else "PARTIAL"

    @classmethod
    def get_member_debt(cls, member):
        """
        Calculate total dues debt for a member.
        Debt = (years_from_joining_to_now \u00d7 5000) \u2212 total_paid
        """
        from datetime import datetime
        current_year = datetime.now().year

        join_year = getattr(member, 'year_joined', None) or 2020
        start_year = max(join_year, 2020)

        expected_years = list(range(start_year, current_year + 1))
        total_expected = len(expected_years) * cls.YEARLY_DUES_AMOUNT

        total_paid = cls.objects.filter(
            member=member,
            year__in=expected_years
        ).aggregate(total=models.Sum("amount_paid"))["total"] or 0

        return {
            "total_expected": total_expected,
            "total_paid": total_paid,
            "debt_owed": max(total_expected - total_paid, 0),
            "years_expected": expected_years,
            "years_paid": list(cls.objects.filter(member=member).values_list("year", flat=True)),
        }


class Expense(BaseModel):
    """Expense model for tracking association expenditures."""

    CATEGORY_CHOICES = [
        ("ADMINISTRATIVE", "Administrative"),
        ("PROJECT", "Project"),
        ("EVENT", "Event"),
        ("MAINTENANCE", "Maintenance"),
        ("SALARY", "Salary"),
        ("OTHER", "Other"),
    ]

    id = models.BigAutoField(primary_key=True)
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        verbose_name="Amount"
    )
    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        verbose_name="Category"
    )
    description = models.TextField(verbose_name="Description")
    receipt_file = models.FileField(
        upload_to="finance/receipts/%Y/%m/",
        verbose_name="Receipt File"
    )
    created_by = models.ForeignKey(
        "accounts.User",
        on_delete=models.SET_NULL,
        null=True,
        related_name="expenses_created",
        verbose_name="Created By"
    )

    class Meta:
        db_table = "finance_expense"
        verbose_name = "Expense"
        verbose_name_plural = "Expenses"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["category"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"\u20a6{self.amount:,.2f} - {self.category}"

    def clean(self):
        if not self.receipt_file:
            raise ValidationError({"receipt_file": "Receipt upload is mandatory."})
