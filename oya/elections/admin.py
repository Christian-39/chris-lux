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
    list_display = ["executive", "election", "bank_balance", "cash_balance", "total_balance", "created_at"]
    list_filter = ["election"]
    search_fields = ["executive__member__full_name", "election__title"]
    list_select_related = ["executive__member", "election"]
