"""
Updated views for OYA finance with real data fetching.
"""
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count
from django.utils import timezone
from django.http import JsonResponse
from datetime import timedelta
from auditlogs.services import log_action
from .models import Income, Expense
from .forms import IncomeForm, ExpenseForm

logger = logging.getLogger("oya")


@login_required
def income_list(request):
    """List all income records with search and pagination."""
    queryset = Income.objects.select_related("created_by").all()

    # Search
    search_term = request.GET.get("search", "")
    if search_term:
        queryset = queryset.filter(
            Q(reason__icontains=search_term) |
            Q(paid_by__icontains=search_term) |
            Q(created_by__full_name__icontains=search_term)
        )

    # Date filter
    date_from = request.GET.get("date_from", "")
    date_to = request.GET.get("date_to", "")
    if date_from:
        queryset = queryset.filter(created_at__date__gte=date_from)
    if date_to:
        queryset = queryset.filter(created_at__date__lte=date_to)

    paginator = Paginator(queryset, 25)
    page = request.GET.get("page", 1)
    incomes = paginator.get_page(page)

    # Stats
    total_income = Income.objects.aggregate(total=Sum("amount"))["total"] or 0

    # This month income
    now = timezone.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    this_month_income = Income.objects.filter(
        created_at__gte=month_start
    ).aggregate(total=Sum("amount"))["total"] or 0

    total_records = Income.objects.count()
    unique_payers = Income.objects.exclude(paid_by="").values("paid_by").distinct().count()

    context = {
        "incomes": incomes,
        "search_term": search_term,
        "date_from": date_from,
        "date_to": date_to,
        "total_income": total_income,
        "this_month_income": this_month_income,
        "total_records": total_records,
        "unique_payers": unique_payers,
    }
    return render(request, "finance/income_list.html", context)


@login_required
def income_create(request):
    """Create a new income record with real backend data."""
    if not request.user.has_executive_access():
        messages.error(request, "Executive access required.")
        return redirect("finance:income_list")

    # Real-time financial data from backend
    total_income = Income.objects.aggregate(total=Sum("amount"))["total"] or 0
    total_expenses = Expense.objects.aggregate(total=Sum("amount"))["total"] or 0
    treasury_balance = total_income - total_expenses

    # Recent incomes for context (last 5)
    recent_incomes = Income.objects.select_related("created_by").order_by("-created_at")[:5]

    # Common reasons from past 30 days (frequency-based suggestions)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    common_reasons = (
        Income.objects.filter(created_at__gte=thirty_days_ago)
        .values("reason")
        .annotate(count=Count("id"))
        .order_by("-count")
        .values_list("reason", flat=True)[:5]
    )

    if request.method == "POST":
        form = IncomeForm(request.POST)
        if form.is_valid():
            income = form.save(commit=False)
            income.created_by = request.user
            income.save()
            log_action(
                user=request.user,
                action="CREATE",
                object_type="Income",
                object_id=income.id,
                ip_address=getattr(request, "client_ip", ""),
                description=f"Recorded income: \u20a6{income.amount:,.2f} - {income.reason}"
            )
            messages.success(request, "Income recorded successfully.")
            return redirect("finance:income_list")
        else:
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = IncomeForm()

    return render(request, "finance/income_form.html", {
        "form": form,
        "title": "Record Income",
        "action": "Save",
        "treasury_balance": treasury_balance,
        "total_income": total_income,
        "total_expenses": total_expenses,
        "recent_incomes": recent_incomes,
        "common_reasons": list(common_reasons),
    })


@login_required
def income_detail(request, pk):
    """Display income details."""
    income = get_object_or_404(Income.objects.select_related("created_by"), pk=pk)
    return render(request, "finance/income_detail.html", {"income": income})


