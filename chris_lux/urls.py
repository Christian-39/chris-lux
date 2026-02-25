"""
URL configuration for Chris Lux project.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from django.contrib.sitemaps.views import sitemap
from chris_lux.core.sitemaps import StaticViewSitemap, ProductSitemap

sitemaps = {
    'static': StaticViewSitemap,
    'products': ProductSitemap,
}

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('chris_lux.core.urls')),
    path('products/', include('chris_lux.products.urls')),
    path('cart/', include('chris_lux.cart.urls')),
    path('orders/', include('chris_lux.orders.urls')),
    path('accounts/', include('chris_lux.accounts.urls')),
    path('reviews/', include('chris_lux.reviews.urls')),
    
    # SEO
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('robots.txt', TemplateView.as_view(template_name='robots.txt', content_type='text/plain')),
    
    # Error pages
    path('404/', TemplateView.as_view(template_name='404.html')),
    path('500/', TemplateView.as_view(template_name='500.html')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
