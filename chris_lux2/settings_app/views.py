"""
Views for settings app.
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.views.generic import ListView, UpdateView
from django.contrib.auth.mixins import UserPassesTestMixin
from django.urls import reverse_lazy

from .models import SiteSettings, BankDetails, OrderStatus, EmailTemplate


def is_staff(user):
    """Check if user is staff."""
    return user.is_staff


@login_required
@user_passes_test(is_staff)
def site_settings_view(request):
    """Manage site settings."""
    settings = SiteSettings.get_settings()
    
    if request.method == 'POST':
        # Basic Info
        settings.site_name = request.POST.get('site_name', 'Chris-Lux')
        settings.site_tagline = request.POST.get('site_tagline', '')
        settings.site_description = request.POST.get('site_description', '')
        settings.site_keywords = request.POST.get('site_keywords', '')
        
        # Contact
        settings.contact_email = request.POST.get('contact_email', '')
        settings.support_phone = request.POST.get('support_phone', '')
        settings.whatsapp_number = request.POST.get('whatsapp_number', '')
        
        # Address
        settings.business_address = request.POST.get('business_address', '')
        settings.business_city = request.POST.get('business_city', '')
        settings.business_country = request.POST.get('business_country', '')
        
        # Social Media
        settings.facebook_url = request.POST.get('facebook_url', '')
        settings.instagram_url = request.POST.get('instagram_url', '')
        settings.twitter_url = request.POST.get('twitter_url', '')
        settings.youtube_url = request.POST.get('youtube_url', '')
        settings.tiktok_url = request.POST.get('tiktok_url', '')
        settings.pinterest_url = request.POST.get('pinterest_url', '')
        
        # Currency
        settings.currency = request.POST.get('currency', 'USD')
        settings.currency_symbol = request.POST.get('currency_symbol', '$')
        
        # Tax
        settings.tax_rate = request.POST.get('tax_rate', 0)
        
        # Shipping
        settings.free_shipping_threshold = request.POST.get('free_shipping_threshold', 0)
        settings.standard_shipping_cost = request.POST.get('standard_shipping_cost', 15)
        settings.express_shipping_cost = request.POST.get('express_shipping_cost', 25)
        settings.overnight_shipping_cost = request.POST.get('overnight_shipping_cost', 50)
        
        # Order Settings
        settings.order_prefix = request.POST.get('order_prefix', 'CL')
        settings.auto_cancel_hours = request.POST.get('auto_cancel_hours', 48)
        
        # Notification Settings
        settings.admin_notification_email = request.POST.get('admin_notification_email', '')
        settings.notify_on_new_order = request.POST.get('notify_on_new_order') == 'on'
        settings.notify_on_payment = request.POST.get('notify_on_payment') == 'on'
        settings.notify_on_low_stock = request.POST.get('notify_on_low_stock') == 'on'
        settings.low_stock_threshold = request.POST.get('low_stock_threshold', 5)
        
        # Theme Settings
        settings.primary_color = request.POST.get('primary_color', '#6B21A8')
        settings.secondary_color = request.POST.get('secondary_color', '#1F2937')
        settings.accent_color = request.POST.get('accent_color', '#F59E0B')
        
        # Maintenance
        settings.maintenance_mode = request.POST.get('maintenance_mode') == 'on'
        settings.maintenance_message = request.POST.get('maintenance_message', '')
        
        # Analytics
        settings.google_analytics_id = request.POST.get('google_analytics_id', '')
        settings.facebook_pixel_id = request.POST.get('facebook_pixel_id', '')
        
        # Handle file uploads
        if request.FILES.get('logo'):
            settings.logo = request.FILES['logo']
        if request.FILES.get('favicon'):
            settings.favicon = request.FILES['favicon']
        
        settings.save()
        messages.success(request, 'Site settings updated successfully!')
        return redirect('settings:site_settings')
    
    return render(request, 'settings/site_settings.html', {
        'settings': settings
    })


class BankDetailsListView(UserPassesTestMixin, ListView):
    """List bank details."""
    
    model = BankDetails
    template_name = 'settings/bank_details_list.html'
    context_object_name = 'bank_details'
    
    def test_func(self):
        return self.request.user.is_staff


@login_required
@user_passes_test(is_staff)
def add_bank_details(request):
    """Add bank details."""
    if request.method == 'POST':
        bank_name = request.POST.get('bank_name')
        account_name = request.POST.get('account_name')
        account_number = request.POST.get('account_number')
        routing_number = request.POST.get('routing_number', '')
        swift_code = request.POST.get('swift_code', '')
        bank_address = request.POST.get('bank_address', '')
        is_default = request.POST.get('is_default') == 'on'
        
        BankDetails.objects.create(
            bank_name=bank_name,
            account_name=account_name,
            account_number=account_number,
            routing_number=routing_number,
            swift_code=swift_code,
            bank_address=bank_address,
            is_default=is_default,
        )
        
        messages.success(request, 'Bank details added successfully!')
        return redirect('settings:bank_details')
    
    return render(request, 'settings/add_bank_details.html')


@login_required
@user_passes_test(is_staff)
def edit_bank_details(request, pk):
    """Edit bank details."""
    bank = BankDetails.objects.get(pk=pk)
    
    if request.method == 'POST':
        bank.bank_name = request.POST.get('bank_name')
        bank.account_name = request.POST.get('account_name')
        bank.account_number = request.POST.get('account_number')
        bank.routing_number = request.POST.get('routing_number', '')
        bank.swift_code = request.POST.get('swift_code', '')
        bank.bank_address = request.POST.get('bank_address', '')
        bank.is_active = request.POST.get('is_active') == 'on'
        bank.is_default = request.POST.get('is_default') == 'on'
        bank.save()
        
        messages.success(request, 'Bank details updated successfully!')
        return redirect('settings:bank_details')
    
    return render(request, 'settings/edit_bank_details.html', {
        'bank': bank
    })


@login_required
@user_passes_test(is_staff)
def delete_bank_details(request, pk):
    """Delete bank details."""
    bank = BankDetails.objects.get(pk=pk)
    bank.delete()
    messages.success(request, 'Bank details deleted successfully!')
    return redirect('settings:bank_details')


class EmailTemplateListView(UserPassesTestMixin, ListView):
    """List email templates."""
    
    model = EmailTemplate
    template_name = 'settings/email_templates.html'
    context_object_name = 'templates'
    
    def test_func(self):
        return self.request.user.is_staff


@login_required
@user_passes_test(is_staff)
def edit_email_template(request, pk):
    """Edit email template."""
    template = EmailTemplate.objects.get(pk=pk)
    
    if request.method == 'POST':
        template.subject = request.POST.get('subject')
        template.body_html = request.POST.get('body_html')
        template.body_text = request.POST.get('body_text', '')
        template.is_active = request.POST.get('is_active') == 'on'
        template.save()
        
        messages.success(request, 'Email template updated successfully!')
        return redirect('settings:email_templates')
    
    return render(request, 'settings/edit_email_template.html', {
        'template': template
    })


@login_required
@user_passes_test(is_staff)
def theme_settings(request):
    """Manage theme settings."""
    settings = SiteSettings.get_settings()
    
    if request.method == 'POST':
        settings.primary_color = request.POST.get('primary_color', '#6B21A8')
        settings.secondary_color = request.POST.get('secondary_color', '#1F2937')
        settings.accent_color = request.POST.get('accent_color', '#F59E0B')
        settings.save()
        
        messages.success(request, 'Theme settings updated successfully!')
        return redirect('settings:theme_settings')
    
    return render(request, 'settings/theme_settings.html', {
        'settings': settings
    })
