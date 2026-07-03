"""Updated views for OYA finance with smart dues allocation."""
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count, Max
from django.utils import timezone
from django.http import JsonResponse
from django.db.models import Value, DecimalField
from django.db.models import Coalesce
from django.db import transaction
from auditlogs.services import log_action
from accounts.models import User
from .models import Income, Expense, DuesPayment, DuesPaymentTransaction
from .forms import IncomeForm, ExpenseForm, DuesPaymentAllocationForm

logger = logging.getLogger("oya")

PLATFORM_START_YEAR = 2020
YEARLY_DUES = 5000


# ============================================================
# DONATIONS / OTHER CONTRIBUTIONS
# ============================================================

@login_required
def donation_list(request):
    """List all non-dues income (donations, events, other)."""
    queryset = Income.objects.exclude(income_type="DUES").select_related("created_by", "member")

    search_term = request.GET.get("search", "")
    if search_term:
        queryset = queryset.filter(
            Q(reason__icontains=search_term) |
            Q(paid_by__icontains=search_term) |
            Q(member__full_name__icontains=search_term) |
            Q(created_by__full_name__icontains=search_term)
        )

    type_filter = request.GET.get("type", "")
    if type_filter:
        queryset = queryset.filter(income_type=type_filter)

    date_from = request.GET.get("date_from", "")
    date_to = request.GET.get("date_to", "")
    if date_from:
        queryset = queryset.filter(created_at__date__gte=date_from)
    if date_to:
        queryset = queryset.filter(created_at__date__lte=date_to)

    paginator = Paginator(queryset, 25)
    page = request.GET.get("page", 1)
    donations = paginator.get_page(page)

    total_donations = Income.objects.exclude(income_type="DUES").aggregate(
        total=Sum("amount")
    )["total"] or 0

    now = timezone.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    this_month_donations = Income.objects.exclude(income_type="DUES").filter(
        created_at__gte=month_start
    ).aggregate(total=Sum("amount"))["total"] or 0

    total_records = Income.objects.exclude(income_type="DUES").count()

    context = {
        "donations": donations,
        "search_term": search_term,
        "type_filter": type_filter,
        "income_types": [c for c in Income.INCOME_TYPE_CHOICES if c[0] != "DUES"],
        "date_from": date_from,
        "date_to": date_to,
        "total_donations": total_donations,
        "this_month_donations": this_month_donations,
        "total_records": total_records,
    }
    return render(request, "finance/donation_list.html", context)


# ============================================================
# DUES TRACKER
# ============================================================

@login_required
def dues_tracker(request):
    """Full member x year grid showing dues payment status."""
    current_year = timezone.now().year
    years = list(range(PLATFORM_START_YEAR, current_year + 1))

    members = User.objects.filter(is_active=True).order_by("full_name")

    # Build a lookup of all dues payments
    dues_map = {}
    for dp in DuesPayment.objects.select_related("member").all():
        key = (dp.member_id, dp.year)
        dues_map[key] = dp

    member_rows = []
    total_dues_collected = Decimal("0")
    total_dues_expected = Decimal("0")

    for member in members:
        row = {"member": member, "years": {}}
        member_debt = DuesPayment.get_member_debt(member)
        row["total_debt"] = member_debt["debt_owed"]
        row["years_paid_count"] = len(member_debt["years_paid"])
        row["years_partial_count"] = len(member_debt.get("years_partial", []))

        for year in years:
            key = (member.id, year)
            if key in dues_map:
                dp = dues_map[key]
                row["years"][year] = {
                    "status": dp.status,
                    "payment": dp,
                    "amount_paid": dp.amount_paid,
                    "remaining": dp.remaining_balance,
                }
                total_dues_collected += dp.amount_paid
            else:
                row["years"][year] = {
                    "status": DuesPayment.STATUS_OWED,
                    "payment": None,
                    "amount_paid": Decimal("0"),
                    "remaining": Decimal(str(YEARLY_DUES)),
                }
                total_dues_expected += YEARLY_DUES

        member_rows.append(row)

    active_members_count = members.count()
    total_possible_dues = active_members_count * len(years) * YEARLY_DUES
    collection_rate = round(
        (float(total_dues_collected) / total_possible_dues * 100), 1
    ) if total_possible_dues > 0 else 0

    this_year_paid = DuesPayment.objects.filter(
        year=current_year,
        amount_paid__gte=YEARLY_DUES,
    ).count()
    this_year_expected = active_members_count
    this_year_rate = round(
        (this_year_paid / this_year_expected * 100), 1
    ) if this_year_expected > 0 else 0

    context = {
        "years": years,
        "member_rows": member_rows,
        "current_year": current_year,
        "yearly_dues": YEARLY_DUES,
        "total_dues_collected": total_dues_collected,
        "total_dues_expected": total_dues_expected,
        "total_possible_dues": total_possible_dues,
        "collection_rate": collection_rate,
        "this_year_paid": this_year_paid,
        "this_year_expected": this_year_expected,
        "this_year_rate": this_year_rate,
        "active_members_count": active_members_count,
    }
    return render(request, "finance/dues_tracker.html", context)


