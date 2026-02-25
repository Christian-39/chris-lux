"""
Products URL configuration.
"""

from django.urls import path
from . import views

urlpatterns = [
    path('', views.ShopView.as_view(), name='shop'),
    path('category/<slug:slug>/', views.CategoryDetailView.as_view(), name='category_detail'),
    path('<slug:slug>/', views.ProductDetailView.as_view(), name='product_detail'),
    path('ajax/variation-price/', views.get_variation_price, name='variation_price'),
]
