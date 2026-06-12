"""
Admin configuration for finance app.
"""
from django.contrib import admin
from .models import Income, Expense


@admin.register(Income)
class IncomeAdmin(admin.ModelAdmin):
    list_display = ["reason", "amount", "paid_by", "created_by", "created_at"]
    list_filter = ["created_at"]
    search_fields = ["reason", "paid_by"]
    ordering = ["-created_at"]
    date_hierarchy = "created_at"


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ["category", "amount", "description", "created_by", "created_at"]
    list_filter = ["category", "created_at"]
    search_fields = ["description", "category"]
    ordering = ["-created_at"]
    date_hierarchy = "created_at"
