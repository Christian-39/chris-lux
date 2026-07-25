"""
Views for OYA Project Donations.
"""
import logging
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count, Value, DecimalField
from django.db.models.functions import Coalesce
from django.http import JsonResponse, HttpResponse
from django.db import transaction
from django.utils import timezone
from auditlogs.services import log_action
from .models import OutsideDonor, Donation
from .forms import OutsideDonorForm, DonationForm
from .reports import (
    generate_project_fundraising_report,
    generate_donation_history_report,
    generate_member_donation_history_report,
    generate_outside_donor_statement,
)

logger = logging.getLogger("oya")


# ============================================================
# OUTSIDE DONORS
# ============================================================

@login_required
def outside_donor_list(request):
    """List all outside donors with search and pagination."""
    queryset = OutsideDonor.objects.select_related("invited_by").all()

    search_term = request.GET.get("search", "")
    if search_term:
        queryset = queryset.filter(
            Q(full_name__icontains=search_term) |
            Q(phone_number__icontains=search_term) |
            Q(occupation__icontains=search_term) |
            Q(invited_by__full_name__icontains=search_term)
        )

    paginator = Paginator(queryset, 25)
    page = request.GET.get("page", 1)
    donors = paginator.get_page(page)

    stats = {
        "total": OutsideDonor.objects.count(),
        "total_donations": Donation.objects.filter(
            status="CONFIRMED", donor_type="OUTSIDE"
        ).aggregate(total=Coalesce(Sum("amount"), Value(0, output_field=DecimalField())))["total"],
    }

    context = {
        "donors": donors,
        "search_term": search_term,
        "stats": stats,
    }
    return render(request, "project_donations/outside_donor_list.html", context)


@login_required
def outside_donor_detail(request, pk):
    """Display complete outside donor profile."""
    donor = get_object_or_404(
        OutsideDonor.objects.select_related("invited_by"),
        pk=pk
    )
    donations = Donation.objects.filter(
        outside_donor=donor
    ).select_related("project", "recorded_by").order_by("-donation_date")

    context = {
        "donor": donor,
        "donations": donations,
        "total_donations": donor.total_donations,
        "donation_count": donor.donation_count,
        "projects_supported": donor.projects_supported,
    }
    return render(request, "project_donations/outside_donor_detail.html", context)


@login_required
def outside_donor_create(request):
    """Create a new outside donor."""
    if not request.user.has_executive_access():
        messages.error(request, "Executive access required.")
        return redirect("project_donations:outside_donor_list")

    if request.method == "POST":
        form = OutsideDonorForm(request.POST, request.FILES)
        if form.is_valid():
            donor = form.save()
            log_action(
                user=request.user,
                action="CREATE",
                object_type="OutsideDonor",
                object_id=donor.id,
                ip_address=getattr(request, "client_ip", ""),
                description=f"Created outside donor: {donor.full_name}"
            )
            messages.success(
                request,
                f"Outside donor '{donor.full_name}' created successfully."
            )
            return redirect("project_donations:outside_donor_list")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = OutsideDonorForm()

    return render(request, "project_donations/outside_donor_form.html", {
        "form": form,
        "title": "Add Outside Donor",
        "action": "Create"
    })


@login_required
def outside_donor_update(request, pk):
    """Update an existing outside donor."""
    if not request.user.has_executive_access():
        messages.error(request, "Executive access required.")
        return redirect("project_donations:outside_donor_list")

    donor = get_object_or_404(OutsideDonor, pk=pk)

    if request.method == "POST":
        form = OutsideDonorForm(request.POST, request.FILES, instance=donor)
        if form.is_valid():
            donor = form.save()
            log_action(
                user=request.user,
                action="UPDATE",
                object_type="OutsideDonor",
                object_id=donor.id,
                ip_address=getattr(request, "client_ip", ""),
                description=f"Updated outside donor: {donor.full_name}"
            )
            messages.success(
                request,
                f"Outside donor '{donor.full_name}' updated successfully."
            )
            return redirect("project_donations:outside_donor_detail", pk=donor.pk)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = OutsideDonorForm(instance=donor)

    return render(request, "project_donations/outside_donor_form.html", {
        "form": form,
        "title": "Update Outside Donor",
        "action": "Update",
        "donor": donor
    })


