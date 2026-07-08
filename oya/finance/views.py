"""Updated views for OYA finance with smart dues allocation."""
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count, Max, Value, DecimalField
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.http import JsonResponse
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

    paginator = Paginator(queryset, 10)
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

    # Include all registered members in dues tracking.
    # Exclude staff and superuser accounts — only real members should appear.
    members = User.objects.filter(
        serial_number__isnull=False
    ).exclude(
        serial_number=""
    ).exclude(
        is_staff=True
    ).exclude(
        is_superuser=True
    ).order_by("full_name")

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
        try:
            member_debt = DuesPayment.get_member_debt(member)
        except Exception as e:
            logger.warning(f"Could not get member debt for {member}: {e}")
            member_debt = {
                "debt_owed": Decimal("0"),
                "years_paid": [],
                "years_partial": [],
                "years_expected": [],
                "join_year": PLATFORM_START_YEAR,
            }
        row["total_debt"] = member_debt.get("debt_owed", Decimal("0"))
        row["years_paid_count"] = len(member_debt.get("years_paid", []))
        row["years_partial_count"] = len(member_debt.get("years_partial", []))
        row["join_year"] = member_debt.get("join_year", PLATFORM_START_YEAR)

        for year in years:
            key = (member.id, year)
            # Check if year is before member's join year
            if year < row["join_year"]:
                row["years"][year] = {
                    "status": DuesPayment.STATUS_NOT_APPLICABLE,
                    "payment": None,
                    "amount_paid": Decimal("0"),
                    "remaining": Decimal("0"),
                    "before_join": True,
                }
            elif key in dues_map:
                dp = dues_map[key]
                row["years"][year] = {
                    "status": dp.status,
                    "payment": dp,
                    "amount_paid": dp.amount_paid,
                    "remaining": dp.remaining_balance,
                    "before_join": False,
                }
                total_dues_collected += dp.amount_paid
            else:
                row["years"][year] = {
                    "status": DuesPayment.STATUS_OWED,
                    "payment": None,
                    "amount_paid": Decimal("0"),
                    "remaining": Decimal(str(YEARLY_DUES)),
                    "before_join": False,
                }
                total_dues_expected += YEARLY_DUES

        member_rows.append(row)

    active_members_count = members.count()
    # Adjust total possible dues to only count years from each member's join year
    total_possible_dues = Decimal("0")
    for m in members:
        try:
            join_year = DuesPayment.get_member_join_year(m)
        except Exception:
            join_year = PLATFORM_START_YEAR
        total_possible_dues += (current_year - max(join_year, PLATFORM_START_YEAR) + 1) * YEARLY_DUES
    collection_rate = round(
        (float(total_dues_collected) / float(total_possible_dues) * 100), 1
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
    member = get_object_or_404(User, pk=member_id)
    current_year = timezone.now().year

    # Get join year to determine range
    join_year = DuesPayment.get_member_join_year(member)
    start_year = PLATFORM_START_YEAR  # Always show from platform start for context

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
        # Years before join year are marked as N/A
        if year < join_year:
            year_status.append({
                "year": year,
                "status": DuesPayment.STATUS_NOT_APPLICABLE,
                "payment": None,
                "is_future": year > current_year,
                "before_join": True,
            })
        else:
            payment = payments.filter(year=year).first()
            year_status.append({
                "year": year,
                "status": payment.status if payment else DuesPayment.STATUS_OWED,
                "payment": payment,
                "is_future": year > current_year,
                "before_join": False,
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
        "join_year": join_year,
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
    """List all income records split by Dues (grouped by transaction) and Donations with totals."""
    
    # --- DUES (grouped by DuesPaymentTransaction) ---
    dues_txns_qs = DuesPaymentTransaction.objects.select_related(
        "member", "recorded_by"
    ).order_by("-payment_date")
    
    # --- DONATIONS & OTHER (non-dues income) ---
    donation_qs = Income.objects.exclude(income_type="DUES").select_related("created_by", "member")

    # Search/filter
    search_term = request.GET.get("search", "")
    if search_term:
        donation_qs = donation_qs.filter(
            Q(reason__icontains=search_term) |
            Q(paid_by__icontains=search_term) |
            Q(member__full_name__icontains=search_term) |
            Q(created_by__full_name__icontains=search_term)
        )
        dues_txns_qs = dues_txns_qs.filter(
            Q(member__full_name__icontains=search_term) |
            Q(receipt_reference__icontains=search_term) |
            Q(recorded_by__full_name__icontains=search_term)
        )

    type_filter = request.GET.get("type", "")
    if type_filter:
        donation_qs = donation_qs.filter(income_type=type_filter)

    date_from = request.GET.get("date_from", "")
    date_to = request.GET.get("date_to", "")
    if date_from:
        donation_qs = donation_qs.filter(created_at__date__gte=date_from)
        dues_txns_qs = dues_txns_qs.filter(payment_date__gte=date_from)
    if date_to:
        donation_qs = donation_qs.filter(created_at__date__lte=date_to)
        dues_txns_qs = dues_txns_qs.filter(payment_date__lte=date_to)

    # Build grouped dues data for display
    current_year = timezone.now().year
    dues_grouped = []
    for txn in dues_txns_qs:
        dues_records = DuesPayment.objects.filter(
            transactions=txn
        ).values_list("year", flat=True).order_by("year")
        
        years_list = list(dues_records)
        if years_list:
            if len(years_list) == 1:
                year_display = str(years_list[0])
                reason = f"Yearly Dues — {year_display}"
            else:
                year_display = f"{years_list[0]}–{years_list[-1]}"
                has_prepaid = any(y > current_year for y in years_list)
                prepaid_label = " (Prepaid)" if has_prepaid else ""
                reason = f"Yearly Dues — {year_display}{prepaid_label}"
        else:
            reason = "Yearly Dues"
        
        dues_grouped.append({
            "transaction": txn,
            "reason": reason,
            "amount": txn.total_amount,
            "member": txn.member,
            "recorded_by": txn.recorded_by,
            "payment_date": txn.payment_date,
            "years": years_list,
            "is_prepaid": any(y > current_year for y in years_list) if years_list else False,
        })

    # Pagination for DUES (grouped transactions)
    dues_paginator = Paginator(dues_grouped, 10)
    dues_page = request.GET.get("dues_page", 1)
    dues_incomes = dues_paginator.get_page(dues_page)

    # Pagination for DONATIONS
    donation_paginator = Paginator(donation_qs, 10)
    donation_page = request.GET.get("page", 1)
    donation_incomes = donation_paginator.get_page(donation_page)

    # Totals (use full QS, not paginated)
    total_dues = Income.objects.filter(income_type="DUES").aggregate(
        total=Coalesce(Sum("amount"), Value(0, output_field=DecimalField()))
    )["total"]

    total_donations = Income.objects.exclude(income_type="DUES").aggregate(
        total=Coalesce(Sum("amount"), Value(0, output_field=DecimalField()))
    )["total"]

    total_income = total_dues + total_donations
    total_records = Income.objects.count()

    context = {
        "dues_incomes": dues_incomes,
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

    paginator = Paginator(queryset, 10)
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

    # FIX Issue 3: Count only registered members (exclude admins, staff, system users)
    active_members = User.objects.filter(
        is_active=True,
        serial_number__isnull=False
    ).exclude(
        serial_number=""
    ).exclude(
        is_staff=True
    ).exclude(
        is_superuser=True
    ).count()

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

        # ===================================================================
    # FIX: Group dues payments by transaction instead of showing each year
    # ===================================================================
    
    recent_dues_txns = DuesPaymentTransaction.objects.select_related(
        "member", "recorded_by"
    ).order_by("-payment_date")[:5]
    
    recent_donations = Income.objects.exclude(
        income_type="DUES"
    ).select_related("created_by", "member").order_by("-created_at")[:5]
    
    recent_expenses = Expense.objects.select_related("created_by").order_by("-created_at")[:5]
    
    recent_transactions = []
    
    for txn in recent_dues_txns:
        dues_records = DuesPayment.objects.filter(
            transactions=txn
        ).values_list("year", flat=True).order_by("year")
        
        years_list = list(dues_records)
        if years_list:
            if len(years_list) == 1:
                year_display = str(years_list[0])
                description = f"Yearly Dues {year_display}"
            else:
                year_display = f"{years_list[0]}–{years_list[-1]}"
                has_prepaid = any(y > current_year for y in years_list)
                prepaid_label = " (Prepaid)" if has_prepaid else ""
                description = f"Yearly Dues ({year_display}){prepaid_label}"
        else:
            description = "Yearly Dues"
        
        recent_transactions.append({
            "type": "dues_transaction",
            "amount": txn.total_amount,
            "description": description,
            "reason": description,
            "created_at": txn.payment_date,
            "payment_date": txn.payment_date,
            "member": txn.member,
            "recorded_by": txn.recorded_by,
            "transaction_id": txn.id,
            "income_type": "DUES",
            "years": years_list,
            "is_prepaid": any(y > current_year for y in years_list) if years_list else False,
        })
    
    for income in recent_donations:
        recent_transactions.append({
            "type": "income",
            "amount": income.amount,
            "description": income.reason,
            "reason": income.reason,
            "created_at": income.created_at,
            "income_type": income.income_type,
            "income_object": income,
            "member": income.member,
            "created_by": income.created_by,
            "paid_by": income.paid_by,
        })
    
    for expense in recent_expenses:
        recent_transactions.append({
            "type": "expense",
            "amount": expense.amount,
            "description": expense.description,
            "reason": expense.description,
            "created_at": expense.created_at,
            "category": expense.category,
            "expense_object": expense,
            "created_by": expense.created_by,
        })
    
    recent_transactions.sort(key=lambda x: x["created_at"], reverse=True)
    recent_transactions = recent_transactions[:5]


    # FIX: Only include actual members (not staff/superusers) in debtor list
    members = User.objects.filter(
        is_active=True,
        serial_number__isnull=False
    ).exclude(
        serial_number=""
    ).exclude(
        is_staff=True
    ).exclude(
        is_superuser=True
    )

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
    ).filter(
        serial_number__isnull=False
    ).exclude(
        serial_number=""
    ).exclude(
        is_staff=True
    ).exclude(
        is_superuser=True
    ).distinct()[:10]

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
        member = User.objects.get(pk=member_id)
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

# ============================================================
# PREPAID DUES
# ============================================================

@login_required
def prepaid_list(request):
    """List all members with prepaid dues (future years fully paid) — grouped by member."""
    current_year = timezone.now().year

    # Get all prepaid dues payments (year > current_year, fully paid)
    prepaid_members_qs = DuesPayment.objects.filter(
        year__gt=current_year,
        amount_paid__gte=YEARLY_DUES,
    ).select_related("member", "recorded_by").order_by("member__full_name", "-year")

    # Group by member: collect years and total amounts
    member_prepaid_map = {}
    for dp in prepaid_members_qs:
        member_id = dp.member_id
        if member_id not in member_prepaid_map:
            member_prepaid_map[member_id] = {
                "member": dp.member,
                "years": [],
                "total_amount": Decimal("0"),
                "latest_recorded_by": dp.recorded_by,
                "latest_date": dp.created_at,
            }
        member_prepaid_map[member_id]["years"].append(dp.year)
        member_prepaid_map[member_id]["total_amount"] += dp.amount_paid
        if dp.created_at > member_prepaid_map[member_id]["latest_date"]:
            member_prepaid_map[member_id]["latest_date"] = dp.created_at
            member_prepaid_map[member_id]["latest_recorded_by"] = dp.recorded_by

    # Build grouped records list
    prepaid_grouped = []
    for member_id, data in member_prepaid_map.items():
        years_sorted = sorted(data["years"])
        if len(years_sorted) == 1:
            year_display = str(years_sorted[0])
        else:
            year_display = f"{years_sorted[0]}–{years_sorted[-1]}"
        
        prepaid_grouped.append({
            "member": data["member"],
            "years": years_sorted,
            "year_display": year_display,
            "total_amount": data["total_amount"],
            "recorded_by": data["latest_recorded_by"],
            "created_at": data["latest_date"],
            "year_count": len(years_sorted),
        })

    # Sort by total amount (highest first)
    prepaid_grouped.sort(key=lambda x: x["total_amount"], reverse=True)

    # Calculate totals
    total_prepaid_amount = sum(item["total_amount"] for item in prepaid_grouped)
    total_prepaid_records = len(prepaid_grouped)
    prepaid_members_count = len(prepaid_grouped)

    # Get unique future years covered
    all_years = set()
    for item in prepaid_grouped:
        all_years.update(item["years"])
    years_with_prepaid = sorted(all_years, reverse=True)

    context = {
        "prepaid_records": prepaid_grouped,
        "total_prepaid_amount": total_prepaid_amount,
        "total_prepaid_records": total_prepaid_records,
        "prepaid_members_count": prepaid_members_count,
        "years_with_prepaid": years_with_prepaid,
        "current_year": current_year,
        "yearly_dues": YEARLY_DUES,
    }
    return render(request, "finance/prepaid_list.html", context)



@login_required
def prepaid_detail(request, member_id):
    """Show prepaid dues details for a specific member."""
    member = get_object_or_404(User, pk=member_id)
    current_year = timezone.now().year

    # Get all prepaid records for this member
    prepaid_records = DuesPayment.objects.filter(
        member=member,
        year__gt=current_year,
    ).select_related("recorded_by", "income").order_by("-year")

    # Calculate total prepaid
    total_prepaid = prepaid_records.aggregate(
        total=Sum("amount_paid")
    )["total"] or Decimal("0")

    # Get member's debt info for context
    debt_info = DuesPayment.get_member_debt(member)

    context = {
        "member": member,
        "prepaid_records": prepaid_records,
        "total_prepaid": total_prepaid,
        "debt_info": debt_info,
        "current_year": current_year,
        "yearly_dues": YEARLY_DUES,
    }
    return render(request, "finance/prepaid_detail.html", context)