@login_required
def dues_allocate(request):
    """Smart dues payment allocation — auto-distributes across years."""
    if not request.user.has_executive_access():
        messages.error(request, "Executive access required.")
        return redirect("finance:dues_tracker")

    if request.method == "POST":
        form = DuesPaymentAllocationForm(request.POST, recorded_by=request.user)
        if form.is_valid():
            try:
                with transaction.atomic():
                    result = form.allocate()

                # Log the action
                tx = result["transaction"]
                allocation_summary = ", ".join(
                    f"{a['year']}: ₦{a['allocated']:,.2f}"
                    for a in result["allocations"]
                )
                log_action(
                    user=request.user,
                    action="CREATE",
                    object_type="DuesPaymentTransaction",
                    object_id=tx.id,
                    ip_address=getattr(request, "client_ip", ""),
                    description=(
                        f"Allocated dues payment: {tx.member.get_full_name()} — "
                        f"₦{tx.total_amount:,.2f} → [{allocation_summary}]"
                    ),
                )

                # Show user-friendly messages
                for msg in result["messages"]:
                    messages.info(request, msg)

                messages.success(
                    request,
                    f"Successfully allocated ₦{result['total_allocated']:,.2f} "
                    f"for {tx.member.get_full_name()}."
                )
                if result["remaining"] > 0:
                    messages.warning(
                        request,
                        f"₦{result['remaining']:,.2f} could not be allocated."
                    )

                return redirect("finance:dues_tracker")

            except Exception as e:
                logger.exception("Dues allocation failed")
                messages.error(request, f"Allocation failed: {str(e)}")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = DuesPaymentAllocationForm(recorded_by=request.user)

    return render(request, "finance/dues_form.html", {
        "form": form,
        "title": "Record Dues Payment",
        "action": "Allocate Payment",
        "yearly_dues": YEARLY_DUES,
    })


@login_required
def member_dues_detail(request, member_id):
    """Show detailed dues history and debt for a single member."""
    member = get_object_or_404(User, pk=member_id, is_active=True)
    current_year = timezone.now().year

    # Get join year to determine range
    join_year = DuesPayment.get_member_join_year(member)
    start_year = max(join_year, PLATFORM_START_YEAR)

    # Include future prepaid years in the display
    max_year = max(
        current_year,
        DuesPayment.objects.filter(member=member).aggregate(
            max_year=Coalesce(Max("year"), Value(current_year))
        )["max_year"]
    )

    years = list(range(start_year, max_year + 1))

    debt_info = DuesPayment.get_member_debt(member)
    payments = DuesPayment.objects.filter(member=member).select_related(
        "recorded_by", "income"
    ).order_by("-year")

    year_status = []
    for year in years:
        payment = payments.filter(year=year).first()
        year_status.append({
            "year": year,
            "status": payment.status if payment else DuesPayment.STATUS_OWED,
            "payment": payment,
            "is_future": year > current_year,
        })

    # Get payment transactions for this member
    transactions = DuesPaymentTransaction.objects.filter(
        member=member
    ).select_related("recorded_by").order_by("-payment_date")[:20]

    context = {
        "member": member,
        "year_status": year_status,
        "debt_info": debt_info,
        "payments": payments,
        "transactions": transactions,
        "yearly_dues": YEARLY_DUES,
        "current_year": current_year,
    }
    return render(request, "finance/member_dues_detail.html", context)


