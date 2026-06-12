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
from operations.models import CaseFile, TaskForceMember, Motorcycle

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
)

logger = logging.getLogger("oya")


@login_required
def global_search_ajax(request):
    """AJAX endpoint for global search across members, users, and cases."""
    query = request.GET.get('q', '').strip()
    if len(query) < 2:
        return JsonResponse({'members': [], 'users': [], 'cases': []})
    
    # Search members
    members = Member.objects.filter(
        Q(full_name__icontains=query) |
        Q(serial_number__icontains=query) |
        Q(phone__icontains=query) |
        Q(state_or_abroad__icontains=query)
    )[:5]
    
    # Search users
    users = User.objects.filter(
        Q(full_name__icontains=query) |
        Q(serial_number__icontains=query) |
        Q(phone__icontains=query)
    )[:5]
    
    # Search cases
    cases = CaseFile.objects.filter(
        Q(title__icontains=query) |
        Q(description__icontains=query) |
        Q(status__icontains=query)
    )[:5]
    
    return JsonResponse({
        'members': [
            {
                'id': m.id,
                'full_name': m.full_name,
                'serial_number': m.serial_number,
                'status': m.status,
            }
            for m in members
        ],
        'users': [
            {
                'id': u.id,
                'full_name': u.full_name,
                'serial_number': u.serial_number,
                'role': u.get_role_display() if hasattr(u, 'get_role_display') else u.role,
            }
            for u in users
        ],
        'cases': [
            {
                'id': c.id,
                'title': c.title,
                'status': c.status,
            }
            for c in cases
        ],
    })



@login_required
def index(request):
    """Main admin/executive dashboard view with all KPIs."""
    kpis = get_dashboard_kpis()
    member_stats = get_member_statistics()
    finance_stats = get_finance_statistics()
    recent_activities = get_recent_activities()

    # NEW: Real data for dashboard components
    clan_distribution = get_clan_distribution()
    urgent_cases = get_urgent_cases()
    executives = get_current_executives()
    task_force = get_active_task_force()
    notices = get_recent_notices()

    # Role-based context
    is_admin = request.user.has_admin_access()
    is_executive = request.user.has_executive_access()

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
        "is_admin": is_admin,
        "is_executive": is_executive,
    }
    return render(request, "dashboard/admin_dashboard.html", context)


@login_required
def member_dashboard(request):
    """Member-only dashboard view."""
    kpis = get_dashboard_kpis()
    member_stats = get_member_statistics()
    recent_activities = get_recent_activities()

    # NEW: Real data for member dashboard
    clan_distribution = get_clan_distribution()
    executives = get_current_executives()
    task_force = get_active_task_force()
    notices = get_recent_notices()

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
        "recent_activities": recent_activities,
        "clan_distribution": clan_distribution,
        "executives": executives,
        "task_force": task_force,
        "notices": notices,
        "member": member,
        "contributions": contributions,
        "total_contributed": total_contributed,
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