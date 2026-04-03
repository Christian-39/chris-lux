"""
Notifications URL Configuration
"""
from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    # Notifications
    path('', views.notifications_view, name='notifications'),
    path('mark-read/<uuid:notification_id>/', views.mark_as_read_view, name='mark_as_read'),
    path('mark-all-read/', views.mark_all_as_read_view, name='mark_all_as_read'),
    path('delete/<uuid:notification_id>/', views.delete_notification_view, name='delete_notification'),
    path('preferences/', views.notification_preferences_view, name='preferences'),
    
    # AJAX
    path('ajax/get/', views.get_notifications_ajax, name='get_ajax'),
    path('ajax/mark-read/', views.mark_notification_read_ajax, name='mark_read_ajax'),
]
