"""
Notification Forms
"""
from django import forms
from .models import Notification, NotificationTemplate, BulkNotification


class NotificationForm(forms.ModelForm):
    """Form for creating/editing notifications"""
    class Meta:
        model = Notification
        fields = ['user', 'notification_type', 'title', 'message', 'priority', 
                  'send_email', 'send_sms', 'send_push']
        widgets = {
            'user': forms.Select(attrs={'class': 'form-select'}),
            'notification_type': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Notification title'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Message content'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'send_email': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'send_sms': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'send_push': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class NotificationTemplateForm(forms.ModelForm):
    """Form for notification templates"""
    class Meta:
        model = NotificationTemplate
        fields = ['name', 'template_type', 'subject', 'content', 'variables', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'template_type': forms.Select(attrs={'class': 'form-select'}),
            'subject': forms.TextInput(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 8}),
            'variables': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'user_name, order_id, etc.'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class BulkNotificationForm(forms.ModelForm):
    """Form for bulk notifications"""
    class Meta:
        model = BulkNotification
        fields = ['title', 'message', 'notification_type', 'target_all_users', 
                  'target_specific_users', 'send_as_email', 'send_as_sms', 'scheduled_at']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'notification_type': forms.Select(attrs={'class': 'form-select'}),
            'target_all_users': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'target_specific_users': forms.SelectMultiple(attrs={'class': 'form-select', 'size': 5}),
            'send_as_email': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'send_as_sms': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'scheduled_at': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }