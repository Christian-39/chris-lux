"""
Views for OYA elections.
"""
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.db import transaction
from django.db.utils import OperationalError
from auditlogs.services import log_action
from .models import Election, Candidate, HandoverLedger, Vote
from .forms import ElectionForm, CandidateForm, HandoverLedgerForm

logger = logging.getLogger("oya")


@login_required
def election_list(request):
    """List all elections with search and filter."""
    queryset = Election.objects.all()

    search_term = request.GET.get("search", "")
    if search_term:
        queryset = queryset.filter(
            Q(title__icontains=search_term) |
            Q(description__icontains=search_term)
        )

    status_filter = request.GET.get("status", "")
    if status_filter:
        queryset = queryset.filter(status=status_filter)

    paginator = Paginator(queryset, 25)
    page = request.GET.get("page", 1)
    elections = paginator.get_page(page)

    context = {
        "elections": elections,
        "search_term": search_term,
        "status_filter": status_filter,
        "status_choices": Election.STATUS_CHOICES,
    }
    return render(request, "elections/election_list.html", context)


@login_required
def election_detail(request, pk):
    """Display election details with candidates."""
    election = get_object_or_404(Election.objects.prefetch_related("candidates"), pk=pk)
    candidates = election.candidates.select_related("member").all()

    # Determine which posts the current user has already voted for in this election
    voted_posts = set()
    if request.user.is_authenticated:
        try:
            voted_posts = set(
                Vote.objects.filter(
                    voter=request.user, election=election
                ).values_list("post", flat=True)
            )
        except OperationalError:
            # Vote table may not exist yet (migration pending)
            pass

    context = {
        "election": election,
        "candidates": candidates,
        "voted_posts": voted_posts,
    }
    return render(request, "elections/election_detail.html", context)


@login_required
def election_create(request):
    """Create a new election."""
    if not request.user.has_executive_access():
        messages.error(request, "Executive access required.")
        return redirect("elections:election_list")

    if request.method == "POST":
        form = ElectionForm(request.POST)
        if form.is_valid():
            election = form.save()
            log_action(
                user=request.user,
                action="CREATE",
                object_type="Election",
                object_id=election.id,
                ip_address=getattr(request, "client_ip", ""),
                description=f"Created election: {election.title}"
            )
            messages.success(request, f"Election '{election.title}' created successfully.")
            return redirect("elections:election_list")
        else:
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = ElectionForm()

    return render(request, "elections/election_form.html", {
        "form": form,
        "title": "Create Election",
        "action": "Create"
    })


@login_required
def election_update(request, pk):
    """Update an election."""
    if not request.user.has_executive_access():
        messages.error(request, "Executive access required.")
        return redirect("elections:election_list")

    election = get_object_or_404(Election, pk=pk)

    if request.method == "POST":
        form = ElectionForm(request.POST, instance=election)
        if form.is_valid():
            form.save()
            log_action(
                user=request.user,
                action="UPDATE",
                object_type="Election",
                object_id=election.id,
                ip_address=getattr(request, "client_ip", ""),
                description=f"Updated election: {election.title}"
            )
            messages.success(request, "Election updated successfully.")
            return redirect("elections:election_list")
        else:
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = ElectionForm(instance=election)

    return render(request, "elections/election_form.html", {
        "form": form,
        "title": "Update Election",
        "action": "Update",
        "election": election
    })


@login_required
def candidate_create(request):
    """Add a candidate to an election."""
    if not request.user.has_executive_access():
        messages.error(request, "Executive access required.")
        return redirect("elections:election_list")

    election_id = request.GET.get("election")
    if request.method == "POST":
        form = CandidateForm(request.POST, request.FILES)
        if form.is_valid():
            candidate = form.save()
            log_action(
                user=request.user,
                action="CREATE",
                object_type="Candidate",
                object_id=candidate.id,
                ip_address=getattr(request, "client_ip", ""),
                description=f"Added candidate {candidate.member.full_name} for {candidate.post}"
            )
            messages.success(
                request,
                f"{candidate.member.full_name} added as candidate for {candidate.post}."
            )
            return redirect("elections:election_detail", pk=candidate.election.id)
        else:
            for error in form.errors.values():
                messages.error(request, error)
    else:
        initial = {}
        if election_id:
            initial["election"] = election_id
        form = CandidateForm(initial=initial)

    return render(request, "elections/candidate_form.html", {
        "form": form,
        "title": "Add Candidate",
        "action": "Add"
    })


