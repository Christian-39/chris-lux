"""
Forms for OYA finance.
"""
from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Income, Expense, DuesPayment


class IncomeForm(forms.ModelForm):
    """Form for creating and updating income records (Donations, Events, Other)."""

    class Meta:
        model = Income
        fields = ["income_type", "amount", "reason", "paid_by"]
        widgets = {
            "income_type": forms.Select(attrs={"class": "form-select"}),
            "amount": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.01",
                "min": "0.01",
                "placeholder": "0.00"
            }),
            "reason": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "e.g., Donation for project, Event ticket sales"
            }),
            "paid_by": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Name of payer / contributor"
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["income_type"].initial = "DONATION"
        choices = [c for c in Income.INCOME_TYPE_CHOICES if c[0] != "DUES"]
        self.fields["income_type"].choices = choices

    def clean_amount(self):
        amount = self.cleaned_data.get("amount")
        if amount and amount <= 0:
            raise ValidationError("Amount must be greater than zero.")
        return amount


class DuesPaymentForm(forms.ModelForm):
    """
    Form for recording yearly dues payments.
    Auto-creates the linked Income record.
    """
    member_search = forms.CharField(
        required=False,
        widget=forms.HiddenInput(),
    )

    class Meta:
        model = DuesPayment
        fields = ["member", "year", "notes"]
        widgets = {
            "member": forms.Select(attrs={
                "class": "form-select",
                "data-search": "members",
            }),
            "year": forms.NumberInput(attrs={
                "class": "form-control",
                "min": "2020",
                "max": str(timezone.now().year),
                "placeholder": "e.g., 2024",
            }),
            "notes": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 2,
                "placeholder": "Payment method, reference number, etc.",
            }),
        }

    def __init__(self, *args, **kwargs):
        self.recorded_by = kwargs.pop("recorded_by", None)
        super().__init__(*args, **kwargs)
        self.fields["year"].initial = timezone.now().year

    def clean_year(self):
        year = self.cleaned_data.get("year")
        current_year = timezone.now().year
        if year < 2020:
            raise ValidationError("Dues year cannot be before 2020.")
        if year > current_year:
            raise ValidationError("Cannot record dues for future years.")
        return year

    def clean(self):
        cleaned_data = super().clean()
        member = cleaned_data.get("member")
        year = cleaned_data.get("year")

        if member and year:
            existing = DuesPayment.objects.filter(member=member, year=year)
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists():
                raise ValidationError(
                    f"Dues for {year} have already been recorded for {member.get_full_name()}."
                )
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.amount_paid = DuesPayment.YEARLY_DUES_AMOUNT
        instance.recorded_by = self.recorded_by

        if commit:
            income = Income.objects.create(
                income_type="DUES",
                amount=DuesPayment.YEARLY_DUES_AMOUNT,
                reason=f"Yearly Dues \u2014 {instance.year}",
                paid_by=instance.member.get_full_name(),
                created_by=self.recorded_by,
            )
            instance.income = income
            instance.save()
        return instance


class ExpenseForm(forms.ModelForm):
    """Form for creating and updating expense records."""

    class Meta:
        model = Expense
        fields = ["amount", "category", "description", "receipt_file"]
        widgets = {
            "amount": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.01",
                "min": "0.01",
                "placeholder": "0.00"
            }),
            "category": forms.Select(attrs={"class": "form-select"}),
            "description": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": "Describe the expense..."
            }),
            "receipt_file": forms.FileInput(attrs={
                "class": "form-control",
                "accept": ".pdf,.jpg,.jpeg,.png"
            }),
        }

    def clean_amount(self):
        amount = self.cleaned_data.get("amount")
        if amount and amount <= 0:
            raise ValidationError("Amount must be greater than zero.")
        return amount

    def clean_receipt_file(self):
        receipt = self.cleaned_data.get("receipt_file")
        if receipt:
            if receipt.size > 10 * 1024 * 1024:
                raise ValidationError("Receipt file must be under 10MB.")
        return receipt
