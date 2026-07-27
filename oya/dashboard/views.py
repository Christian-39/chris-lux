"""
Views for OYA dashboard.
"""
import logging
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from members.models import Member
from accounts.models import User
from projects.models import Project
from operations.models import CaseFile, TaskForceMember, Motorcycle
from project_donations.models import Donation as ProjectDonation, OutsideDonor
from django.db.models import Sum, Value, DecimalField
from django.db.models.functions import Coalesce

from .services import (
    get_dashboard_kpis,
    get_member_statistics,
    get_finance_statistics,
    get_recent_activities,
    get_clan_distribution,
    get_urgent_cases,
    get_current_executives,
    get_active_task_force,
    get_recent_notices,
    get_member_contributions,
    get_income_expense_trend,
)

logger = logging.getLogger("oya")


@login_required
def global_search_ajax(request):
    """AJAX endpoint for global search across all OYA modules including project donations."""
    query = request.GET.get("q", "").strip()
    if len(query) < 2:
        return JsonResponse({
            "members": [],
            "users": [],
            "cases": [],
            "outside_donors": [],
            "donations": [],
        })

    # ─── MEMBERS ───
    members = Member.objects.filter(
        Q(full_name__icontains=query) |
        Q(serial_number__icontains=query) |
        Q(phone__icontains=query) |
        Q(state_or_abroad__icontains=query)
    )[:5]

    # ─── USERS ───
    users = User.objects.filter(
        Q(full_name__icontains=query) |
        Q(serial_number__icontains=query) |
        Q(phone__icontains=query)
    )[:5]

    # ─── CASES ───
    cases = CaseFile.objects.filter(
        Q(title__icontains=query) |
        Q(description__icontains=query) |
        Q(status__icontains=query)
    )[:5]

    # ─── OUTSIDE DONORS ───
    from project_donations.models import OutsideDonor
    outside_donors = OutsideDonor.objects.filter(
        Q(full_name__icontains=query) | Q(phone_number__icontains=query)
    ).select_related("invited_by")[:5]

    # ─── DONATIONS ───
    from project_donations.models import Donation
    donations = Donation.objects.filter(
        Q(reference_number__icontains=query) |
        Q(narration__icontains=query) |
        Q(project__title__icontains=query) |
        Q(member__full_name__icontains=query) |
        Q(outside_donor__full_name__icontains=query) |
        Q(invited_by__full_name__icontains=query)
    ).select_related("project", "member", "outside_donor", "invited_by")[:5]

    return JsonResponse({
        "members": [
            {
                "id": m.id,
                "full_name": m.full_name,
                "serial_number": m.serial_number,
                "status": m.status,
            }
            for m in members
        ],
        "users": [
            {
                "id": u.id,
                "full_name": u.full_name,
                "serial_number": u.serial_number,
                "role": u.get_role_display() if hasattr(u, "get_role_display") else u.role,
            }
            for u in users
        ],
        "cases": [
            {
                "id": c.id,
                "title": c.title,
                "status": c.status,
            }
            for c in cases
        ],
        "outside_donors": [
            {
                "id": d.id,
                "full_name": d.full_name,
                "phone_number": d.phone_number,
                "invited_by": d.invited_by.full_name if d.invited_by else None,
            }
            for d in outside_donors
        ],
        "donations": [
            {
                "id": d.id,
                "amount": float(d.amount),
                "project": d.project.title if d.project else None,
                "donor_type": d.get_donor_type_display(),
                "donor_name": (
                    d.member.full_name if d.member
                    else d.outside_donor.full_name if d.outside_donor
                    else "Anonymous"
                ),
                "donation_date": d.donation_date.strftime("%Y-%m-%d"),
                "status": d.get_status_display(),
            }
            for d in donations
        ],
    })


@login_required
def financial_trend_ajax(request):
    """AJAX endpoint to return income vs expenses trend data as JSON."""
    from datetime import datetime
    year_param = request.GET.get("year")
    try:
        year = int(year_param) if year_param else None  # None = auto-detect
    except ValueError:
        year = None

    trend_data = get_income_expense_trend(year=year)
    return JsonResponse(trend_data)