@login_required
def candidate_update(request, pk):
    """Update a candidate's information."""
    if not request.user.has_executive_access():
        messages.error(request, "Executive access required.")
        return redirect("elections:election_list")

    candidate = get_object_or_404(Candidate, pk=pk)

    if request.method == "POST":
        form = CandidateForm(request.POST, request.FILES, instance=candidate)
        if form.is_valid():
            candidate = form.save()
            log_action(
                user=request.user,
                action="UPDATE",
                object_type="Candidate",
                object_id=candidate.id,
                ip_address=getattr(request, "client_ip", ""),
                description=f"Updated candidate {candidate.member.full_name} for {candidate.post}"
            )
            messages.success(
                request,
                f"Candidate {candidate.member.full_name} updated successfully."
            )
            return redirect("elections:election_detail", pk=candidate.election.id)
        else:
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = CandidateForm(instance=candidate)

    return render(request, "elections/candidate_form.html", {
        "form": form,
        "title": "Edit Candidate",
        "action": "Update",
        "candidate": candidate
    })


@login_required
def cast_vote(request, pk):
    """Cast a vote for a candidate."""
    if request.method != "POST":
        messages.error(request, "Invalid request method.")
        return redirect("elections:election_list")

    candidate = get_object_or_404(
        Candidate.objects.select_related("election", "member"), pk=pk
    )
    election = candidate.election

    if election.status != "ONGOING":
        messages.error(request, "Voting is only allowed for ongoing elections.")
        return redirect("elections:election_detail", pk=election.id)

    # Prevent voting for the same post twice in the same election
    try:
        already_voted = Vote.objects.filter(
            voter=request.user, election=election, post=candidate.post
        ).exists()
    except OperationalError:
        messages.error(request, "Voting system is temporarily unavailable. Please try again later.")
        return redirect("elections:election_detail", pk=election.id)

    if already_voted:
        messages.warning(
            request,
            f"You have already voted for {candidate.post} in this election."
        )
        return redirect("elections:election_detail", pk=election.id)

    with transaction.atomic():
        Vote.objects.create(
            voter=request.user,
            election=election,
            candidate=candidate,
            post=candidate.post,
        )
        candidate.votes += 1
        candidate.save(update_fields=["votes"])

    log_action(
        user=request.user,
        action="VOTE",
        object_type="Candidate",
        object_id=candidate.id,
        ip_address=getattr(request, "client_ip", ""),
        description=f"Voted for {candidate.member.full_name} ({candidate.post}) in {election.title}"
    )
    messages.success(
        request,
        f"Vote cast for {candidate.member.full_name} for {candidate.post}."
    )
    return redirect("elections:election_detail", pk=election.id)


# ============================================================
# HANDOVER LEDGER VIEWS
# ============================================================

@login_required
def handover_list(request):
    """List all handover ledgers with search and pagination."""
    queryset = HandoverLedger.objects.select_related("executive__member", "election").all()

    search_term = request.GET.get("search", "")
    if search_term:
        queryset = queryset.filter(
            Q(executive__member__full_name__icontains=search_term) |
            Q(executive__post__icontains=search_term) |
            Q(election__title__icontains=search_term)
        )

    paginator = Paginator(queryset, 12)
    page = request.GET.get("page", 1)
    handovers = paginator.get_page(page)

    # Summary stats — aggregate DB fields only, compute total_revenue in Python
    from django.db.models import Sum, Value
    from django.db.models.functions import Coalesce

    agg = HandoverLedger.objects.aggregate(
        total_bank=Coalesce(Sum("bank_balance"), Value(0)),
        total_cash=Coalesce(Sum("cash_balance"), Value(0)),
        sum_income=Coalesce(Sum("total_income"), Value(0)),
        sum_dues=Coalesce(Sum("total_dues"), Value(0)),
        sum_donations=Coalesce(Sum("total_donations"), Value(0)),
        sum_taskforce=Coalesce(Sum("taskforce_revenue"), Value(0)),
    )

    stats = {
        "total": HandoverLedger.objects.count(),
        "total_bank": agg["total_bank"],
        "total_cash": agg["total_cash"],
        "total_revenue": (
            agg["sum_income"] + agg["sum_dues"] +
            agg["sum_donations"] + agg["sum_taskforce"]
        ),
    }

    return render(request, "elections/handover_list.html", {
        "handovers": handovers,
        "search_term": search_term,
        "stats": stats,
    })



