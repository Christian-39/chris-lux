"""
Models for OYA elections.
"""
from django.db import models
from core.models import BaseModel


class Election(BaseModel):
    """Election model for managing association elections."""

    STATUS_CHOICES = [
        ("UPCOMING", "Upcoming"),
        ("ONGOING", "Ongoing"),
        ("COMPLETED", "Completed"),
        ("CANCELLED", "Cancelled"),
    ]

    id = models.BigAutoField(primary_key=True)
    title = models.CharField(max_length=255, verbose_name="Title")
    start_date = models.DateTimeField(verbose_name="Start Date")
    end_date = models.DateTimeField(verbose_name="End Date")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="UPCOMING",
        verbose_name="Status"
    )
    description = models.TextField(blank=True, verbose_name="Description")

    class Meta:
        db_table = "elections_election"
        verbose_name = "Election"
        verbose_name_plural = "Elections"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["start_date"]),
        ]

    def __str__(self):
        return self.title


class Candidate(BaseModel):
    """Candidate model for election contestants."""

    id = models.BigAutoField(primary_key=True)
    election = models.ForeignKey(
        Election,
        on_delete=models.CASCADE,
        related_name="candidates",
        verbose_name="Election"
    )
    member = models.ForeignKey(
        "members.Member",
        on_delete=models.PROTECT,
        related_name="candidacies",
        verbose_name="Member"
    )
    post = models.CharField(
        max_length=50,
        verbose_name="Post"
    )
    photo = models.ImageField(
        upload_to="elections/candidates/%Y/%m/",
        blank=True,
        null=True,
        verbose_name="Campaign Photo"
    )
    manifesto = models.TextField(blank=True, verbose_name="Manifesto")
    votes = models.PositiveIntegerField(default=0, verbose_name="Votes")

    class Meta:
        db_table = "elections_candidate"
        verbose_name = "Candidate"
        verbose_name_plural = "Candidates"
        ordering = ["-votes", "post"]
        unique_together = [["election", "member", "post"]]

    def __str__(self):
        return f"{self.member.full_name} for {self.post}"


class HandoverLedger(BaseModel):
    """Handover ledger for documenting executive transitions."""

    id = models.BigAutoField(primary_key=True)
    election = models.ForeignKey(
        Election,
        on_delete=models.PROTECT,
        related_name="handovers",
        verbose_name="Related Election",
        blank=True,
        null=True,
        help_text="The election that resulted in this executive transition."
    )
    executive = models.ForeignKey(
        "executives.Executive",
        on_delete=models.PROTECT,
        related_name="handovers",
        verbose_name="Outgoing Executive"
    )
    bank_balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00,
        verbose_name="Bank Balance"
    )
    cash_balance = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00,
        verbose_name="Cash Balance"
    )
    assets_description = models.TextField(
        blank=True,
        verbose_name="Assets Description"
    )
    notes = models.TextField(blank=True, verbose_name="Notes")

    class Meta:
        db_table = "elections_handoverledger"
        verbose_name = "Handover Ledger"
        verbose_name_plural = "Handover Ledgers"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Handover - {self.executive}"

    @property
    def total_balance(self):
        """Calculate total balance."""
        return self.bank_balance + self.cash_balance