@login_required
def index(request):
    """Main admin/executive dashboard view with all KPIs."""
    kpis = get_dashboard_kpis()
    member_stats = get_member_statistics()
    finance_stats = get_finance_statistics()

    # Merge confirmed project donations into dashboard finance stats
    total_project_donations = ProjectDonation.objects.filter(
        status="CONFIRMED"
    ).aggregate(
        total=Coalesce(Sum("amount"), Value(0, output_field=DecimalField()))
    )["total"]

    if isinstance(finance_stats, dict):
        finance_stats["total_project_donations"] = total_project_donations
        if "total_income" in finance_stats:
            finance_stats["total_income"] = finance_stats["total_income"] + total_project_donations
        if "treasury_balance" in finance_stats:
            finance_stats["treasury_balance"] = finance_stats["treasury_balance"] + total_project_donations

    recent_activities = get_recent_activities()

    # Real data for dashboard components
    clan_distribution = get_clan_distribution()
    urgent_cases = get_urgent_cases()
    executives = get_current_executives()
    task_force = get_active_task_force()
    notices = get_recent_notices()

    # Financial trend data for charts - auto-detects year with data
    trend_data = get_income_expense_trend()

    # Role-based context
    is_admin = request.user.has_admin_access()
    is_executive = request.user.has_executive_access()

    # ─── FIX: Project donation KPIs for admin dashboard ───
    total_project_donations = ProjectDonation.objects.filter(status="CONFIRMED").aggregate(
        total=Coalesce(Sum("amount"), Value(0, output_field=DecimalField()))
    )["total"]

    context = {
        "kpis": kpis,
        "member_stats": member_stats,
        "finance_stats": finance_stats,
        "recent_activities": recent_activities,
        "clan_distribution": clan_distribution,
        "urgent_cases": urgent_cases,
        "executives": executives,
        "task_force": task_force,
        "notices": notices,
        "trend_data": trend_data,
        "is_admin": is_admin,
        "is_executive": is_executive,
        # Project donations
        "total_project_donations": total_project_donations,
        "active_fundraising_projects": Project.objects.filter(
            enable_fundraising=True, fundraising_status="ACTIVE"
        ).count(),
        "total_outside_donors": OutsideDonor.objects.count(),
        "total_raised_through_invitees": ProjectDonation.objects.filter(
            status="CONFIRMED", invited_by__isnull=False
        ).aggregate(total=Coalesce(Sum("amount"), Value(0, output_field=DecimalField())))["total"],
    }
    return render(request, "dashboard/admin_dashboard.html", context)


@login_required
def member_dashboard(request):
    """Member-only dashboard view."""
    kpis = get_dashboard_kpis()
    member_stats = get_member_statistics()

    # Merge confirmed project donations into dashboard finance stats
    total_project_donations = ProjectDonation.objects.filter(
        status="CONFIRMED"
    ).aggregate(
        total=Coalesce(Sum("amount"), Value(0, output_field=DecimalField()))
    )["total"]

    if isinstance(finance_stats, dict):
        finance_stats["total_project_donations"] = total_project_donations
        if "total_income" in finance_stats:
            finance_stats["total_income"] = finance_stats["total_income"] + total_project_donations
        if "treasury_balance" in finance_stats:
            finance_stats["treasury_balance"] = finance_stats["treasury_balance"] + total_project_donations

    # Floor members get restricted activities (money + member add/remove only)
    member_activities = get_member_recent_activities(limit=5)

    # Real data for member dashboard
    clan_distribution = get_clan_distribution()
    executives = get_current_executives()
    task_force = get_active_task_force()
    notices = get_recent_notices()

    # Financial trend data for charts
    trend_data = get_income_expense_trend()

    # Get member-specific contribution data
    try:
        from members.models import Member
        member = Member.objects.get(user=request.user)
        contribution_data = get_member_contributions(member)
        contributions = contribution_data["contributions"]
        total_contributed = contribution_data["total_contributed"]
    except (Member.DoesNotExist, Exception):
        member = None
        contributions = []
        total_contributed = 0

    context = {
        "kpis": kpis,
        "member_stats": member_stats,
        "total_project_donations": ProjectDonation.objects.filter(status="CONFIRMED").aggregate(
            total=Coalesce(Sum("amount"), Value(0, output_field=DecimalField()))
        )["total"],
        "active_fundraising_projects": Project.objects.filter(
            enable_fundraising=True, fundraising_status="ACTIVE"
        ).count(),
        "total_outside_donors": OutsideDonor.objects.count(),
        "total_raised_through_invitees": ProjectDonation.objects.filter(
            status="CONFIRMED", invited_by__isnull=False
        ).aggregate(total=Coalesce(Sum("amount"), Value(0, output_field=DecimalField())))["total"],
        "recent_activities": member_activities,  # restricted view for members
        "clan_distribution": clan_distribution,
        "executives": executives,
        "task_force": task_force,
        "notices": notices,
        "member": member,
        "contributions": contributions,
        "total_contributed": total_contributed,
        "trend_data": trend_data,
        "is_member": True,
    }
    return render(request, "dashboard/member_dashboard.html", context)



@login_required
def admin_dashboard(request):
    """Admin-only dashboard view (redirects to main index with admin context)."""
    if not request.user.has_admin_access():
        messages.error(request, "Admin access required.")
        return render(request, "dashboard/member_dashboard.html")

    return index(request)