@login_required
def handover_detail(request, pk):
    """Display comprehensive handover details."""
    handover = get_object_or_404(
        HandoverLedger.objects.select_related("executive__member", "election"),
        pk=pk
    )
    
    # Fetch detailed records for the tenure period
    from operations.models import TaskForceMember, Motorcycle, CaseFile
    from projects.models import Project
    from project_donations.models import Donation as ProjectDonation
    from finance.models import Income, Expense, DuesPayment
    
    start = handover.tenure_start
    end = handover.tenure_end
    
    # Operations details
    taskforce_members = TaskForceMember.objects.select_related("member").all()
    motorcycles = Motorcycle.objects.select_related("assigned_to").all()
    cases = CaseFile.objects.select_related("respondent", "created_by").all()
    
    # Finance details
    recent_income = Income.objects.filter(
        created_at__date__gte=start,
        created_at__date__lte=end
    ).exclude(income_type__in=["DUES", "PROJECT_DONATION"]).select_related("created_by", "member").order_by("-created_at")[:10]
    
    recent_expenses = Expense.objects.filter(
        created_at__date__gte=start,
        created_at__date__lte=end
    ).select_related("created_by").order_by("-created_at")[:10]
    
    recent_dues = DuesPayment.objects.filter(
        created_at__date__gte=start,
        created_at__date__lte=end
    ).select_related("member", "recorded_by").order_by("-created_at")[:10]
    
    # Project details with donations during tenure
    projects = Project.objects.all().order_by("-created_at")
    projects_with_donations = []
    for project in projects:
        donations = ProjectDonation.objects.filter(
            project=project,
            status="CONFIRMED",
            donation_date__gte=start,
            donation_date__lte=end
        ).select_related("member", "outside_donor").order_by("-donation_date")
        
        donation_total = donations.aggregate(total=Sum("amount"))["total"] or 0
        
        projects_with_donations.append({
            "project": project,
            "donations": donations[:5],
            "donation_total": donation_total,
            "donation_count": donations.count(),
        })
    
    context = {
        "handover": handover,
        "taskforce_members": taskforce_members,
        "motorcycles": motorcycles,
        "cases": cases,
        "recent_income": recent_income,
        "recent_expenses": recent_expenses,
        "recent_dues": recent_dues,
        "projects_with_donations": projects_with_donations,
    }
    return render(request, "elections/handover_detail.html", context)


@login_required
def handover_create(request):
    """Create a comprehensive handover ledger entry."""
    if not request.user.has_executive_access():
        messages.error(request, "Executive access required.")
        return redirect("elections:handover_list")

    if request.method == "POST":
        form = HandoverLedgerForm(request.POST)
        if form.is_valid():
            handover = form.save()
            log_action(
                user=request.user,
                action="CREATE",
                object_type="HandoverLedger",
                object_id=handover.id,
                ip_address=getattr(request, "client_ip", ""),
                description=f"Created handover ledger for {handover.executive} (₦{handover.net_financial_position:,.2f})"
            )
            messages.success(request, "Handover ledger created successfully with auto-calculated aggregates.")
            return redirect("elections:handover_detail", pk=handover.id)
        else:
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = HandoverLedgerForm()

    return render(request, "elections/handover_form.html", {
        "form": form,
        "title": "Create Handover Ledger",
        "action": "Create"
    })


@login_required
def handover_update(request, pk):
    """Update a handover ledger and recalculate aggregates."""
    if not request.user.has_executive_access():
        messages.error(request, "Executive access required.")
        return redirect("elections:handover_list")

    handover = get_object_or_404(HandoverLedger, pk=pk)

    if request.method == "POST":
        form = HandoverLedgerForm(request.POST, instance=handover)
        if form.is_valid():
            handover = form.save()
            log_action(
                user=request.user,
                action="UPDATE",
                object_type="HandoverLedger",
                object_id=handover.id,
                ip_address=getattr(request, "client_ip", ""),
                description=f"Updated handover ledger for {handover.executive}"
            )
            messages.success(request, "Handover ledger updated and aggregates recalculated.")
            return redirect("elections:handover_detail", pk=handover.id)
        else:
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = HandoverLedgerForm(instance=handover)

    return render(request, "elections/handover_form.html", {
        "form": form,
        "title": "Update Handover Ledger",
        "action": "Update",
        "handover": handover
    })


@login_required
def handover_delete(request, pk):
    """Delete a handover ledger."""
    if not request.user.has_admin_access():
        messages.error(request, "Admin access required.")
        return redirect("elections:handover_list")

    handover = get_object_or_404(HandoverLedger, pk=pk)

    if request.method == "POST":
        executive_name = str(handover.executive)
        handover.delete()
        log_action(
            user=request.user,
            action="DELETE",
            object_type="HandoverLedger",
            object_id=pk,
            ip_address=getattr(request, "client_ip", ""),
            description=f"Deleted handover ledger for {executive_name}"
        )
        messages.success(request, f"Handover ledger for {executive_name} deleted.")
        return redirect("elections:handover_list")

    return render(request, "elections/handover_confirm_delete.html", {"handover": handover})
