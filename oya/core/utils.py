"""
Utility functions for OYA.
"""
import uuid
from datetime import datetime
from django.utils import timezone
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


def generate_serial_number():
    """Generate a unique serial number for members."""
    from members.models import Member
    year = timezone.now().year
    prefix = f"OYA-{year}"

    # Get the last member with this prefix
    last_member = Member.objects.filter(
        serial_number__startswith=prefix
    ).order_by("-serial_number").first()

    if last_member:
        try:
            last_num = int(last_member.serial_number.split("-")[-1])
            new_num = last_num + 1
        except (ValueError, IndexError):
            new_num = 1
    else:
        new_num = 1

    return f"{prefix}-{new_num:04d}"


def generate_user_serial_number():
    """Generate a unique serial number for user accounts."""
    from accounts.models import User
    year = timezone.now().year
    prefix = f"OYA-{year}"

    last_user = User.objects.filter(
        serial_number__startswith=prefix
    ).order_by("-serial_number").first()

    if last_user:
        try:
            last_num = int(last_user.serial_number.split("-")[-1])
            new_num = last_num + 1
        except (ValueError, IndexError):
            new_num = 1
    else:
        new_num = 1

    return f"{prefix}-{new_num:04d}"


def paginate_queryset(queryset, page_size=25, page=1):
    """Paginate a queryset with standard settings."""
    paginator = Paginator(queryset, page_size)
    try:
        paginated = paginator.page(page)
    except PageNotAnInteger:
        paginated = paginator.page(1)
    except EmptyPage:
        paginated = paginator.page(paginator.num_pages)

    return paginated


def build_search_query(fields, search_term):
    """Build a Q object for searching across multiple fields."""
    query = Q()
    for field in fields:
        query |= Q(**{f"{field}__icontains": search_term})
    return query


def exclude_removed_members(queryset):
    """
    Exclude Member records whose status is REMOVED from a Member queryset.

    Use this (instead of ad-hoc status filters) on every queryset that
    powers a member-selection input — dropdowns, autocomplete/search
    endpoints, etc. — so removed members can never be picked for new
    activities (payments, dues, donations, fines, task force, elections,
    asset assignment, and so on).
    """
    return queryset.exclude(status="REMOVED")


def exclude_removed_users(queryset):
    """
    Exclude User accounts linked (by matching serial_number) to a Member
    whose status is REMOVED.

    The User and Member models are matched by serial_number rather than a
    direct foreign key, so User-based selection endpoints (e.g. dues /
    income "member" pickers) need this explicit exclusion — filtering
    User.is_active alone does not account for a member being marked
    Removed on the Member record.
    """
    from members.models import Member
    removed_serials = Member.objects.filter(status="REMOVED").values_list(
        "serial_number", flat=True
    )
    return queryset.exclude(serial_number__in=removed_serials)