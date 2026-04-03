"""
Notifications Views - User Notifications
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator

from .models import Notification, NotificationPreference


@login_required
def notifications_view(request):
    """User Notifications View"""
    notifications = request.user.notifications.all()
    
    # Filter by type
    notification_type = request.GET.get('type')
    if notification_type:
        notifications = notifications.filter(notification_type=notification_type)
    
    # Filter by read status
    read_status = request.GET.get('status')
    if read_status == 'unread':
        notifications = notifications.filter(is_read=False)
    elif read_status == 'read':
        notifications = notifications.filter(is_read=True)
    
    # Pagination
    paginator = Paginator(notifications, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'notifications': page_obj,
        'page_obj': page_obj,
        'paginator': paginator,
        'unread_count': request.user.notifications.filter(is_read=False).count(),
    }
    
    return render(request, 'notifications/notifications.html', context)


@login_required
def mark_as_read_view(request, notification_id):
    """Mark Notification as Read"""
    notification = get_object_or_404(
        Notification,
        id=notification_id,
        user=request.user
    )
    notification.mark_as_read()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    
    return redirect('notifications:notifications')


@login_required
def mark_all_as_read_view(request):
    """Mark All Notifications as Read"""
    request.user.notifications.filter(is_read=False).update(is_read=True)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    
    return redirect('notifications:notifications')


@login_required
def delete_notification_view(request, notification_id):
    """Delete Notification"""
    notification = get_object_or_404(
        Notification,
        id=notification_id,
        user=request.user
    )
    notification.delete()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    
    return redirect('notifications:notifications')


@login_required
def notification_preferences_view(request):
    """Notification Preferences View"""
    preferences, created = NotificationPreference.objects.get_or_create(
        user=request.user
    )
    
    if request.method == 'POST':
        # Email preferences
        preferences.email_order_updates = request.POST.get('email_order_updates') == 'on'
        preferences.email_payment_updates = request.POST.get('email_payment_updates') == 'on'
        preferences.email_promotions = request.POST.get('email_promotions') == 'on'
        preferences.email_product_updates = request.POST.get('email_product_updates') == 'on'
        preferences.email_messages = request.POST.get('email_messages') == 'on'
        preferences.email_reviews = request.POST.get('email_reviews') == 'on'
        preferences.email_wishlist = request.POST.get('email_wishlist') == 'on'
        preferences.email_cart_reminders = request.POST.get('email_cart_reminders') == 'on'
        
        # SMS preferences
        preferences.sms_order_updates = request.POST.get('sms_order_updates') == 'on'
        preferences.sms_payment_updates = request.POST.get('sms_payment_updates') == 'on'
        preferences.sms_promotions = request.POST.get('sms_promotions') == 'on'
        preferences.sms_delivery_updates = request.POST.get('sms_delivery_updates') == 'on'
        
        # Push preferences
        preferences.push_order_updates = request.POST.get('push_order_updates') == 'on'
        preferences.push_payment_updates = request.POST.get('push_payment_updates') == 'on'
        preferences.push_promotions = request.POST.get('push_promotions') == 'on'
        preferences.push_messages = request.POST.get('push_messages') == 'on'
        preferences.push_reviews = request.POST.get('push_reviews') == 'on'
        preferences.push_wishlist = request.POST.get('push_wishlist') == 'on'
        preferences.push_cart_reminders = request.POST.get('push_cart_reminders') == 'on'
        
        # Quiet hours
        preferences.quiet_hours_enabled = request.POST.get('quiet_hours_enabled') == 'on'
        quiet_hours_start = request.POST.get('quiet_hours_start')
        quiet_hours_end = request.POST.get('quiet_hours_end')
        
        if quiet_hours_start:
            from datetime import datetime
            preferences.quiet_hours_start = datetime.strptime(quiet_hours_start, '%H:%M').time()
        if quiet_hours_end:
            from datetime import datetime
            preferences.quiet_hours_end = datetime.strptime(quiet_hours_end, '%H:%M').time()
        
        preferences.save()
        
        from django.contrib import messages
        messages.success(request, 'Notification preferences updated.')
        return redirect('notifications:preferences')
    
    context = {
        'preferences': preferences,
    }
    
    return render(request, 'notifications/preferences.html', context)


# AJAX Views
@login_required
@require_POST
def get_notifications_ajax(request):
    """Get notifications via AJAX"""
    limit = int(request.POST.get('limit', 5))
    
    notifications = request.user.notifications.all()[:limit]
    
    data = []
    for notification in notifications:
        data.append({
            'id': str(notification.id),
            'title': notification.title,
            'message': notification.message[:100] + '...' if len(notification.message) > 100 else notification.message,
            'type': notification.notification_type,
            'icon': notification.icon_class,
            'is_read': notification.is_read,
            'created_at': notification.created_at.strftime('%b %d, %Y %H:%M'),
            'link': notification.link or '#',
        })
    
    return JsonResponse({
        'success': True,
        'notifications': data,
        'unread_count': request.user.notifications.filter(is_read=False).count(),
    })


@login_required
@require_POST
def mark_notification_read_ajax(request):
    """Mark notification as read via AJAX"""
    notification_id = request.POST.get('notification_id')
    
    try:
        notification = Notification.objects.get(id=notification_id, user=request.user)
        notification.mark_as_read()
        
        return JsonResponse({
            'success': True,
            'unread_count': request.user.notifications.filter(is_read=False).count(),
        })
    except Notification.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Notification not found'
        })
