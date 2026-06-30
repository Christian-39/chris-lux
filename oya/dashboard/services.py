"""
Dashboard services for OYA KPIs and aggregations.
"""
import logging
from datetime import datetime
from django.db.models import Sum, Count, Q
from django.core.cache import cache
from members.models import Member, Clan
from executives.models import Executive
from finance.models import Income, Expense, DuesPayment
from projects.models import Project
from operations.models import TaskForceMember, Motorcycle, CaseFile
from elections.models import Election
from notifications.models import Notification

logger = logging.getLogger("oya")

CACHE_TIMEOUT = 300  # 5 minutes


def get_dashboard_kpis():
    """Get all dashboard KPIs with caching."""
    cache_key = "oya_dashboard_kpis"
    cached = cache.get(cache_key)
    if cached:
        return cached

    kpis = {
        "total_active_members": _get_total_active_members(),
        "treasury_balance": _get_treasury_balance(),
        "total_income": _get_total_income(),
        "total_expenses": _get_total_expenses(),
        "pending_cases": _get_pending_cases(),
        "active_task_force": _get_active_task_force_count(),
        "motorcycles_active": _get_motorcycles_active(),
        "projects_finished": _get_projects_finished(),
        "projects_at_hand": _get_projects_at_hand(),
        "projects_future": _get_projects_future(),
        "current_executives": _get_current_executives_count(),
        "upcoming_elections": _get_upcoming_elections(),
    }

    cache.set(cache_key, kpis, CACHE_TIMEOUT)
    return kpis


def get_member_statistics():
    """Get member statistics by clan and status."""
    cache_key = "oya_member_statistics"
    cached = cache.get(cache_key)
    if cached:
        return cached

    stats = {
        "by_clan": list(
            Clan.objects.annotate(
                member_count=Count("members")
            ).values("name", "member_count")
        ),
        "by_status": {
            "active": Member.objects.filter(status="ACTIVE").count(),
            "past": Member.objects.filter(status="PAST_MEMBER").count(),
            "removed": Member.objects.filter(status="REMOVED").count(),
        },
        "total": Member.objects.count(),
    }

    cache.set(cache_key, stats, CACHE_TIMEOUT)
    return stats


def get_finance_statistics():
    """Get finance statistics."""
    cache_key = "oya_finance_statistics"
    cached = cache.get(cache_key)
    if cached:
        return cached

    stats = {
        "total_income": _get_total_income(),
        "total_expenses": _get_total_expenses(),
        "treasury_balance": _get_treasury_balance(),
        "expenses_by_category": list(
            Expense.objects.values("category").annotate(
                total=Sum("amount")
            ).order_by("-total")
        ),
    }

    cache.set(cache_key, stats, CACHE_TIMEOUT)
    return stats


def get_income_expense_trend(year=None):
    """
    Get monthly income vs expenses data for chart display.
    Returns data for each month Jan-current_month of the given year (or current year).
    Includes all income types (dues, donations, events, other) + dues payments.
    """
    if year is None:
        year = datetime.now().year

    cache_key = f"oya_income_expense_trend_{year}"
    cached = cache.get(cache_key)
    if cached:
        return cached

    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    income_data = []
    expense_data = []

    for month in range(1, 13):
        # Income for this month (all types including linked dues payments)
        monthly_income = Income.objects.filter(
            created_at__year=year,
            created_at__month=month
        ).aggregate(total=Sum("amount"))["total"] or 0

        # Expenses for this month
        monthly_expense = Expense.objects.filter(
            created_at__year=year,
            created_at__month=month
        ).aggregate(total=Sum("amount"))["total"] or 0

        income_data.append(float(monthly_income))
        expense_data.append(float(monthly_expense))

    # Only return months up to current month for current year
    current_year = datetime.now().year
    current_month = datetime.now().month

    if year == current_year:
        display_months = months[:current_month]
        display_income = income_data[:current_month]
        display_expense = expense_data[:current_month]
    else:
        display_months = months
        display_income = income_data
        display_expense = expense_data

    result = {
        "year": year,
        "months": display_months,
        "income": display_income,
        "expenses": display_expense,
        "total_income_ytd": sum(display_income),
        "total_expenses_ytd": sum(display_expense),
        "net_ytd": sum(display_income) - sum(display_expense),
    }

    cache.set(cache_key, result, CACHE_TIMEOUT)
    return result


def get_recent_activities(limit=10):
    """Get recent audit log activities."""
    from auditlogs.models import AuditLog
    return AuditLog.objects.select_related("user").all()[:limit]


