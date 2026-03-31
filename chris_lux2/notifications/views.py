"""
Views for notifications app.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.utils import timezone

from .models import Notification, NotificationPreference


class NotificationListView(LoginRequiredMixin, ListView):
    """Display user's notifications."""
    
    model = Notification
    template_name = 'notifications/notification_list.html'
    context_object_name = 'notifications'
    paginate_by = 20
    
    def get_queryset(self):
        return Notification.objects.filter(
            user=self.request.user
        ).select_related('order').order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['unread_count'] = Notification.objects.filter(
            user=self.request.user,
            is_read=False
        ).count()
        return context


@login_required
def mark_as_read(request, notification_id):
    """Mark a notification as read."""
    notification = get_object_or_404(
        Notification,
        id=notification_id,
        user=request.user
    )
    notification.mark_as_read()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    
    return redirect('notifications:notification_list')


@login_required
def mark_all_as_read(request):
    """Mark all notifications as read."""
    Notification.objects.filter(
        user=request.user,
        is_read=False
    ).update(is_read=True, read_at=timezone.now())
    
    messages.success(request, 'All notifications marked as read.')
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    
    return redirect('notifications:notification_list')


@login_required
def delete_notification(request, notification_id):
    """Delete a notification."""
    notification = get_object_or_404(
        Notification,
        id=notification_id,
        user=request.user
    )
    notification.delete()
    
    messages.success(request, 'Notification deleted.')
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    
    return redirect('notifications:notification_list')


@login_required
def get_notifications_ajax(request):
    """AJAX endpoint to get recent notifications."""
    if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
        return JsonResponse({'error': 'Invalid request'}, status=400)
    
    notifications = Notification.objects.filter(
        user=request.user
    ).select_related('order')[:10]
    
    data = {
        'notifications': [
            {
                'id': n.id,
                'title': n.title,
                'message': n.message,
                'type': n.notification_type,
                'is_read': n.is_read,
                'created_at': n.created_at.isoformat(),
                'icon_class': n.icon_class,
                'color_class': n.color_class,
                'order_id': n.order.id if n.order else None,
            }
            for n in notifications
        ],
        'unread_count': Notification.objects.filter(
            user=request.user,
            is_read=False
        ).count()
    }
    
    return JsonResponse(data)


@login_required
def notification_preferences(request):
    """Manage notification preferences."""
    preference, created = NotificationPreference.objects.get_or_create(
        user=request.user
    )
    
    if request.method == 'POST':
        # Email preferences
        preference.email_order_updates = request.POST.get('email_order_updates') == 'on'
        preference.email_payment_updates = request.POST.get('email_payment_updates') == 'on'
        preference.email_shipping_updates = request.POST.get('email_shipping_updates') == 'on'
        preference.email_promotions = request.POST.get('email_promotions') == 'on'
        preference.email_newsletter = request.POST.get('email_newsletter') == 'on'
        
        # SMS preferences
        preference.sms_order_updates = request.POST.get('sms_order_updates') == 'on'
        preference.sms_payment_updates = request.POST.get('sms_payment_updates') == 'on'
        preference.sms_shipping_updates = request.POST.get('sms_shipping_updates') == 'on'
        
        # In-app preferences
        preference.app_order_updates = request.POST.get('app_order_updates') == 'on'
        preference.app_payment_updates = request.POST.get('app_payment_updates') == 'on'
        preference.app_shipping_updates = request.POST.get('app_shipping_updates') == 'on'
        preference.app_promotions = request.POST.get('app_promotions') == 'on'
        
        # Frequency
        preference.email_frequency = request.POST.get('email_frequency', 'immediate')
        
        preference.save()
        messages.success(request, 'Notification preferences updated.')
        return redirect('notifications:preferences')
    
    return render(request, 'notifications/preferences.html', {
        'preference': preference
    })
