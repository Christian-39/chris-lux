"""
Forms for OYA system settings.
"""
from django import forms
from .models import SystemSettings


class SystemSettingsForm(forms.ModelForm):
    """Form for updating system settings."""

    class Meta:
        model = SystemSettings
        fields = [
            "association_name", "motto",
            "logo", "favicon",
            "yearly_dues", "minimum_age", "past_member_age",
            "primary_color", "accent_color", "theme_mode"
        ]
        widgets = {
            "association_name": forms.TextInput(attrs={"class": "form-control"}),
            "motto": forms.TextInput(attrs={"class": "form-control"}),
            "logo": forms.ClearableFileInput(attrs={
                "class": "form-control",
                "accept": "image/png,image/jpeg,image/jpg,image/svg+xml,image/webp"
            }),
            "favicon": forms.ClearableFileInput(attrs={
                "class": "form-control",
                "accept": "image/x-icon,image/png,image/svg+xml"
            }),
            "yearly_dues": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.01",
                "min": "0"
            }),
            "minimum_age": forms.NumberInput(attrs={
                "class": "form-control",
                "min": "1",
                "max": "120"
            }),
            "past_member_age": forms.NumberInput(attrs={
                "class": "form-control",
                "min": "1",
                "max": "120"
            }),
            "primary_color": forms.TextInput(attrs={
                "class": "form-control",
                "type": "color"
            }),
            "accent_color": forms.TextInput(attrs={
                "class": "form-control",
                "type": "color"
            }),
            "theme_mode": forms.Select(attrs={"class": "form-select"}),
        }

    def clean_logo(self):
        logo = self.cleaned_data.get("logo")
        if logo:
            if logo.size > 2 * 1024 * 1024:
                raise forms.ValidationError("Logo must be under 2MB.")
            ext = logo.name.split(".")[-1].lower()
            if ext not in ["png", "jpg", "jpeg", "svg", "webp"]:
                raise forms.ValidationError("Logo must be PNG, JPG, SVG, or WEBP.")
        return logo

    def clean_favicon(self):
        favicon = self.cleaned_data.get("favicon")
        if favicon:
            if favicon.size > 1 * 1024 * 1024:
                raise forms.ValidationError("Favicon must be under 1MB.")
            ext = favicon.name.split(".")[-1].lower()
            if ext not in ["ico", "png", "svg"]:
                raise forms.ValidationError("Favicon must be ICO, PNG, or SVG.")
        return favicon

    def clean(self):
        cleaned_data = super().clean()
        min_age = cleaned_data.get("minimum_age")
        past_age = cleaned_data.get("past_member_age")

        if min_age and past_age and past_age <= min_age:
            raise forms.ValidationError(
                "Past member age must be greater than minimum age."
            )

        return cleaned_data