def get_clan_distribution():
    """Get clan distribution data for charts."""
    cache_key = "oya_clan_distribution"
    cached = cache.get(cache_key)
    if cached:
        return cached

    clans = Clan.objects.annotate(
        member_count=Count("members")
    ).filter(member_count__gt=0).order_by("-member_count")

    data = {
        "labels": [clan.name for clan in clans],
        "data": [clan.member_count for clan in clans],
        "total": sum(clan.member_count for clan in clans),
    }

    cache.set(cache_key, data, CACHE_TIMEOUT)
    return data


def get_urgent_cases(limit=5):
    """Get urgent/open cases for dashboard display."""
    return CaseFile.objects.filter(
        Q(status="OPEN") | Q(status="IN_PROGRESS")
    ).select_related("respondent", "created_by").order_by("-created_at")[:limit]


def get_current_executives(limit=10):
    """Get current executives for directory."""
    try:
        return Executive.objects.filter(
            is_current=True
        ).select_related("member").order_by("post_order", "-created_at")[:limit]
    except Exception:
        return []


def get_active_task_force(limit=10):
    """Get active task force members for directory."""
    try:
        return TaskForceMember.objects.filter(
            is_active=True
        ).select_related("member").order_by("-assigned_date")[:limit]
    except Exception:
        return []


def get_recent_notices(limit=5):
    """Get recent notifications/notices."""
    try:
        return Notification.objects.filter(
            is_active=True
        ).order_by("-created_at")[:limit]
    except Exception:
        return []


def get_member_contributions(member):
    """Get contribution history for a specific member."""
    from finance.models import Income
    try:
        contributions = Income.objects.filter(
            paid_by__icontains=member.full_name
        ).order_by("-created_at")[:6]
        total = Income.objects.filter(
            paid_by__icontains=member.full_name
        ).aggregate(total=Sum("amount"))["total"] or 0
        return {
            "contributions": contributions,
            "total_contributed": total,
        }
    except Exception:
        return {
            "contributions": [],
            "total_contributed": 0,
        }


def invalidate_dashboard_cache():
    """Invalidate all dashboard cache keys."""
    cache.delete("oya_dashboard_kpis")
    cache.delete("oya_member_statistics")
    cache.delete("oya_finance_statistics")
    cache.delete("oya_clan_distribution")
    # Also invalidate trend cache for current and previous year
    current_year = datetime.now().year
    cache.delete(f"oya_income_expense_trend_{current_year}")
    cache.delete(f"oya_income_expense_trend_{current_year - 1}")


# --- Private helper functions ---

def _get_total_active_members():
    """Get total number of active members."""
    try:
        return Member.objects.filter(status="ACTIVE").count()
    except Exception:
        return 0


def _get_treasury_balance():
    """Calculate treasury balance (total income - total expenses)."""
    try:
        total_income = Income.objects.aggregate(total=Sum("amount"))["total"] or 0
        total_expenses = Expense.objects.aggregate(total=Sum("amount"))["total"] or 0
        return total_income - total_expenses
    except Exception:
        return 0


def _get_total_income():
    """Get total income."""
    try:
        return Income.objects.aggregate(total=Sum("amount"))["total"] or 0
    except Exception:
        return 0


def _get_total_expenses():
    """Get total expenses."""
    try:
        return Expense.objects.aggregate(total=Sum("amount"))["total"] or 0
    except Exception:
        return 0


def _get_pending_cases():
    """Get count of open and in-progress cases."""
    try:
        return CaseFile.objects.filter(
            Q(status="OPEN") | Q(status="IN_PROGRESS")
        ).count()
    except Exception:
        return 0


def _get_active_task_force_count():
    """Get count of active task force members."""
    try:
        return TaskForceMember.objects.filter(is_active=True).count()
    except Exception:
        return 0


def _get_motorcycles_active():
    """Get count of motorcycles that are not grounded."""
    try:
        return Motorcycle.objects.exclude(condition="GROUNDED").count()
    except Exception:
        return 0


def _get_projects_finished():
    """Get count of finished projects."""
    try:
        return Project.objects.filter(status="FINISHED").count()
    except Exception:
        return 0


def _get_projects_at_hand():
    """Get count of ongoing projects."""
    try:
        return Project.objects.filter(status="AT_HAND").count()
    except Exception:
        return 0


def _get_projects_future():
    """Get count of future projects."""
    try:
        return Project.objects.filter(status="FUTURE").count()
    except Exception:
        return 0


def _get_current_executives_count():
    """Get count of current executives."""
    try:
        return Executive.objects.filter(is_current=True).count()
    except Exception:
        return 0


def _get_upcoming_elections():
    """Get count of upcoming elections."""
    try:
        return Election.objects.filter(status__in=["UPCOMING", "ONGOING"]).count()
    except Exception:
        return 0
