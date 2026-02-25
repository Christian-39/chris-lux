"""
Sitemaps for Chris Lux.
"""

from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from chris_lux.products.models import Product


class StaticViewSitemap(Sitemap):
    """Sitemap for static pages."""
    priority = 0.5
    changefreq = 'weekly'
    
    def items(self):
        return ['home', 'about', 'contact', 'faq', 'shop']
    
    def location(self, item):
        return reverse(item)


class ProductSitemap(Sitemap):
    """Sitemap for products."""
    changefreq = 'daily'
    priority = 0.8
    
    def items(self):
        return Product.objects.filter(is_active=True)
    
    def lastmod(self, obj):
        return obj.updated_at
