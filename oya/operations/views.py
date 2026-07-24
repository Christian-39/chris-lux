"""
Views for OYA operations.
"""
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from auditlogs.services import log_action
from .models import TaskForceMember, Motorcycle, CaseFile
from .forms import (
    TaskForceMemberForm, MotorcycleForm,
    CaseFileForm, CaseResolutionForm
)

logger = logging.getLogger("oya")


# Task Force Views
@login_required
def taskforce_list(request):
    """List all task force members."""
    queryset = TaskForceMember.objects.select_related("member", "member__umu_nna_clan").all()

    status_filter = request.GET.get("status", "")
    if status_filter == "active":
        queryset = queryset.filter(is_active=True)
    elif status_filter == "inactive":
        queryset = queryset.filter(is_active=False)

    paginator = Paginator(queryset, 25)
    page = request.GET.get("page", 1)
    taskforce = paginator.get_page(page)

    # Stats
    total_taskforce = TaskForceMember.objects.count()
    active_count = TaskForceMember.objects.filter(is_active=True).count()
    inactive_count = TaskForceMember.objects.filter(is_active=False).count()

    context = {
        "taskforce": taskforce,
        "status_filter": status_filter,
        "total_taskforce": total_taskforce,
        "active_count": active_count,
        "inactive_count": inactive_count,
    }
    return render(request, "operations/taskforce_list.html", context)


@login_required
def taskforce_create(request):
    """Assign a task force member."""
    if not request.user.has_executive_access():
        messages.error(request, "Executive access required.")
        return redirect("operations:taskforce_list")

    # Get active members not already in task force
    from members.models import Member
    assigned_ids = TaskForceMember.objects.filter(is_active=True).values_list("member_id", flat=True)
    available_members = Member.objects.filter(
        status="ACTIVE"
    ).exclude(
        id__in=assigned_ids
    ).order_by("full_name")

    if request.method == "POST":
        form = TaskForceMemberForm(request.POST)
        if form.is_valid():
            tf = form.save()
            log_action(
                user=request.user,
                action="CREATE",
                object_type="TaskForceMember",
                object_id=tf.id,
                ip_address=getattr(request, "client_ip", ""),
                description=f"Assigned {tf.member.full_name} to task force"
            )
            messages.success(request, f"{tf.member.full_name} assigned to task force.")
            return redirect("operations:taskforce_list")
        else:
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = TaskForceMemberForm()

    return render(request, "operations/taskforce_form.html", {
        "form": form,
        "available_members": available_members,
        "title": "Assign Task Force Member",
        "action": "Assign"
    })


@login_required
def taskforce_update(request, pk):
    """Update a task force member assignment."""
    if not request.user.has_executive_access():
        messages.error(request, "Executive access required.")
        return redirect("operations:taskforce_list")

    tf = get_object_or_404(TaskForceMember, pk=pk)

    if request.method == "POST":
        form = TaskForceMemberForm(request.POST, instance=tf)
        if form.is_valid():
            tf = form.save()
            log_action(
                user=request.user,
                action="UPDATE",
                object_type="TaskForceMember",
                object_id=tf.id,
                ip_address=getattr(request, "client_ip", ""),
                description=f"Updated task force assignment for {tf.member.full_name}"
            )
            messages.success(request, f"Task force assignment for {tf.member.full_name} updated.")
            return redirect("operations:taskforce_list")
        else:
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = TaskForceMemberForm(instance=tf)

    return render(request, "operations/taskforce_form.html", {
        "form": form,
        "taskforce": tf,
        "title": "Update Task Force Member",
        "action": "Update"
    })


@login_required
def taskforce_remove(request, pk):
    """Remove a task force member."""
    if not request.user.has_executive_access():
        messages.error(request, "Executive access required.")
        return redirect("operations:taskforce_list")

    tf = get_object_or_404(TaskForceMember, pk=pk)

    if request.method == "POST":
        tf.is_active = False
        tf.save()
        log_action(
            user=request.user,
            action="UPDATE",
            object_type="TaskForceMember",
            object_id=tf.id,
            ip_address=getattr(request, "client_ip", ""),
            description=f"Removed {tf.member.full_name} from task force"
        )
        messages.success(request, f"{tf.member.full_name} removed from task force.")
        return redirect("operations:taskforce_list")

    return render(request, "operations/taskforce_remove.html", {"taskforce": tf})


# Motorcycle Views
@login_required
def motorcycle_list(request):
    """List all motorcycles with search and filter."""
    queryset = Motorcycle.objects.select_related("assigned_to").all()

    search_term = request.GET.get("search", "")
    if search_term:
        queryset = queryset.filter(
            Q(asset_tag__icontains=search_term) |
            Q(brand__icontains=search_term) |
            Q(model__icontains=search_term)
        )

    condition_filter = request.GET.get("condition", "")
    if condition_filter:
        queryset = queryset.filter(condition=condition_filter)

    paginator = Paginator(queryset, 25)
    page = request.GET.get("page", 1)
    motorcycles = paginator.get_page(page)

    # Stats
    total_motorcycles = Motorcycle.objects.count()
    excellent_count = Motorcycle.objects.filter(condition="EXCELLENT").count()
    needs_service_count = Motorcycle.objects.filter(condition="NEEDS_SERVICE").count()
    grounded_count = Motorcycle.objects.filter(condition="GROUNDED").count()

    context = {
        "motorcycles": motorcycles,
        "search_term": search_term,
        "condition_filter": condition_filter,
        "condition_choices": Motorcycle.CONDITION_CHOICES,
        "total_motorcycles": total_motorcycles,
        "excellent_count": excellent_count,
        "needs_service_count": needs_service_count,
        "grounded_count": grounded_count,
    }
    return render(request, "operations/motorcycle_list.html", context)


