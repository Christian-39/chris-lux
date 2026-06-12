"""
Forms for OYA projects.
"""
from django import forms
from .models import Project


class ProjectForm(forms.ModelForm):
    """Form for creating and updating projects."""

    class Meta:
        model = Project
        fields = ["title", "budget", "description", "status", "progress_percentage"]
        widgets = {
            "title": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Project title"
            }),
            "budget": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.01",
                "min": "0",
                "placeholder": "0.00"
            }),
            "description": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 6,
                "placeholder": "Project description..."
            }),
            "status": forms.Select(attrs={"class": "form-select"}),
            "progress_percentage": forms.NumberInput(attrs={
                "class": "form-control",
                "min": "0",
                "max": "100",
                "placeholder": "0-100"
            }),
        }

    def clean_progress_percentage(self):
        progress = self.cleaned_data.get("progress_percentage")
        if progress is not None and (progress < 0 or progress > 100):
            raise forms.ValidationError("Progress must be between 0 and 100.")
        return progress

    def clean_budget(self):
        budget = self.cleaned_data.get("budget")
        if budget and budget < 0:
            raise forms.ValidationError("Budget cannot be negative.")
        return budget
