"""
Admin configuration for elections app.
"""
from django.contrib import admin
from .models import Election, Candidate, HandoverLedger


@admin.register(Election)
class ElectionAdmin(admin.ModelAdmin):
    list_display = ["title", "start_date", "end_date", "status", "created_at"]
    list_filter = ["status", "start_date"]
    search_fields = ["title", "description"]
    ordering = ["-created_at"]


@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ["member", "election", "post", "votes", "created_at"]
    list_filter = ["election", "post"]
    search_fields = ["member__full_name", "post"]
    list_select_related = ["member", "election"]


@admin.register(HandoverLedger)
class HandoverLedgerAdmin(admin.ModelAdmin):
    list_display = [
        "executive", "election", "tenure_start", "tenure_end",
        "total_balance", "net_financial_position", "created_at"
    ]
    list_filter = ["election", "tenure_start"]
    search_fields = ["executive__member__full_name", "election__title", "notes"]
    list_select_related = ["executive__member", "election"]
    readonly_fields = [
        "total_income", "total_dues", "total_donations", "taskforce_revenue",
        "total_expenses", "taskforce_total", "taskforce_active", "taskforce_inactive",
        "motorcycle_total", "motorcycle_excellent", "motorcycle_needs_service",
        "motorcycle_grounded", "cases_total", "cases_open", "cases_in_progress",
        "cases_resolved", "projects_completed", "projects_at_hand", "projects_future",
        "created_at", "updated_at"
    ]
    fieldsets = (
        ("Basic Info", {
            "fields": ("election", "executive", "tenure_start", "tenure_end", "notes")
        }),
        ("Physical Balances", {
            "fields": ("bank_balance", "cash_balance", "assets_description")
        }),
        ("Auto-Calculated Finance", {
            "fields": (
                "total_income", "total_dues", "total_donations",
                "taskforce_revenue", "total_expenses"
            ),
            "description": "These fields are auto-calculated from the tenure date range."
        }),
        ("Auto-Calculated Operations", {
            "fields": (
                ("taskforce_total", "taskforce_active", "taskforce_inactive"),
                ("motorcycle_total", "motorcycle_excellent", "motorcycle_needs_service", "motorcycle_grounded"),
                ("cases_total", "cases_open", "cases_in_progress", "cases_resolved"),
            )
        }),
        ("Auto-Calculated Projects", {
            "fields": ("projects_completed", "projects_at_hand", "projects_future")
        }),
    )