@login_required
def motorcycle_create(request):
    """Register a new motorcycle."""
    if not request.user.has_executive_access():
        messages.error(request, "Executive access required.")
        return redirect("operations:motorcycle_list")

    if request.method == "POST":
        form = MotorcycleForm(request.POST)
        if form.is_valid():
            mc = form.save()
            log_action(
                user=request.user,
                action="CREATE",
                object_type="Motorcycle",
                object_id=mc.id,
                ip_address=getattr(request, "client_ip", ""),
                description=f"Registered motorcycle {mc.asset_tag}"
            )
            messages.success(request, f"Motorcycle {mc.asset_tag} registered.")
            return redirect("operations:motorcycle_list")
        else:
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = MotorcycleForm()

    return render(request, "operations/motorcycle_form.html", {
        "form": form,
        "title": "Register Motorcycle",
        "action": "Register"
    })


@login_required
def motorcycle_update(request, pk):
    """Update motorcycle details."""
    if not request.user.has_executive_access():
        messages.error(request, "Executive access required.")
        return redirect("operations:motorcycle_list")

    mc = get_object_or_404(Motorcycle, pk=pk)

    if request.method == "POST":
        form = MotorcycleForm(request.POST, instance=mc)
        if form.is_valid():
            form.save()
            log_action(
                user=request.user,
                action="UPDATE",
                object_type="Motorcycle",
                object_id=mc.id,
                ip_address=getattr(request, "client_ip", ""),
                description=f"Updated motorcycle {mc.asset_tag}"
            )
            messages.success(request, "Motorcycle updated.")
            return redirect("operations:motorcycle_list")
        else:
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = MotorcycleForm(instance=mc)

    return render(request, "operations/motorcycle_form.html", {
        "form": form,
        "title": "Update Motorcycle",
        "action": "Update",
        "motorcycle": mc
    })


@login_required
def motorcycle_delete(request, pk):
    """Delete a motorcycle record."""
    if not request.user.has_executive_access():
        messages.error(request, "Executive access required.")
        return redirect("operations:motorcycle_list")

    mc = get_object_or_404(Motorcycle, pk=pk)

    if request.method == "POST":
        asset_tag = mc.asset_tag
        mc.delete()
        log_action(
            user=request.user,
            action="DELETE",
            object_type="Motorcycle",
            object_id=pk,
            ip_address=getattr(request, "client_ip", ""),
            description=f"Deleted motorcycle {asset_tag}"
        )
        messages.success(request, f"Motorcycle {asset_tag} deleted.")
        return redirect("operations:motorcycle_list")

    return render(request, "operations/motorcycle_delete.html", {"motorcycle": mc})


# Case File Views
@login_required
def case_list(request):
    """List all case files with search and filter."""
    queryset = CaseFile.objects.select_related("respondent", "created_by").all()

    search_term = request.GET.get("search", "")
    if search_term:
        queryset = queryset.filter(
            Q(title__icontains=search_term) |
            Q(case_number__icontains=search_term) |
            Q(respondent__full_name__icontains=search_term)
        )

    status_filter = request.GET.get("status", "")
    if status_filter:
        queryset = queryset.filter(status=status_filter)

    paginator = Paginator(queryset, 25)
    page = request.GET.get("page", 1)
    cases = paginator.get_page(page)

    stats = {
        "open": CaseFile.objects.filter(status="OPEN").count(),
        "in_progress": CaseFile.objects.filter(status="IN_PROGRESS").count(),
        "resolved": CaseFile.objects.filter(status="RESOLVED").count(),
        "total": CaseFile.objects.count(),
    }

    context = {
        "cases": cases,
        "stats": stats,
        "search_term": search_term,
        "status_filter": status_filter,
        "status_choices": CaseFile.STATUS_CHOICES,
    }
    return render(request, "operations/case_list.html", context)


@login_required
def case_detail(request, pk):
    """Display case details."""
    case = get_object_or_404(
        CaseFile.objects.select_related("respondent", "created_by"), pk=pk
    )
    return render(request, "operations/case_detail.html", {"case": case})


@login_required
def case_create(request):
    """Create a new case file."""
    if not request.user.has_executive_access():
        messages.error(request, "Executive access required.")
        return redirect("operations:case_list")

    if request.method == "POST":
        form = CaseFileForm(request.POST)
        if form.is_valid():
            case = form.save(commit=False)
            case.created_by = request.user
            case.save()
            log_action(
                user=request.user,
                action="CREATE",
                object_type="CaseFile",
                object_id=case.id,
                ip_address=getattr(request, "client_ip", ""),
                description=f"Created case {case.case_number}: {case.title}"
            )
            messages.success(request, f"Case {case.case_number} created.")
            return redirect("operations:case_list")
        else:
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = CaseFileForm()

    return render(request, "operations/case_form.html", {
        "form": form,
        "title": "Create Case File",
        "action": "Create"
    })


@login_required
def case_resolve(request, pk):
    """Resolve a case file."""
    if not request.user.has_executive_access():
        messages.error(request, "Executive access required.")
        return redirect("operations:case_list")

    case = get_object_or_404(CaseFile, pk=pk)

    if request.method == "POST":
        form = CaseResolutionForm(request.POST, instance=case)
        if form.is_valid():
            form.save()
            log_action(
                user=request.user,
                action="UPDATE",
                object_type="CaseFile",
                object_id=case.id,
                ip_address=getattr(request, "client_ip", ""),
                description=f"Resolved case {case.case_number}: {case.status}"
            )
            messages.success(request, f"Case {case.case_number} resolved.")
            return redirect("operations:case_list")
        else:
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = CaseResolutionForm(instance=case)

    return render(request, "operations/case_resolve.html", {
        "form": form,
        "case": case
    })