@login_required
def income_delete(request, pk):
    """Delete an income record."""
    if not request.user.has_admin_access():
        messages.error(request, "Admin access required.")
        return redirect("finance:income_list")

    income = get_object_or_404(Income, pk=pk)

    if request.method == "POST":
        amount = income.amount
        reason = income.reason
        income.delete()
        log_action(
            user=request.user,
            action="DELETE",
            object_type="Income",
            object_id=pk,
            ip_address=getattr(request, "client_ip", ""),
            description=f"Deleted income: \u20a6{amount:,.2f} - {reason}"
        )
        messages.success(request, "Income record deleted.")
        return redirect("finance:income_list")

    return render(request, "finance/income_confirm_delete.html", {"income": income})


@login_required
def expense_list(request):
    """List all expense records with search and pagination."""
    queryset = Expense.objects.select_related("created_by").all()

    # Search
    search_term = request.GET.get("search", "")
    if search_term:
        queryset = queryset.filter(
            Q(description__icontains=search_term) |
            Q(category__icontains=search_term) |
            Q(created_by__full_name__icontains=search_term)
        )

    # Category filter
    category_filter = request.GET.get("category", "")
    if category_filter:
        queryset = queryset.filter(category=category_filter)

    # Date filter
    date_from = request.GET.get("date_from", "")
    date_to = request.GET.get("date_to", "")
    if date_from:
        queryset = queryset.filter(created_at__date__gte=date_from)
    if date_to:
        queryset = queryset.filter(created_at__date__lte=date_to)

    paginator = Paginator(queryset, 25)
    page = request.GET.get("page", 1)
    expenses = paginator.get_page(page)

    # Stats
    total_expenses = Expense.objects.aggregate(total=Sum("amount"))["total"] or 0

    # This month expenses
    now = timezone.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    this_month_expenses = Expense.objects.filter(
        created_at__gte=month_start
    ).aggregate(total=Sum("amount"))["total"] or 0

    total_records = Expense.objects.count()

    # Treasury balance
    total_income = Income.objects.aggregate(total=Sum("amount"))["total"] or 0
    treasury_balance = total_income - total_expenses

    context = {
        "expenses": expenses,
        "search_term": search_term,
        "category_filter": category_filter,
        "category_choices": Expense.CATEGORY_CHOICES,
        "date_from": date_from,
        "date_to": date_to,
        "total_expenses": total_expenses,
        "this_month_expenses": this_month_expenses,
        "total_records": total_records,
        "treasury_balance": treasury_balance,
    }
    return render(request, "finance/expense_list.html", context)


@login_required
def expense_create(request):
    """Create a new expense record with real backend data."""
    if not request.user.has_executive_access():
        messages.error(request, "Executive access required.")
        return redirect("finance:expense_list")

    # Real-time financial data from backend
    total_income = Income.objects.aggregate(total=Sum("amount"))["total"] or 0
    total_expenses = Expense.objects.aggregate(total=Sum("amount"))["total"] or 0
    treasury_balance = total_income - total_expenses

    # Recent expenses for context (last 5)
    recent_expenses = Expense.objects.select_related("created_by").order_by("-created_at")[:5]

    # Common categories from past 30 days
    thirty_days_ago = timezone.now() - timedelta(days=30)
    common_categories = (
        Expense.objects.filter(created_at__gte=thirty_days_ago)
        .values("category")
        .annotate(count=Count("id"))
        .order_by("-count")
        .values_list("category", flat=True)[:5]
    )

    if request.method == "POST":
        form = ExpenseForm(request.POST, request.FILES)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.created_by = request.user
            expense.save()
            log_action(
                user=request.user,
                action="CREATE",
                object_type="Expense",
                object_id=expense.id,
                ip_address=getattr(request, "client_ip", ""),
                description=f"Recorded expense: \u20a6{expense.amount:,.2f} - {expense.category}"
            )
            messages.success(request, "Expense recorded successfully.")
            return redirect("finance:expense_list")
        else:
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = ExpenseForm()

    return render(request, "finance/expense_form.html", {
        "form": form,
        "title": "Record Expense",
        "action": "Save",
        "treasury_balance": treasury_balance,
        "total_income": total_income,
        "total_expenses": total_expenses,
        "recent_expenses": recent_expenses,
        "common_categories": list(common_categories),
    })


