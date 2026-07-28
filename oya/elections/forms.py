"""
Forms for OYA elections.
"""
from django import forms
from django.core.exceptions import ValidationError
from .models import Election, Candidate, HandoverLedger
from executives.models import Executive


class ElectionForm(forms.ModelForm):
    """Form for creating and updating elections."""

    class Meta:
        model = Election
        fields = ["title", "start_date", "end_date", "status", "description"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "start_date": forms.DateTimeInput(attrs={
                "class": "form-control",
                "type": "datetime-local"
            }),
            "end_date": forms.DateTimeInput(attrs={
                "class": "form-control",
                "type": "datetime-local"
            }),
            "status": forms.Select(attrs={"class": "form-select"}),
            "description": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 4
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")

        if start_date and end_date and end_date <= start_date:
            raise ValidationError("End date must be after start date.")

        return cleaned_data


class CandidateForm(forms.ModelForm):
    """Form for creating and updating candidates."""

    class Meta:
        model = Candidate
        fields = ["election", "member", "post", "photo", "manifesto"]
        widgets = {
            "election": forms.Select(attrs={"class": "form-select"}),
            "member": forms.Select(attrs={"class": "form-select"}),
            "post": forms.Select(attrs={"class": "form-select"}),
            "photo": forms.FileInput(attrs={"class": "form-control"}),
            "manifesto": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 6,
                "placeholder": "Candidate manifesto..."
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Populate post choices dynamically from Executive.POST_CHOICES
        self.fields["post"].widget = forms.Select(
            attrs={"class": "form-select"},
            choices=Executive.POST_CHOICES
        )
        self.fields["post"].choices = [("", "Select position")] + list(Executive.POST_CHOICES)


class HandoverLedgerForm(forms.ModelForm):
    """Form for creating and updating comprehensive handover ledgers."""

    class Meta:
        model = HandoverLedger
        fields = [
            "election", "executive", "tenure_start", "tenure_end",
            "bank_balance", "cash_balance",
            "assets_description", "notes"
        ]
        widgets = {
            "election": forms.Select(attrs={"class": "form-select"}),
            "executive": forms.Select(attrs={"class": "form-select"}),
            "tenure_start": forms.DateInput(attrs={
                "class": "form-control",
                "type": "date"
            }),
            "tenure_end": forms.DateInput(attrs={
                "class": "form-control",
                "type": "date"
            }),
            "bank_balance": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.01",
                "min": "0",
                "placeholder": "0.00"
            }),
            "cash_balance": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.01",
                "min": "0",
                "placeholder": "0.00"
            }),
            "assets_description": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": "List all assets being handed over (motorcycles, equipment, documents, etc.)..."
            }),
            "notes": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Additional notes about the handover..."
            }),
        }

        def clean(self):
        cleaned_data = super().clean()
        tenure_start = cleaned_data.get("tenure_start")
        tenure_end = cleaned_data.get("tenure_end")
        
        if tenure_start and tenure_end and tenure_end < tenure_start:
            raise ValidationError("Tenure end date cannot be before start date.")
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        # Auto-calculate all aggregates before saving
        instance.recalculate_aggregates()
        if commit:
            instance.save()
        return instance
