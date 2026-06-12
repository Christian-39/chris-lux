"""
Views for OYA members.
"""
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from auditlogs.services import log_action
from accounts.permissions import AdminRequiredMixin, ExecutiveRequiredMixin
from core.utils import paginate_queryset, build_search_query
from .models import Member, Clan
from .forms import MemberForm, MemberUpdateForm, MemberRemoveForm, ClanForm

logger = logging.getLogger("oya")


@login_required
def member_list(request):
    """List all members with search, filter, and pagination."""
    queryset = Member.objects.select_related("umu_nna_clan").all()

    search_term = request.GET.get("search", "")
    if search_term:
        search_fields = [
            "serial_number", "full_name", "phone",
            "state_or_abroad", "umu_nna_clan__name"
        ]
        queryset = queryset.filter(build_search_query(search_fields, search_term))

    status_filter = request.GET.get("status", "")
    if status_filter:
        queryset = queryset.filter(status=status_filter)

    clan_filter = request.GET.get("clan", "")
    if clan_filter:
        queryset = queryset.filter(umu_nna_clan_id=clan_filter)

    order_by = request.GET.get("order_by", "-created_at")
    queryset = queryset.order_by(order_by)

    paginator = Paginator(queryset, 25)
    page = request.GET.get("page", 1)
    members = paginator.get_page(page)

    stats = {
        "total": Member.objects.count(),
        "active": Member.objects.filter(status="ACTIVE").count(),
        "past": Member.objects.filter(status="PAST_MEMBER").count(),
        "removed": Member.objects.filter(status="REMOVED").count(),
    }

    return render(request, "members/member_list.html", {
        "members": members,
        "clans": Clan.objects.all(),
        "stats": stats,
        "search_term": search_term,
        "status_filter": status_filter,
        "clan_filter": clan_filter,
        "status_choices": Member.STATUS_CHOICES,
    })


@login_required
def member_detail(request, pk):
    """Display member details."""
    member = get_object_or_404(Member.objects.select_related("umu_nna_clan"), pk=pk)
    return render(request, "members/member_detail.html", {"member": member})


@login_required
def member_create(request):
    """Create a new member with login account and PIN."""
    if not request.user.has_executive_access():
        messages.error(request, "Executive access required.")
        return redirect("members:member_list")

    generated_pin = None

    if request.method == "POST":
        form = MemberForm(request.POST, request.FILES)
        if form.is_valid():
            member = form.save()

            # Get generated PIN from the instance
            if hasattr(member, '_generated_pin'):
                generated_pin = member._generated_pin

            log_action(
                user=request.user,
                action="CREATE",
                object_type="Member",
                object_id=member.id,
                ip_address=getattr(request, "client_ip", ""),
                description=f"Created member {member.serial_number} with login account"
            )
            messages.success(request, f"Member {member.serial_number} created successfully.")

            # Render form with PIN banner (don't redirect — admin needs to see PIN!)
            return render(request, "members/member_form.html", {
                "form": MemberForm(),
                "title": "Add New Member",
                "action": "Create",
                "generated_pin": generated_pin,
                "member": member,
            })
        else:
            # CRITICAL FIX: Properly iterate through nested error lists
            for field_name, error_list in form.errors.items():
                for error in error_list:
                    messages.error(request, f"{field_name}: {error}")
    else:
        form = MemberForm()

    return render(request, "members/member_form.html", {
        "form": form,
        "title": "Add New Member",
        "action": "Create",
        "generated_pin": generated_pin,
    })


@login_required
def member_update(request, pk):
    """Update an existing member and sync login account."""
    if not request.user.has_executive_access():
        messages.error(request, "Executive access required.")
        return redirect("members:member_list")

    member = get_object_or_404(Member, pk=pk)
    updated_pin = None

    if request.method == "POST":
        form = MemberUpdateForm(request.POST, request.FILES, instance=member)
        if form.is_valid():
            member = form.save()

            if hasattr(member, '_updated_pin'):
                updated_pin = member._updated_pin
            elif hasattr(member, '_generated_pin'):
                updated_pin = member._generated_pin

            log_action(
                user=request.user,
                action="UPDATE",
                object_type="Member",
                object_id=member.id,
                ip_address=getattr(request, "client_ip", ""),
                description=f"Updated member {member.serial_number}"
            )
            messages.success(request, f"Member {member.serial_number} updated successfully.")

            # Render form with PIN banner
            return render(request, "members/member_form.html", {
                "form": form,
                "title": "Update Member",
                "action": "Update",
                "member": member,
                "updated_pin": updated_pin,
            })
        else:
            # CRITICAL FIX: Properly iterate through nested error lists
            for field_name, error_list in form.errors.items():
                for error in error_list:
                    messages.error(request, f"{field_name}: {error}")
    else:
        form = MemberUpdateForm(instance=member)

    return render(request, "members/member_form.html", {
        "form": form,
        "title": "Update Member",
        "action": "Update",
        "member": member,
        "updated_pin": updated_pin,
    })


@login_required
def member_remove(request, pk):
    """Remove a member with a reason."""
    if not request.user.has_executive_access():
        messages.error(request, "Executive access required.")
        return redirect("members:member_list")

    member = get_object_or_404(Member, pk=pk)

    if request.method == "POST":
        form = MemberRemoveForm(request.POST, instance=member)
        if form.is_valid():
            form.save()

            try:
                from accounts.models import User
                user = User.objects.get(serial_number=member.serial_number)
                user.is_active = False
                user.save()
            except User.DoesNotExist:
                pass

            log_action(
                user=request.user,
                action="UPDATE",
                object_type="Member",
                object_id=member.id,
                ip_address=getattr(request, "client_ip", ""),
                description=f"Removed member {member.serial_number}: {member.removal_reason}"
            )
            messages.success(request, f"Member {member.serial_number} has been removed.")
            return redirect("members:member_list")
    else:
        form = MemberRemoveForm(instance=member)

    return render(request, "members/member_remove.html", {
        "form": form,
        "member": member
    })


@login_required
def member_delete(request, pk):
    """Delete a member permanently (admin only)."""
    if not request.user.has_admin_access():
        messages.error(request, "Admin access required.")
        return redirect("members:member_list")

    member = get_object_or_404(Member, pk=pk)

    if request.method == "POST":
        serial = member.serial_number

        try:
            from accounts.models import User
            user = User.objects.get(serial_number=serial)
            user.delete()
        except User.DoesNotExist:
            pass

        member.delete()
        log_action(
            user=request.user,
            action="DELETE",
            object_type="Member",
            object_id=pk,
            ip_address=getattr(request, "client_ip", ""),
            description=f"Deleted member {serial}"
        )
        messages.success(request, f"Member {serial} deleted permanently.")
        return redirect("members:member_list")

    return render(request, "members/member_confirm_delete.html", {"member": member})


@login_required
def clan_list(request):
    """List all clans with member counts."""
    clans = Clan.objects.annotate(member_count=Count("members")).all()
    return render(request, "members/clan_list.html", {"clans": clans})


@login_required
def clan_create(request):
    """Create a new clan - supports both regular and AJAX requests."""
    if not request.user.has_executive_access():
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Executive access required.'}, status=403)
        messages.error(request, "Executive access required.")
        return redirect("members:clan_list")

    if request.method == "POST":
        form = ClanForm(request.POST)
        if form.is_valid():
            clan = form.save()
            log_action(
                user=request.user,
                action="CREATE",
                object_type="Clan",
                object_id=clan.id,
                ip_address=getattr(request, "client_ip", ""),
                description=f"Created clan {clan.name}"
            )

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'id': clan.id,
                    'name': clan.name,
                    'member_count': 0
                })

            messages.success(request, f"Clan '{clan.name}' created successfully.")
            return redirect("members:clan_list")
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                errors = []
                for field_errors in form.errors.values():
                    errors.extend(field_errors)
                return JsonResponse({'success': False, 'error': ' '.join(errors)}, status=400)

            for field_name, error_list in form.errors.items():
                for error in error_list:
                    messages.error(request, f"{field_name}: {error}")
    else:
        form = ClanForm()

    return render(request, "members/clan_form.html", {
        "form": form,
        "title": "Add Clan",
        "action": "Create"
    })


@login_required
@require_http_methods(["GET"])
def member_stats_ajax(request):
    """AJAX endpoint for member statistics."""
    stats = {
        "total": Member.objects.count(),
        "active": Member.objects.filter(status="ACTIVE").count(),
        "past": Member.objects.filter(status="PAST_MEMBER").count(),
        "removed": Member.objects.filter(status="REMOVED").count(),
        "by_clan": list(
            Clan.objects.annotate(
                count=Count("members")
            ).values("name", "count")
        ),
    }
    return JsonResponse(stats)