@login_required
def outside_donor_delete(request, pk):
    """Delete an outside donor (admin only)."""
    if not request.user.has_admin_access():
        messages.error(request, "Admin access required.")
        return redirect("project_donations:outside_donor_list")

    donor = get_object_or_404(OutsideDonor, pk=pk)

    if request.method == "POST":
        name = donor.full_name
        donor.delete()
        log_action(
            user=request.user,
            action="DELETE",
            object_type="OutsideDonor",
            object_id=pk,
            ip_address=getattr(request, "client_ip", ""),
            description=f"Deleted outside donor: {name}"
        )
        messages.success(request, f"Outside donor '{name}' deleted.")
        return redirect("project_donations:outside_donor_list")

    return render(
        request,
        "project_donations/outside_donor_confirm_delete.html",
        {"donor": donor}
    )


# ============================================================
# DONATIONS
# ============================================================

@login_required
def donation_list(request):
    """List all donations with search, filter, and pagination."""
    queryset = Donation.objects.select_related(
        "project", "member", "outside_donor", "recorded_by", "invited_by"
    ).all()

    search_term = request.GET.get("search", "")
    if search_term:
        queryset = queryset.filter(
            Q(project__title__icontains=search_term) |
            Q(member__full_name__icontains=search_term) |
            Q(outside_donor__full_name__icontains=search_term) |
            Q(invited_by__full_name__icontains=search_term) |
            Q(reference_number__icontains=search_term) |
            Q(narration__icontains=search_term)
        )

    project_filter = request.GET.get("project", "")
    if project_filter:
        queryset = queryset.filter(project_id=project_filter)

    donor_type_filter = request.GET.get("donor_type", "")
    if donor_type_filter:
        queryset = queryset.filter(donor_type=donor_type_filter)

    status_filter = request.GET.get("status", "")
    if status_filter:
        queryset = queryset.filter(status=status_filter)

    paginator = Paginator(queryset, 25)
    page = request.GET.get("page", 1)
    donations = paginator.get_page(page)

    total_donations = Donation.objects.filter(status="CONFIRMED").aggregate(
        total=Coalesce(Sum("amount"), Value(0, output_field=DecimalField()))
    )["total"]

    member_total = Donation.objects.filter(
        status="CONFIRMED", donor_type="MEMBER"
    ).aggregate(
        total=Coalesce(Sum("amount"), Value(0, output_field=DecimalField()))
    )["total"]

    outside_total = Donation.objects.filter(
        status="CONFIRMED", donor_type="OUTSIDE"
    ).aggregate(
        total=Coalesce(Sum("amount"), Value(0, output_field=DecimalField()))
    )["total"]

    context = {
        "donations": donations,
        "search_term": search_term,
        "project_filter": project_filter,
        "donor_type_filter": donor_type_filter,
        "status_filter": status_filter,
        "donor_type_choices": Donation.DONOR_TYPE_CHOICES,
        "status_choices": Donation.STATUS_CHOICES,
        "total_donations": total_donations,
        "member_total": member_total,
        "outside_total": outside_total,
    }
    return render(request, "project_donations/donation_list.html", context)


@login_required
def donation_detail(request, pk):
    """Display donation details."""
    donation = get_object_or_404(
        Donation.objects.select_related(
            "project", "member", "outside_donor", "recorded_by", "invited_by"
        ),
        pk=pk
    )
    return render(request, "project_donations/donation_detail.html", {"donation": donation})


@login_required
def donation_create(request):
    """Record a new donation."""
    if not request.user.has_executive_access():
        messages.error(request, "Executive access required.")
        return redirect("project_donations:donation_list")

    if request.method == "POST":
        form = DonationForm(request.POST)
        if form.is_valid():
            donation = form.save(commit=False)
            donation.recorded_by = request.user
            donation.save()
            log_action(
                user=request.user,
                action="CREATE",
                object_type="Donation",
                object_id=donation.id,
                ip_address=getattr(request, "client_ip", ""),
                description=(
                    f"Recorded donation: ₦{donation.amount:,.2f} "
                    f"for {donation.project.title}"
                )
            )
            messages.success(request, "Donation recorded successfully.")
            return redirect("project_donations:donation_list")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = DonationForm()

    return render(request, "project_donations/donation_form.html", {
        "form": form,
        "title": "Record Donation",
        "action": "Save"
    })


