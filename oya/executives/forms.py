"""
Forms for OYA executives.
"""
from django import forms
from django.utils import timezone
from .models import Executive


class ExecutiveForm(forms.ModelForm):
    """Form for creating and updating executives."""

    class Meta:
        model = Executive
        fields = ["member", "post", "start_date", "end_date", "is_current"]
        widgets = {
            "member": forms.Select(attrs={"class": "form-select"}),
            "post": forms.Select(attrs={"class": "form-select"}),
            "start_date": forms.DateInput(attrs={
                "class": "form-control",
                "type": "date"
            }),
            "end_date": forms.DateInput(attrs={
                "class": "form-control",
                "type": "date"
            }),
            "is_current": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }

    def clean(self):
        cleaned_data = super().clean()
        end_date = cleaned_data.get("end_date")
        is_current = cleaned_data.get("is_current")

        if end_date and is_current:
            raise forms.ValidationError(
                "An executive with an end date cannot be marked as current."
            )

        if not end_date and not is_current:
            raise forms.ValidationError(
                "Either set an end date or mark as current."
            )

        return cleaned_data
