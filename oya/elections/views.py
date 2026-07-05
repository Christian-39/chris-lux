"""
Views for OYA elections.
"""
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from auditlogs.services import log_action
from .models import Election, Candidate, HandoverLedger
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

    context = {
        "election": election,
        "candidates": candidates,
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
def handover_list(request):
    """List all handover ledgers."""
    queryset = HandoverLedger.objects.select_related("executive__member", "election").all()

    paginator = Paginator(queryset, 25)
    page = request.GET.get("page", 1)
    handovers = paginator.get_page(page)

    return render(request, "elections/handover_list.html", {"handovers": handovers})


@login_required
def handover_create(request):
    """Create a handover ledger entry."""
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
                description=f"Created handover ledger for {handover.executive}"
            )
            messages.success(request, "Handover ledger created successfully.")
            return redirect("elections:handover_list")
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
