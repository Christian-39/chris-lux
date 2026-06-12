"""
Forms for OYA finance.
"""
from django import forms
from .models import Income, Expense


class IncomeForm(forms.ModelForm):
    """Form for creating and updating income records."""

    class Meta:
        model = Income
        fields = ["amount", "reason", "paid_by"]
        widgets = {
            "amount": forms.NumberInput(attrs={
                "class": "form-control",
                "step": "0.01",
                "min": "0.01",
                "placeholder": "0.00"
            }),
            "reason": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "e.g., Annual Dues, Donation"
            }),
            "paid_by": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Name of payer"
            }),
        }

    def clean_amount(self):
        amount = self.cleaned_data.get("amount")
        if amount and amount <= 0:
            raise forms.ValidationError("Amount must be greater than zero.")
        return amount


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
            raise forms.ValidationError("Amount must be greater than zero.")
        return amount

    def clean_receipt_file(self):
        receipt = self.cleaned_data.get("receipt_file")
        if receipt:
            if receipt.size > 10 * 1024 * 1024:  # 10MB limit
                raise forms.ValidationError("Receipt file must be under 10MB.")
        return receipt