@login_required
def dues_delete(request, pk):
    """Delete a dues payment record (and its linked income)."""
    if not request.user.has_admin_access():
        messages.error(request, "Admin access required.")
        return redirect("finance:dues_tracker")

    dues = get_object_or_404(DuesPayment.objects.select_related("member", "income"), pk=pk)

    if request.method == "POST":
        member_name = dues.member.get_full_name()
        year = dues.year
        if dues.income:
            dues.income.delete()
        dues.delete()
        log_action(
            user=request.user,
            action="DELETE",
            object_type="DuesPayment",
            object_id=pk,
            ip_address=getattr(request, "client_ip", ""),
            description=f"Deleted dues record: {member_name} - {year}"
        )
        messages.success(request, f"Dues record deleted for {member_name} - {year}.")
        return redirect("finance:dues_tracker")

    return render(request, "finance/dues_confirm_delete.html", {"dues": dues})


# ============================================================
# INCOME LIST (SPLIT: DUES + DONATIONS)
# ============================================================

@login_required
def income_list(request):
    """List all income records split by Dues and Donations with totals."""
    # --- DUES (from Income records with income_type="DUES") ---
    dues_qs = Income.objects.filter(income_type="DUES").select_related(
        "created_by", "dues_payment", "dues_payment__member"
    ).order_by("-created_at")

    # --- DONATIONS & OTHER (non-dues income) ---
    donation_qs = Income.objects.exclude(income_type="DUES").select_related("created_by", "member")

    # Search/filter for donations
    search_term = request.GET.get("search", "")
    if search_term:
        donation_qs = donation_qs.filter(
            Q(reason__icontains=search_term) |
            Q(paid_by__icontains=search_term) |
            Q(member__full_name__icontains=search_term) |
            Q(created_by__full_name__icontains=search_term)
        )

    type_filter = request.GET.get("type", "")
    if type_filter:
        donation_qs = donation_qs.filter(income_type=type_filter)

    date_from = request.GET.get("date_from", "")
    date_to = request.GET.get("date_to", "")
    if date_from:
        dues_qs = dues_qs.filter(created_at__date__gte=date_from)
        donation_qs = donation_qs.filter(created_at__date__gte=date_from)
    if date_to:
        dues_qs = dues_qs.filter(created_at__date__lte=date_to)
        donation_qs = donation_qs.filter(created_at__date__lte=date_to)

    # Pagination for donations only
    paginator = Paginator(donation_qs, 25)
    page = request.GET.get("page", 1)
    donation_incomes = paginator.get_page(page)

    # Totals
    total_dues = Income.objects.filter(income_type="DUES").aggregate(
        total=Coalesce(Sum("amount"), Value(0, output_field=DecimalField()))
    )["total"]

    total_donations = Income.objects.exclude(income_type="DUES").aggregate(
        total=Coalesce(Sum("amount"), Value(0, output_field=DecimalField()))
    )["total"]

    total_income = total_dues + total_donations
    total_records = Income.objects.count()

    context = {
        "dues_incomes": dues_qs,
        "donation_incomes": donation_incomes,
        "search_term": search_term,
        "type_filter": type_filter,
        "date_from": date_from,
        "date_to": date_to,
        "total_dues": total_dues,
        "total_donations": total_donations,
        "total_income": total_income,
        "total_records": total_records,
    }
    return render(request, "finance/income_list.html", context)


