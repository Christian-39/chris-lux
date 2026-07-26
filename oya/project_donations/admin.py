"""
Admin configuration for OYA Project Donations.
"""
from django.contrib import admin
from .models import OutsideDonor, Donation


@admin.register(OutsideDonor)
class OutsideDonorAdmin(admin.ModelAdmin):
    list_display = [
        "full_name", "phone_number", "occupation",
        "invited_by", "created_at", "total_donations"
    ]
    list_filter = ["gender", "created_at"]
    search_fields = [
        "full_name", "phone_number", "occupation",
        "invited_by__full_name"
    ]
    raw_id_fields = ["invited_by"]
    date_hierarchy = "created_at"
    readonly_fields = ["total_donations", "donation_count", "projects_supported"]


@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display = [
        "project", "donor_type", "get_donor_name", "amount",
        "donation_date", "status", "recorded_by"
    ]
    list_filter = [
        "donor_type", "status", "payment_method", "donation_date"
    ]
    search_fields = [
        "project__title", "member__full_name", "outside_donor__full_name",
        "reference_number", "narration"
    ]
    raw_id_fields = [
        "project", "member", "outside_donor", "invited_by", "recorded_by"
    ]
    date_hierarchy = "donation_date"

    def get_donor_name(self, obj):
        if obj.member:
            return obj.member.full_name
        elif obj.outside_donor:
            return obj.outside_donor.full_name
        return "Anonymous"
    get_donor_name.short_description = "Donor"