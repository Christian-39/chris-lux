"""
Views for OYA accounts.
"""
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods, require_POST
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Value, DecimalField
from django.db.models.functions import Coalesce
from core.exceptions import ValidationError, DuplicateRecordError
from auditlogs.services import log_request_action
from .models import User
from .forms import (
    LoginForm, UserCreateForm, UserUpdateForm,
    FloorMemberProfileForm, PINResetForm, ChangePINForm
)
from .permissions import AdminRequiredMixin, ExecutiveRequiredMixin

logger = logging.getLogger("oya")


def login_view(request):
    """Handle user login with serial number and PIN."""
    if request.user.is_authenticated:
        return redirect("dashboard:index")

    form = LoginForm(request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            serial_number = form.cleaned_data.get("serial_number")
            pin = form.cleaned_data.get("pin")
            user = authenticate(
                request,
                serial_number=serial_number,
                pin=pin
            )
            if user is not None:
                login(request, user)
                log_request_action(
                    request,
                    action="LOGIN",
                    object_type="User",
                    object_id=user.id,
                    description=f"User {user.serial_number} logged in"
                )
                messages.success(request, f"Welcome, {user.full_name}!")
                return redirect("dashboard:index")
            else:
                form.add_error(None, "Invalid serial number or PIN. Please check your credentials and try again.")

    return render(request, "accounts/login.html", {"form": form})


def logout_view(request):
    """Handle user logout."""
    if request.user.is_authenticated:
        log_request_action(
            request,
            action="LOGOUT",
            object_type="User",
            object_id=request.user.id,
            description=f"User {request.user.serial_number} logged out"
        )
        logout(request)
        messages.success(request, "You have been logged out.")
    return redirect("accounts:login")


@login_required
def user_list(request):
    """List all users with search and pagination."""
    queryset = User.objects.all()
    search_term = request.GET.get("search", "")

    if search_term:
        queryset = queryset.filter(
            Q(serial_number__icontains=search_term) |
            Q(full_name__icontains=search_term) |
            Q(phone__icontains=search_term) |
            Q(state__icontains=search_term) |
            Q(role__icontains=search_term)
        )

    role_filter = request.GET.get("role", "")
    if role_filter:
        queryset = queryset.filter(role=role_filter)

    paginator = Paginator(queryset, 25)
    page = request.GET.get("page", 1)
    users = paginator.get_page(page)

    context = {
        "users": users,
        "search_term": search_term,
        "role_filter": role_filter,
        "role_choices": User.ROLE_CHOICES,
    }
    return render(request, "accounts/user_list.html", context)


@login_required
def user_detail(request, pk):
    """Display user details."""
    user = get_object_or_404(User, pk=pk)
    return render(request, "accounts/user_detail.html", {"user_obj": user})


@login_required
def user_create(request):
    """Create a new user (admin and executive)."""
    if not request.user.has_executive_access():
        messages.error(request, "You do not have permission to create users.")
        return redirect("accounts:user_list")

    if request.method == "POST":
        form = UserCreateForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            log_request_action(
                request,
                action="CREATE",
                object_type="User",
                object_id=user.id,
                description=f"Created user {user.serial_number}"
            )
            messages.success(request, f"User {user.serial_number} created successfully.")
            return redirect("accounts:user_list")
        else:
            for error_list in form.errors.values():
                for error in error_list:
                    messages.error(request, error)
    else:
        form = UserCreateForm()

    return render(request, "accounts/user_form.html", {
        "form": form,
        "title": "Create User",
        "action": "Create"
    })


@login_required
def user_update(request, pk):
    """Update an existing user."""
    user = get_object_or_404(User, pk=pk)

    if request.user.is_floor_member() and request.user.id != user.id:
        messages.error(request, "You can only edit your own profile.")
        return redirect("dashboard:index")

    if request.user.is_floor_member():
        if request.method == "POST":
            form = FloorMemberProfileForm(request.POST, request.FILES, instance=user)
            if form.is_valid():
                form.save()
                log_request_action(
                    request,
                    action="UPDATE",
                    object_type="User",
                    object_id=user.id,
                    description=f"Updated profile for {user.serial_number}"
                )
                messages.success(request, "Profile updated successfully.")
                return redirect("accounts:profile")
        else:
            form = FloorMemberProfileForm(instance=user)
        return render(request, "accounts/profile_edit.html", {"form": form})

    if request.method == "POST":
        form = UserUpdateForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            # Check if PIN was changed
            pin_changed = bool(form.cleaned_data.get("new_pin"))
            user = form.save()

            # If the user being updated is the current user and PIN changed,
            # update session hash to prevent logout
            if pin_changed and request.user.id == user.id:
                update_session_auth_hash(request, user)

            log_request_action(
                request,
                action="UPDATE",
                object_type="User",
                object_id=user.id,
                description=f"Updated user {user.serial_number}"
            )
            messages.success(request, f"User {user.serial_number} updated successfully.")
            return redirect("accounts:user_list")
        else:
            for error_list in form.errors.values():
                for error in error_list:
                    messages.error(request, error)
    else:
        form = UserUpdateForm(instance=user)

    return render(request, "accounts/user_form.html", {
        "form": form,
        "title": "Update User",
        "action": "Update",
        "user_obj": user
    })


@login_required
def user_delete(request, pk):
    """Delete a user (admin only)."""
    if not request.user.has_admin_access():
        messages.error(request, "Admin access required.")
        return redirect("accounts:user_list")

    user = get_object_or_404(User, pk=pk)

    if request.method == "POST":
        serial = user.serial_number
        user.delete()
        log_request_action(
            request,
            action="DELETE",
            object_type="User",
            object_id=pk,
            description=f"Deleted user {serial}"
        )
        messages.success(request, f"User {serial} deleted successfully.")
        return redirect("accounts:user_list")

    return render(request, "accounts/user_confirm_delete.html", {"user_obj": user})


@login_required
def pin_reset(request):
    """Reset a user's PIN (admin only)."""
    if not request.user.has_admin_access():
        messages.error(request, "Admin access required to reset PINs.")
        return redirect("dashboard:index")

    if request.method == "POST":
        form = PINResetForm(request.POST)
        if form.is_valid():
            serial_number = form.cleaned_data["serial_number"]
            new_pin = form.cleaned_data["new_pin"]

            try:
                user = User.objects.get(serial_number=serial_number)
                # Use set_pin() instead of set_password() for consistency
                user.set_pin(new_pin)
                user.save()

                log_request_action(
                    request,
                    action="PIN_RESET",
                    object_type="User",
                    object_id=user.id,
                    description=f"PIN reset for user {user.serial_number}"
                )
                messages.success(
                    request,
                    f"PIN for {user.serial_number} has been reset successfully."
                )
                return redirect("accounts:user_list")
            except User.DoesNotExist:
                messages.error(request, "User not found.")
        else:
            for error_list in form.errors.values():
                for error in error_list:
                    messages.error(request, error)
    else:
        form = PINResetForm()

    return render(request, "accounts/pin_reset.html", {"form": form})


@login_required
def profile_view(request):
    """View own profile with dues, notifications, and settings."""
    from finance.models import Income, Expense
    from notifications.models import Notification
    from django.conf import settings

    user = request.user

    # Get payment history from Income model (where paid_by matches user's name or serial)
    # Since Income.paid_by is a CharField, we search by name or serial
    payments_qs = Income.objects.filter(
        Q(paid_by__icontains=user.full_name) |
        Q(paid_by__icontains=user.serial_number) |
        Q(created_by=user)
    ).order_by("-created_at")

    payments_paginator = Paginator(payments_qs, 10)
    payments_page = request.GET.get("payments_page", 1)
    payments = payments_paginator.get_page(payments_page)

    # Calculate total paid (sum of income where user is the payer)
    total_paid = Income.objects.filter(
        Q(paid_by__icontains=user.full_name) |
        Q(paid_by__icontains=user.serial_number) |
        Q(created_by=user)
    ).aggregate(total=Coalesce(Sum("amount"), Value(0, output_field=DecimalField())))["total"]

    # Get recent notifications (global + personal)
    notifications = Notification.objects.filter(
        Q(recipient=user) | Q(is_global=True) | Q(recipient__isnull=True)
    ).order_by("-created_at")[:10]

    # Forms
    profile_form = FloorMemberProfileForm(instance=user)
    pin_form = ChangePINForm()

    context = {
        "user": user,
        "payments": payments,
        "total_paid": total_paid,
        "notifications": notifications,
        "profile_form": profile_form,
        "pin_form": pin_form,
        "currency_symbol": getattr(settings, "OYA_SETTINGS", {}).get("CURRENCY_SYMBOL", "₦"),
    }
    return render(request, "accounts/profile.html", context)


@login_required
@require_POST
def profile_update(request):
    """Update own profile (phone, state)."""
    form = FloorMemberProfileForm(request.POST, request.FILES, instance=request.user)
    if form.is_valid():
        form.save()
        log_request_action(
            request,
            action="UPDATE",
            object_type="User",
            object_id=request.user.id,
            description=f"Updated profile for {request.user.serial_number}"
        )
        messages.success(request, "Profile updated successfully.")
    else:
        for error_list in form.errors.values():
            for error in error_list:
                messages.error(request, error)
    return redirect("accounts:profile")


@login_required
@require_POST
def change_pin(request):
    """Change own PIN."""
    form = ChangePINForm(request.POST, user=request.user)
    if form.is_valid():
        new_pin = form.cleaned_data["new_pin"]
        request.user.set_pin(new_pin)
        request.user.save()
        update_session_auth_hash(request, request.user)
        log_request_action(
            request,
            action="PIN_RESET",
            object_type="User",
            object_id=request.user.id,
            description=f"User changed their own PIN"
        )
        messages.success(request, "PIN updated successfully.")
    else:
        for error_list in form.errors.values():
            for error in error_list:
                messages.error(request, error)
    return redirect("accounts:profile")


@login_required
@require_http_methods(["GET"])
def user_search_ajax(request):
    """AJAX endpoint for user search."""
    search_term = request.GET.get("q", "")
    if len(search_term) < 2:
        return JsonResponse({"results": []})

    users = User.objects.filter(
        Q(serial_number__icontains=search_term) |
        Q(full_name__icontains=search_term)
    )[:10]

    results = [
        {
            "id": u.id,
            "serial_number": u.serial_number,
            "full_name": u.full_name,
            "role": u.role,
            "photo_url": u.photo.url if u.photo else ""
        }
        for u in users
    ]

    return JsonResponse({"results": results})