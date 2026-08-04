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

    def process_election_results(self):
        """
        Automatically applied when this election's status transitions to
        COMPLETED (see elections/signals.py):

        - For every post actually contested in this election (i.e. with at
          least one Candidate), the candidate with the highest vote count
          becomes the new current Executive for that post.
        - The previous current holder of that post (if a different member)
          is ended (is_current=False, end_date=today) — i.e. reverted to a
          regular member — UNLESS they also won a different contested post
          in this same election, in which case only their old post ends
          and their new one is created; they are not left without a post.
        - Posts not contested in this election are left completely
          untouched — this is not a "wipe the whole executive body" reset,
          only the posts actually up for election are affected.
        - A tie for the top vote count, or a post with zero votes cast, is
          left for manual resolution rather than guessed automatically.
        - A candidate's post value that doesn't match one of
          Executive.POST_CHOICES is also left for manual resolution,
          rather than silently creating an inconsistent Executive record.

        Returns a summary dict:
            {
                "winners": {post: Candidate, ...},
                "tied_posts": [post, ...],
                "no_votes_posts": [post, ...],
                "invalid_post_names": [post, ...],
                "errors": {post: error_message, ...},
            }
        """
        from django.db import transaction
        from django.utils import timezone
        from executives.models import Executive

        today = timezone.now().date()
        valid_post_values = {choice[0] for choice in Executive.POST_CHOICES}

        contested_posts = list(
            self.candidates.values_list("post", flat=True).distinct()
        )

        winners = {}
        tied_posts = []
        no_votes_posts = []
        invalid_post_names = []
        errors = {}

        for post in contested_posts:
            if post not in valid_post_values:
                invalid_post_names.append(post)
                continue

            candidates = list(
                self.candidates.filter(post=post).select_related("member").order_by("-votes")
            )
            if not candidates:
                continue

            top_votes = candidates[0].votes
            if top_votes <= 0:
                no_votes_posts.append(post)
                continue

            top_candidates = [c for c in candidates if c.votes == top_votes]
            if len(top_candidates) > 1:
                tied_posts.append(post)
                continue

            winner = top_candidates[0]

            try:
                with transaction.atomic():
                    current_holder = Executive.objects.filter(post=post, is_current=True).first()
                    if current_holder and current_holder.member_id == winner.member_id:
                        # Re-elected to the same post they already hold — no new
                        # term record needed, but re-tag them into this election's
                        # administration so handover reports group them correctly.
                        if current_holder.elected_via_id != self.id:
                            current_holder.elected_via = self
                            current_holder.save(update_fields=["elected_via", "updated_at"])
                        winners[post] = winner
                        continue

                    # Outgoing: end the previous holder of this specific post.
                    if current_holder:
                        current_holder.is_current = False
                        current_holder.end_date = today
                        current_holder.save(update_fields=["is_current", "end_date", "updated_at"])

                    # If the winner currently holds a different post, end that
                    # one too — a member holds one executive post at a time.
                    Executive.objects.filter(
                        member=winner.member, is_current=True
                    ).exclude(post=post).update(is_current=False, end_date=today)

                    Executive.objects.create(
                        member=winner.member,
                        post=post,
                        start_date=today,
                        is_current=True,
                        elected_via=self,
                    )
                winners[post] = winner
            except Exception as exc:
                # Isolated per-post: a problem with one post (e.g. a rare
                # unique_together collision on re-election to a previously
                # held, non-consecutive post) must not roll back or block
                # every other post's results.
                errors[post] = str(exc)

        return {
            "winners": winners,
            "tied_posts": tied_posts,
            "no_votes_posts": no_votes_posts,
            "invalid_post_names": invalid_post_names,
            "errors": errors,
        }


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

    # Cash physically remaining in hand at the moment of handover. Defaults
    # to ₦0.00 and is only ever edited by an administrator (enforced in
    # HandoverLedgerForm / elections.views) — everyone else sees it read-only.
    # Once set, it automatically flows into total_balance / closing balance
    # and the net financial position below.
    cash_remaining = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name="Cash Remaining",
        help_text="Cash physically remaining in hand at handover. Administrator-only field.",
    )

    class Meta:
        db_table = "elections_handoverledger"
        verbose_name = "Handover Ledger"
        verbose_name_plural = "Handover Ledgers"
        ordering = ["-created_at"]

    def __str__(self):
        return f"Handover - {self.executive}"

    @property
    def total_balance(self):
        """Physical balance being handed over (bank + cash + cash remaining)."""
        return self.bank_balance + self.cash_balance + self.cash_remaining

    @property
    def closing_balance(self):
        """Alias of total_balance — the administration's closing balance."""
        return self.total_balance
    
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
