"""
Admin configuration for projects app.
"""
from django.contrib import admin
from .models import Project


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ["title", "budget", "status", "progress_percentage", "created_at"]
    list_filter = ["status", "created_at"]
    search_fields = ["title", "description"]
    ordering = ["-created_at"]
    date_hierarchy = "created_at"
