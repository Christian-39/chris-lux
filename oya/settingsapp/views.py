"""
Views for OYA system settings.
"""
import logging
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from auditlogs.services import log_request_action
from accounts.models import User
from members.models import Clan, Member
from django.db.models import Count
from .models import SystemSettings
from .forms import SystemSettingsForm

logger = logging.getLogger("oya")


@login_required
def settings_view(request):
    """View and update system settings."""
    if not request.user.has_admin_access():
        messages.error(request, "Admin access required.")
        return redirect("dashboard:index")

    settings_obj = SystemSettings.load()

    if request.method == "POST":
        form = SystemSettingsForm(request.POST, request.FILES, instance=settings_obj)
        if form.is_valid():
            form.save()
            log_request_action(
                request,
                action="UPDATE",
                object_type="SystemSettings",
                object_id=settings_obj.id,
                description="Updated system settings"
            )
            messages.success(request, "System settings updated successfully.")
            return redirect("settingsapp:settings")
        else:
            for error_list in form.errors.values():
                for error in error_list:
                    messages.error(request, error)
    else:
        form = SystemSettingsForm(instance=settings_obj)

    # Get ALL users (not just admin/executive) for the Users & Access tab
    all_users = User.objects.all().order_by("-date_joined")

    # Get ALL members for the Members Management tab
    all_members = Member.objects.select_related("umu_nna_clan").all().order_by("-created_at")

    # Get member statistics
    member_stats = {
        "total": Member.objects.count(),
        "active": Member.objects.filter(status="ACTIVE").count(),
        "past": Member.objects.filter(status="PAST_MEMBER").count(),
        "removed": Member.objects.filter(status="REMOVED").count(),
    }

    # Get all clans with member counts for Clan Management tab
    clans = Clan.objects.annotate(member_count=Count("members")).order_by("name")

    return render(request, "settingsapp/settings.html", {
        "form": form,
        "settings": settings_obj,
        "all_users": all_users,
        "all_members": all_members,
        "member_stats": member_stats,
        "clans": clans,
    })