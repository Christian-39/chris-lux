"""
Forms for OYA operations.
"""
from django import forms
from .models import TaskForceMember, Motorcycle, CaseFile


class TaskForceMemberForm(forms.ModelForm):
    """Form for creating and updating task force members."""

    class Meta:
        model = TaskForceMember
        fields = ["member", "assigned_date", "notes", "is_active"]
        widgets = {
            "member": forms.Select(attrs={"class": "form-select"}),
            "assigned_date": forms.DateInput(attrs={
                "class": "form-control",
                "type": "date"
            }),
            "notes": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Additional notes..."
            }),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }


class MotorcycleForm(forms.ModelForm):
    """Form for creating and updating motorcycle records."""

    class Meta:
        model = Motorcycle
        fields = ["asset_tag", "brand", "model", "year", "condition", "assigned_to"]
        widgets = {
            "asset_tag": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "e.g., OYA-MC-001"
            }),
            "brand": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "e.g., Honda"
            }),
            "model": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "e.g., CG125"
            }),
            "year": forms.NumberInput(attrs={
                "class": "form-control",
                "min": "1900",
                "max": "2099"
            }),
            "condition": forms.Select(attrs={"class": "form-select"}),
            "assigned_to": forms.Select(attrs={"class": "form-select"}),
        }


class CaseFileForm(forms.ModelForm):
    """Form for creating and updating case files."""

    class Meta:
        model = CaseFile
        fields = [
            "case_number", "title", "description",
            "fine_amount", "status", "respondent"
        ]
        widgets = {
            "case_number": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "e.g., CASE-2026-001"
            }),
            "title": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Case title"
            }),
            "description": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 6,
                "placeholder": "Detailed description of the case..."
            }),
            "fine_amount": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.01",
                "min": "0",
                "placeholder": "0.00"
            }),
            "status": forms.Select(attrs={"class": "form-select"}),
            "respondent": forms.Select(attrs={"class": "form-select"}),
        }


class CaseResolutionForm(forms.ModelForm):
    """Form for resolving a case."""

    class Meta:
        model = CaseFile
        fields = ["status", "resolution_notes", "resolved_date"]
        widgets = {
            "status": forms.Select(attrs={"class": "form-select"}),
            "resolution_notes": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": "Resolution details..."
            }),
            "resolved_date": forms.DateInput(attrs={
                "class": "form-control",
                "type": "date"
            }),
        }
