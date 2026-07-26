"""
Forms for OYA Project Donations.
"""
from django import forms
from django.core.exceptions import ValidationError
from decimal import Decimal
from .models import OutsideDonor, Donation
from members.models import Member


class OutsideDonorForm(forms.ModelForm):
    """Form for creating and updating outside donors."""

    class Meta:
        model = OutsideDonor
        fields = [
            "full_name", "profile_picture", "phone_number", "address",
            "gender", "occupation", "notes", "invited_by"
        ]
        widgets = {
            "full_name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Full Name"
            }),
            "profile_picture": forms.FileInput(attrs={
                "class": "form-control"
            }),
            "phone_number": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Phone Number"
            }),
            "address": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 2,
                "placeholder": "Address"
            }),
            "gender": forms.Select(attrs={
                "class": "form-select"
            }),
            "occupation": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Occupation"
            }),
            "notes": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Additional notes..."
            }),
            "invited_by": forms.Select(attrs={
                "class": "form-select"
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["invited_by"].queryset = Member.objects.filter(
            status="ACTIVE"
        ).order_by("full_name")
        self.fields["invited_by"].empty_label = "-- Select Member Who Invited --"
        self.fields["invited_by"].required = True


class DonationForm(forms.ModelForm):
    """Form for creating and updating donations."""

    class Meta:
        model = Donation
        fields = [
            "project", "donor_type", "member", "outside_donor", "invited_by",
            "amount", "payment_method", "reference_number", "narration",
            "donation_date", "status"
        ]
        widgets = {
            "project": forms.Select(attrs={"class": "form-select"}),
            "donor_type": forms.Select(attrs={
                "class": "form-select",
                "id": "id_donor_type"
            }),
            "member": forms.Select(attrs={
                "class": "form-select",
                "id": "id_member"
            }),
            "outside_donor": forms.Select(attrs={
                "class": "form-select",
                "id": "id_outside_donor"
            }),
            "invited_by": forms.Select(attrs={"class": "form-select"}),
            "amount": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.01",
                "min": "0.01",
                "placeholder": "0.00"
            }),
            "payment_method": forms.Select(attrs={"class": "form-select"}),
            "reference_number": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Reference / Receipt Number"
            }),
            "narration": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 2,
                "placeholder": "Narration or notes..."
            }),
            "donation_date": forms.DateInput(attrs={
                "class": "form-control",
                "type": "date"
            }),
            "status": forms.Select(attrs={"class": "form-select"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["member"].queryset = Member.objects.filter(
            status="ACTIVE"
        ).order_by("full_name")
        self.fields["member"].empty_label = "-- Select Member --"
        self.fields["member"].required = False

        self.fields["outside_donor"].queryset = OutsideDonor.objects.select_related(
            "invited_by"
        ).order_by("full_name")
        self.fields["outside_donor"].empty_label = "-- Select Outside Donor --"
        self.fields["outside_donor"].required = False

        self.fields["invited_by"].queryset = Member.objects.filter(
            status="ACTIVE"
        ).order_by("full_name")
        self.fields["invited_by"].empty_label = "-- Select Inviting Member --"
        self.fields["invited_by"].required = False

        # Only show projects with fundraising enabled, but keep current project on edit
        from django.db.models import Q
        from projects.models import Project
        qs = Project.objects.filter(enable_fundraising=True)
        if self.instance and self.instance.pk and self.instance.project_id:
            qs = Project.objects.filter(
                Q(enable_fundraising=True) | Q(pk=self.instance.project_id)
            )
        self.fields["project"].queryset = qs.order_by("-created_at")
        self.fields["project"].empty_label = "-- Select Fundraising Project --"

    def clean(self):
        cleaned = super().clean()
        donor_type = cleaned.get("donor_type")
        member = cleaned.get("member")
        outside_donor = cleaned.get("outside_donor")

        if donor_type == "MEMBER":
            if not member:
                self.add_error("member", "Please select a member.")
            if outside_donor:
                self.add_error("outside_donor", "Clear outside donor for member donations.")
        elif donor_type == "OUTSIDE":
            if not outside_donor:
                self.add_error("outside_donor", "Please select an outside donor.")
            if member:
                self.add_error("member", "Clear member for outside donations.")

        return cleaned

    def clean_amount(self):
        amount = self.cleaned_data.get("amount")
        if amount and amount <= 0:
            raise ValidationError("Amount must be greater than zero.")
        return amount