@login_required
def donation_update(request, pk):
    """Update an existing donation."""
    if not request.user.has_executive_access():
        messages.error(request, "Executive access required.")
        return redirect("project_donations:donation_list")

    donation = get_object_or_404(Donation, pk=pk)

    if request.method == "POST":
        form = DonationForm(request.POST, instance=donation)
        if form.is_valid():
            donation = form.save()
            log_action(
                user=request.user,
                action="UPDATE",
                object_type="Donation",
                object_id=donation.id,
                ip_address=getattr(request, "client_ip", ""),
                description=(
                    f"Updated donation: ₦{donation.amount:,.2f} "
                    f"for {donation.project.title}"
                )
            )
            messages.success(request, "Donation updated successfully.")
            return redirect("project_donations:donation_list")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = DonationForm(instance=donation)

    return render(request, "project_donations/donation_form.html", {
        "form": form,
        "title": "Update Donation",
        "action": "Update",
        "donation": donation
    })


@login_required
def donation_delete(request, pk):
    """Delete a donation (admin only)."""
    if not request.user.has_admin_access():
        messages.error(request, "Admin access required.")
        return redirect("project_donations:donation_list")

    donation = get_object_or_404(Donation, pk=pk)

    if request.method == "POST":
        project_title = donation.project.title
        amount = donation.amount
        donation.delete()
        log_action(
            user=request.user,
            action="DELETE",
            object_type="Donation",
            object_id=pk,
            ip_address=getattr(request, "client_ip", ""),
            description=f"Deleted donation: ₦{amount:,.2f} for {project_title}"
        )
        messages.success(request, "Donation deleted.")
        return redirect("project_donations:donation_list")

    return render(
        request,
        "project_donations/donation_confirm_delete.html",
        {"donation": donation}
    )


# ============================================================
# REPORTS
# ============================================================

@login_required
def project_fundraising_report(request, project_id):
    """Generate PDF report for project fundraising summary."""
    if not request.user.has_executive_access():
        messages.error(request, "Executive access required.")
        return redirect("projects:project_detail", pk=project_id)

    from projects.models import Project
    project = get_object_or_404(Project, pk=project_id)

    pdf = generate_project_fundraising_report(project)
    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = (
        f'attachment; filename="fundraising_report_{project.id}.pdf"'
    )
    return response


@login_required
def outside_donor_statement_pdf(request, pk):
    """Generate PDF statement for an outside donor."""
    if not request.user.has_executive_access():
        messages.error(request, "Executive access required.")
        return redirect("project_donations:outside_donor_detail", pk=pk)

    donor = get_object_or_404(OutsideDonor, pk=pk)
    pdf = generate_outside_donor_statement(donor)
    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = (
        f'attachment; filename="outside_donor_statement_{pk}.pdf"'
    )
    return response


@login_required
def member_donation_history_pdf(request, pk):
    """Generate PDF report for member donation history."""
    if not request.user.has_executive_access():
        messages.error(request, "Executive access required.")
        return redirect("members:member_detail", pk=pk)

    from members.models import Member
    member = get_object_or_404(Member, pk=pk)
    pdf = generate_member_donation_history_report(member)
    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = (
        f'attachment; filename="member_donation_history_{pk}.pdf"'
    )
    return response


@login_required
def donation_history_report(request):
    """Generate PDF report for all donation history."""
    if not request.user.has_executive_access():
        messages.error(request, "Executive access required.")
        return redirect("project_donations:donation_list")

    donations = Donation.objects.select_related(
        "project", "member", "outside_donor", "recorded_by"
    ).filter(status="CONFIRMED").order_by("-donation_date")

    pdf = generate_donation_history_report(donations)
    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="donation_history.pdf"'
    return response


# ============================================================
# AJAX ENDPOINTS
# ============================================================

@login_required
def search_outside_donors_ajax(request):
    """AJAX endpoint for outside donor auto-suggest."""
    search_term = request.GET.get("q", "").strip()
    if len(search_term) < 2:
        return JsonResponse({"results": []})

    donors = OutsideDonor.objects.filter(
        Q(full_name__icontains=search_term) |
        Q(phone_number__icontains=search_term)
    )[:10]

    results = [
        {
            "id": d.id,
            "text": f"{d.full_name} ({d.phone_number or 'No phone'})",
            "full_name": d.full_name,
            "phone": d.phone_number,
        }
        for d in donors
    ]

    return JsonResponse({"results": results})


@login_required
def get_outside_donor_inviter_ajax(request):
    """AJAX endpoint to get the default inviter for an outside donor."""
    donor_id = request.GET.get("donor_id", "")
    if not donor_id:
        return JsonResponse({"invited_by_id": None})

    try:
        donor = OutsideDonor.objects.get(pk=donor_id)
        return JsonResponse({
            "invited_by_id": donor.invited_by_id,
            "invited_by_name": donor.invited_by.full_name if donor.invited_by else ""
        })
    except OutsideDonor.DoesNotExist:
        return JsonResponse({"invited_by_id": None})
