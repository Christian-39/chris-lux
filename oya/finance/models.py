"""
Models for OYA finance.
"""
from django.db import models
from django.core.validators import MinValueValidator
from core.models import BaseModel


class Income(BaseModel):
    """Income model for tracking association revenue."""

    id = models.BigAutoField(primary_key=True)
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
        ]

    def __str__(self):
        return f"\u20a6{self.amount:,.2f} - {self.reason}"


class Expense(BaseModel):
    """Expense model for tracking association expenditures."""

    CATEGORY_CHOICES = [
        ("ADMINISTRATIVE", "Administrative"),
        ("PROJECT", "Project"),
        ("EVENT", "Event"),
        ("MAINTENANCE", "Maintenance"),
        ( "SALARY", "Salary"),
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
        """Validate that receipt file is provided."""
        from django.core.exceptions import ValidationError
        if not self.receipt_file:
            raise ValidationError({"receipt_file": "Receipt upload is mandatory."})