@login_required
def expense_detail(request, pk):
    """Display expense details."""
    expense = get_object_or_404(Expense.objects.select_related("created_by"), pk=pk)
    return render(request, "finance/expense_detail.html", {"expense": expense})


@login_required
def expense_delete(request, pk):
    """Delete an expense record."""
    if not request.user.has_admin_access():
        messages.error(request, "Admin access required.")
        return redirect("finance:expense_list")

    expense = get_object_or_404(Expense, pk=pk)

    if request.method == "POST":
        amount = expense.amount
        category = expense.category
        expense.delete()
        log_action(
            user=request.user,
            action="DELETE",
            object_type="Expense",
            object_id=pk,
            ip_address=getattr(request, "client_ip", ""),
            description=f"Deleted expense: \u20a6{amount:,.2f} - {category}"
        )
        messages.success(request, "Expense record deleted.")
        return redirect("finance:expense_list")

    return render(request, "finance/expense_confirm_delete.html", {"expense": expense})


@login_required
def finance_summary(request):
    """Display financial summary."""
    total_income = Income.objects.aggregate(total=Sum("amount"))["total"] or 0
    total_expenses = Expense.objects.aggregate(total=Sum("amount"))["total"] or 0
    treasury_balance = total_income - total_expenses
    total_transactions = Income.objects.count() + Expense.objects.count()

    # Expenses by category with percentage
    expenses_raw = Expense.objects.values("category").annotate(
        total=Sum("amount")
    ).order_by("-total")

    expenses_by_category = []
    for item in expenses_raw:
        percentage = round((item["total"] / total_expenses * 100), 1) if total_expenses > 0 else 0
        expenses_by_category.append({
            "category": dict(Expense.CATEGORY_CHOICES).get(item["category"], item["category"]),
            "total": item["total"],
            "percentage": percentage,
        })

    # Recent transactions (combine income and expenses)
    recent_income = list(Income.objects.select_related("created_by").all()[:10])
    recent_expenses = list(Expense.objects.select_related("created_by").all()[:10])

    # Add type marker
    for item in recent_income:
        item.type = "income"
    for item in recent_expenses:
        item.type = "expense"

    # Combine and sort by created_at
    recent_transactions = sorted(
        recent_income + recent_expenses,
        key=lambda x: x.created_at,
        reverse=True
    )[:10]

    context = {
        "total_income": total_income,
        "total_expenses": total_expenses,
        "treasury_balance": treasury_balance,
        "total_transactions": total_transactions,
        "expenses_by_category": expenses_by_category,
        "recent_transactions": recent_transactions,
    }
    return render(request, "finance/finance_summary.html", context)


# AJAX endpoint for member search (used by Select2 in forms)
@login_required
def search_members(request):
    """AJAX endpoint for member name auto-suggest."""
    from accounts.models import User
    
    q = request.GET.get("q", "").strip()
    if len(q) < 2:
        return JsonResponse({"results": []})

    users = User.objects.filter(
        Q(full_name__icontains=q) |
        Q(serial_number__icontains=q) |
        Q(phone__icontains=q)
    ).filter(is_active=True).distinct()[:10]

    results = []
    for u in users:
        html = (
            f'<div class="member-result">'
            f'  <span class="member-name">{u.get_full_name()}</span>'
            f'  <span class="member-meta">{u.serial_number} &middot; {u.get_role_display()}</span>'
            f'</div>'
        )
        results.append({
            "id": u.full_name,
            "text": f"{u.get_full_name()} ({u.serial_number})",
            "html": html,
            "name": u.full_name,
            "serial": u.serial_number,
            "role": u.get_role_display(),
        })

    return JsonResponse({"results": results})