"""
Models for OYA elections.
"""
from django.db import models
from django.conf import settings
from django.db.models import Sum, Q, Count
from decimal import Decimal
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


class Vote(BaseModel):
    """Vote model to track individual votes per post."""

    id = models.BigAutoField(primary_key=True)
    election = models.ForeignKey(
        Election,
        on_delete=models.CASCADE,
        related_name="vote_records",
        verbose_name="Election"
    )
    candidate = models.ForeignKey(
        Candidate,
        on_delete=models.CASCADE,
        related_name="vote_records",
        verbose_name="Candidate"
    )
    voter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="election_votes",
        verbose_name="Voter"
    )
    post = models.CharField(
        max_length=50,
        verbose_name="Post"
    )

    class Meta:
        db_table = "elections_vote"
        verbose_name = "Vote"
        verbose_name_plural = "Votes"
        ordering = ["-created_at"]
        unique_together = [["voter", "election", "post"]]

    def __str__(self):
        return f"{self.voter} voted {self.candidate.member.full_name} for {self.post}"


class HandoverLedger(BaseModel):
    """Comprehensive handover ledger for documenting executive transitions."""

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
    
    # Tenure period for auto-calculation — nullable for backward-compatible migration
    tenure_start = models.DateField(
        verbose_name="Tenure Start Date",
        help_text="Start date of this executive's tenure (for auto-calculating aggregates).",
        null=True,
        blank=True,
    )
    tenure_end = models.DateField(
        verbose_name="Tenure End Date",
        help_text="End/handover date for this executive's tenure.",
        null=True,
        blank=True,
    )

    # Physical balances being handed over
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
    
    # Finance aggregates (auto-calculated during save)
    total_income = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00,
        verbose_name="Total Income Realized",
        help_text="All non-dues income recorded during the tenure period."
    )
    total_dues = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00,
        verbose_name="Total Dues Collected",
        help_text="Dues payments recorded during the tenure period."
    )
    total_donations = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00,
        verbose_name="Total Project Donations",
        help_text="Confirmed project donations received during the tenure period."
    )
    taskforce_revenue = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00,
        verbose_name="Taskforce Revenue",
        help_text="Fines/revenue from resolved case files during the tenure period."
    )
    total_expenses = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00,
        verbose_name="Total Expenses",
        help_text="Expenses recorded during the tenure period."
    )
    
    # Operations aggregates
    taskforce_total = models.PositiveIntegerField(default=0, verbose_name="Taskforce Total")
    taskforce_active = models.PositiveIntegerField(default=0, verbose_name="Taskforce Active")
    taskforce_inactive = models.PositiveIntegerField(default=0, verbose_name="Taskforce Inactive")
    
    motorcycle_total = models.PositiveIntegerField(default=0, verbose_name="Motorcycles Total")
    motorcycle_excellent = models.PositiveIntegerField(default=0, verbose_name="Motorcycles Excellent")
    motorcycle_needs_service = models.PositiveIntegerField(default=0, verbose_name="Motorcycles Needs Service")
    motorcycle_grounded = models.PositiveIntegerField(default=0, verbose_name="Motorcycles Grounded")
    
    cases_total = models.PositiveIntegerField(default=0, verbose_name="Cases Total")
    cases_open = models.PositiveIntegerField(default=0, verbose_name="Cases Open (Unattended)")
    cases_in_progress = models.PositiveIntegerField(default=0, verbose_name="Cases In Progress (Ongoing)")
    cases_resolved = models.PositiveIntegerField(default=0, verbose_name="Cases Resolved")
    
    # Projects aggregates
    projects_completed = models.PositiveIntegerField(default=0, verbose_name="Projects Completed")
    projects_at_hand = models.PositiveIntegerField(default=0, verbose_name="Projects At Hand (Ongoing)")
    projects_future = models.PositiveIntegerField(default=0, verbose_name="Projects Future/Planned")
    
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
        """Physical balance being handed over (bank + cash)."""
        return self.bank_balance + self.cash_balance
    
    @property
    def net_financial_position(self):
        """Net position: all revenue - expenses + physical balance."""
        return self.total_income + self.total_dues + self.total_donations + self.taskforce_revenue - self.total_expenses + self.total_balance
    
    @property
    def total_revenue(self):
        """Total revenue realized during tenure."""
        return self.total_income + self.total_dues + self.total_donations + self.taskforce_revenue
    
    def recalculate_aggregates(self):
        """
        Recalculate all auto-aggregated fields based on tenure dates.
        Call this before saving. Skips if tenure dates are not set.
        """
        from finance.models import Income, Expense, DuesPayment
        from project_donations.models import Donation as ProjectDonation
        from operations.models import TaskForceMember, Motorcycle, CaseFile
        from projects.models import Project
        from django.db.models import Q
        
        # Guard: skip auto-calculation if tenure dates aren't set yet
        if not self.tenure_start or not self.tenure_end:
            return
        
        start = self.tenure_start
        end = self.tenure_end
        
        # ─── FINANCE ───
        # Income (non-dues, non-project-donation)
        income_agg = Income.objects.filter(
            created_at__date__gte=start,
            created_at__date__lte=end
        ).exclude(income_type__in=["DUES", "PROJECT_DONATION"]).aggregate(total=Sum("amount"))
        self.total_income = income_agg["total"] or Decimal("0")
        
        # Dues
        dues_agg = DuesPayment.objects.filter(
            created_at__date__gte=start,
            created_at__date__lte=end
        ).aggregate(total=Sum("amount_paid"))
        self.total_dues = dues_agg["total"] or Decimal("0")
        
        # Project donations
        donation_agg = ProjectDonation.objects.filter(
            status="CONFIRMED",
            donation_date__gte=start,
            donation_date__lte=end
        ).aggregate(total=Sum("amount"))
        self.total_donations = donation_agg["total"] or Decimal("0")
        
        # Taskforce revenue (resolved case fines)
        taskforce_agg = CaseFile.objects.filter(
            status="RESOLVED",
            resolved_date__gte=start,
            resolved_date__lte=end
        ).aggregate(total=Sum("fine_amount"))
        self.taskforce_revenue = taskforce_agg["total"] or Decimal("0")
        
        # Expenses
        expense_agg = Expense.objects.filter(
            created_at__date__gte=start,
            created_at__date__lte=end
        ).aggregate(total=Sum("amount"))
        self.total_expenses = expense_agg["total"] or Decimal("0")
        
        # ─── OPERATIONS ───
        self.taskforce_total = TaskForceMember.objects.count()
        self.taskforce_active = TaskForceMember.objects.filter(is_active=True).count()
        self.taskforce_inactive = TaskForceMember.objects.filter(is_active=False).count()
        
        self.motorcycle_total = Motorcycle.objects.count()
        self.motorcycle_excellent = Motorcycle.objects.filter(condition="EXCELLENT").count()
        self.motorcycle_needs_service = Motorcycle.objects.filter(condition="NEEDS_SERVICE").count()
        self.motorcycle_grounded = Motorcycle.objects.filter(condition="GROUNDED").count()
        
        self.cases_total = CaseFile.objects.count()
        self.cases_open = CaseFile.objects.filter(status="OPEN").count()
        self.cases_in_progress = CaseFile.objects.filter(status="IN_PROGRESS").count()
        self.cases_resolved = CaseFile.objects.filter(status="RESOLVED").count()
        
        # ─── PROJECTS ───
        self.projects_completed = Project.objects.filter(status="FINISHED").count()
        self.projects_at_hand = Project.objects.filter(status="AT_HAND").count()
        self.projects_future = Project.objects.filter(status="FUTURE").count()
