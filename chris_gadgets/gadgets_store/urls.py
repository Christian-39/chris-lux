"""
Gadgets Store URL Configuration
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),

    # Custom Admin Dashboard
    path('dashboard/', include('core.admin_urls')),
    
    # Core
    path('', include('core.urls')),
    
    # Accounts
    path('accounts/', include('accounts.urls')),
    
    # Products
    path('products/', include('products.urls')),
    
    # Orders
    path('orders/', include('orders.urls')),
    
    # Payments
    path('payments/', include('payments.urls')),
    
    # Notifications
    path('notifications/', include('notifications.urls')),
    
    # Messaging
    path('messages/', include('messaging.urls')),
    
    # Error Pages
    path('404/', TemplateView.as_view(template_name='404.html'), name='404'),
    path('500/', TemplateView.as_view(template_name='500.html'), name='500'),
]

# Serve static and media files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Custom error handlers
handler404 = 'core.views.custom_404'
handler500 = 'core.views.custom_500'
