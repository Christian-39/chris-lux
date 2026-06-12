"""
Views for OYA projects.
"""
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from auditlogs.services import log_action
from .models import Project
from .forms import ProjectForm

logger = logging.getLogger("oya")


@login_required
def project_list(request):
    """List all projects with search, filter, and pagination."""
    queryset = Project.objects.all()

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
    projects = paginator.get_page(page)

    # Statistics
    stats = {
        "future": Project.objects.filter(status="FUTURE").count(),
        "at_hand": Project.objects.filter(status="AT_HAND").count(),
        "finished": Project.objects.filter(status="FINISHED").count(),
        "total": Project.objects.count(),
    }

    context = {
        "projects": projects,
        "stats": stats,
        "search_term": search_term,
        "status_filter": status_filter,
        "status_choices": Project.STATUS_CHOICES,
    }
    return render(request, "projects/project_list.html", context)


@login_required
def project_detail(request, pk):
    """Display project details."""
    project = get_object_or_404(Project, pk=pk)
    return render(request, "projects/project_detail.html", {"project": project})


@login_required
def project_create(request):
    """Create a new project."""
    if not request.user.has_executive_access():
        messages.error(request, "Executive access required.")
        return redirect("projects:project_list")

    if request.method == "POST":
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save()
            log_action(
                user=request.user,
                action="CREATE",
                object_type="Project",
                object_id=project.id,
                ip_address=getattr(request, "client_ip", ""),
                description=f"Created project: {project.title}"
            )
            messages.success(request, f"Project '{project.title}' created successfully.")
            return redirect("projects:project_list")
        else:
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = ProjectForm()

    return render(request, "projects/project_form.html", {
        "form": form,
        "title": "Create Project",
        "action": "Create"
    })


@login_required
def project_update(request, pk):
    """Update an existing project."""
    if not request.user.has_executive_access():
        messages.error(request, "Executive access required.")
        return redirect("projects:project_list")

    project = get_object_or_404(Project, pk=pk)

    if request.method == "POST":
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            log_action(
                user=request.user,
                action="UPDATE",
                object_type="Project",
                object_id=project.id,
                ip_address=getattr(request, "client_ip", ""),
                description=f"Updated project: {project.title}"
            )
            messages.success(request, "Project updated successfully.")
            return redirect("projects:project_list")
        else:
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = ProjectForm(instance=project)

    return render(request, "projects/project_form.html", {
        "form": form,
        "title": "Update Project",
        "action": "Update",
        "project": project
    })


@login_required
def project_delete(request, pk):
    """Delete a project."""
    if not request.user.has_admin_access():
        messages.error(request, "Admin access required.")
        return redirect("projects:project_list")

    project = get_object_or_404(Project, pk=pk)

    if request.method == "POST":
        title = project.title
        project.delete()
        log_action(
            user=request.user,
            action="DELETE",
            object_type="Project",
            object_id=pk,
            ip_address=getattr(request, "client_ip", ""),
            description=f"Deleted project: {title}"
        )
        messages.success(request, f"Project '{title}' deleted.")
        return redirect("projects:project_list")

    return render(request, "projects/project_confirm_delete.html", {"project": project})