@login_required
def income_create(request):
    """Create a new non-dues income record with member search."""
    if not request.user.has_executive_access():
        messages.error(request, "Executive access required.")
        return redirect("finance:donation_list")

    total_income = Income.objects.aggregate(total=Sum("amount"))["total"] or 0
    total_expenses = Expense.objects.aggregate(total=Sum("amount"))["total"] or 0
    treasury_balance = total_income - total_expenses

    recent_incomes = Income.objects.exclude(income_type="DUES").select_related("created_by", "member").order_by("-created_at")[:5]

    thirty_days_ago = timezone.now() - timedelta(days=30)
    common_reasons = (
        Income.objects.exclude(income_type="DUES").filter(created_at__gte=thirty_days_ago)
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
                description=f"Recorded {income.get_income_type_display()}: ₦{income.amount:,.2f} - {income.reason} (by {income.get_payer_display()})"
            )
            messages.success(request, "Income recorded successfully.")
            return redirect("finance:donation_list")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = IncomeForm()

    return render(request, "finance/income_form.html", {
        "form": form,
        "title": "Record Contribution",
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
    income = get_object_or_404(Income.objects.select_related("created_by", "member"), pk=pk)
    return render(request, "finance/income_detail.html", {"income": income})


@login_required
def income_delete(request, pk):
    """Delete an income record."""
    if not request.user.has_admin_access():
        messages.error(request, "Admin access required.")
        return redirect("finance:donation_list")

    income = get_object_or_404(Income, pk=pk)

    if request.method == "POST":
        amount = income.amount
        reason = income.reason
        income_type = income.get_income_type_display()
        income.delete()
        log_action(
            user=request.user,
            action="DELETE",
            object_type="Income",
            object_id=pk,
            ip_address=getattr(request, "client_ip", ""),
            description=f"Deleted {income_type}: ₦{amount:,.2f} - {reason}"
        )
        messages.success(request, "Income record deleted.")
        return redirect("finance:donation_list")

    return render(request, "finance/income_confirm_delete.html", {"income": income})


# ============================================================
# EXPENSES
# ============================================================

@login_required
def expense_list(request):
    """List all expense records with search and pagination."""
    queryset = Expense.objects.select_related("created_by").all()

    search_term = request.GET.get("search", "")
    if search_term:
        queryset = queryset.filter(
            Q(description__icontains=search_term) |
            Q(category__icontains=search_term) |
            Q(created_by__full_name__icontains=search_term)
        )

    category_filter = request.GET.get("category", "")
    if category_filter:
        queryset = queryset.filter(category=category_filter)

    date_from = request.GET.get("date_from", "")
    date_to = request.GET.get("date_to", "")
    if date_from:
        queryset = queryset.filter(created_at__date__gte=date_from)
    if date_to:
        queryset = queryset.filter(created_at__date__lte=date_to)

    paginator = Paginator(queryset, 25)
    page = request.GET.get("page", 1)
    expenses = paginator.get_page(page)

    total_expenses = Expense.objects.aggregate(total=Sum("amount"))["total"] or 0

    now = timezone.now()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    this_month_expenses = Expense.objects.filter(
        created_at__gte=month_start
    ).aggregate(total=Sum("amount"))["total"] or 0

    total_records = Expense.objects.count()
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
    """Create a new expense record."""
    if not request.user.has_executive_access():
        messages.error(request, "Executive access required.")
        return redirect("finance:expense_list")

    total_income = Income.objects.aggregate(total=Sum("amount"))["total"] or 0
    total_expenses = Expense.objects.aggregate(total=Sum("amount"))["total"] or 0
    treasury_balance = total_income - total_expenses

    recent_expenses = Expense.objects.select_related("created_by").order_by("-created_at")[:5]

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
                description=f"Recorded expense: ₦{expense.amount:,.2f} - {expense.category}"
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
            description=f"Deleted expense: ₦{amount:,.2f} - {category}"
        )
        messages.success(request, "Expense record deleted.")
        return redirect("finance:expense_list")

    return render(request, "finance/expense_confirm_delete.html", {"expense": expense})


# ============================================================
# FINANCE SUMMARY / DASHBOARD
# ============================================================

@login_required
def finance_summary(request):
    """Display financial summary with split KPIs."""
    current_year = timezone.now().year

    total_dues = Income.objects.filter(income_type="DUES").aggregate(
        total=Sum("amount")
    )["total"] or 0

    total_donations = Income.objects.exclude(income_type="DUES").aggregate(
        total=Sum("amount")
    )["total"] or 0

    total_income = total_dues + total_donations
    total_expenses = Expense.objects.aggregate(total=Sum("amount"))["total"] or 0
    treasury_balance = total_income - total_expenses

    active_members = User.objects.filter(is_active=True).count()
    years_count = current_year - PLATFORM_START_YEAR + 1
    total_dues_possible = active_members * years_count * YEARLY_DUES
    dues_collection_rate = round((total_dues / total_dues_possible * 100), 1) if total_dues_possible > 0 else 0

    this_year_dues_paid = DuesPayment.objects.filter(
        year=current_year,
        amount_paid__gte=YEARLY_DUES,
    ).count()
    this_year_dues_rate = round((this_year_dues_paid / active_members * 100), 1) if active_members > 0 else 0

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

    recent_income = list(Income.objects.select_related("created_by").all()[:10])
    recent_expenses = list(Expense.objects.select_related("created_by").all()[:10])

    for item in recent_income:
        item.type = "income"
    for item in recent_expenses:
        item.type = "expense"

    recent_transactions = sorted(
        recent_income + recent_expenses,
        key=lambda x: x.created_at,
        reverse=True
    )[:10]

    members = User.objects.filter(is_active=True)
    debtor_list = []
    for member in members:
        debt = DuesPayment.get_member_debt(member)
        if debt["debt_owed"] > 0:
            debtor_list.append({
                "member": member,
                "debt": debt["debt_owed"],
                "years_missed": len(debt["years_expected"]) - len(debt["years_paid"]),
            })

    debtor_list.sort(key=lambda x: x["debt"], reverse=True)
    top_debtors = debtor_list[:5]

    # Additional stats for dashboard
    partial_payments = DuesPayment.objects.filter(
        amount_paid__gt=0,
        amount_paid__lt=YEARLY_DUES,
    ).count()

    prepaid_count = DuesPayment.objects.filter(
        year__gt=current_year,
        amount_paid__gte=YEARLY_DUES,
    ).count()

    context = {
        "treasury_balance": treasury_balance,
        "total_income": total_income,
        "total_dues": total_dues,
        "total_donations": total_donations,
        "total_expenses": total_expenses,
        "total_transactions": Income.objects.count() + Expense.objects.count(),
        "expenses_by_category": expenses_by_category,
        "recent_transactions": recent_transactions,
        "active_members": active_members,
        "dues_collection_rate": dues_collection_rate,
        "this_year_dues_paid": this_year_dues_paid,
        "this_year_dues_rate": this_year_dues_rate,
        "top_debtors": top_debtors,
        "current_year": current_year,
        "partial_payments": partial_payments,
        "prepaid_count": prepaid_count,
    }
    return render(request, "finance/finance_summary.html", context)


# ============================================================
# AJAX ENDPOINTS
# ============================================================

@login_required
def search_members(request):
    """AJAX endpoint for member name auto-suggest."""
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
            f'<div class="search-result-item">'
            f'<div class="search-result-name">{u.get_full_name()}</div>'
            f'<div class="search-result-meta">{u.serial_number} · {u.get_role_display()}</div>'
            f'</div>'
        )
        results.append({
            "id": u.id,
            "text": f"{u.get_full_name()} ({u.serial_number})",
            "html": html,
            "name": u.full_name,
            "serial": u.serial_number,
            "role": u.get_role_display(),
        })

    return JsonResponse({"results": results})


@login_required
def member_dues_preview(request):
    """AJAX endpoint for dues allocation preview."""
    member_id = request.GET.get("member_id")
    if not member_id:
        return JsonResponse({"outstanding": []})

    try:
        member = User.objects.get(pk=member_id, is_active=True)
    except User.DoesNotExist:
        return JsonResponse({"outstanding": []})

    outstanding = DuesPayment.get_outstanding_years(member)
    data = []
    for item in outstanding:
        data.append({
            "year": item["year"],
            "amount_paid": float(item["amount_paid"]),
            "remaining_balance": float(item["remaining_balance"]),
            "status": item["status"],
        })

    return JsonResponse({"outstanding": data})
