"""
Cart URL configuration.
"""

from django.urls import path
from . import views

urlpatterns = [
    path('', views.CartView.as_view(), name='cart'),
    path('add/', views.add_to_cart, name='add_to_cart'),
    path('update/', views.update_cart_item, name='update_cart_item'),
    path('remove/', views.remove_from_cart, name='remove_from_cart'),
    path('coupon/apply/', views.apply_coupon, name='apply_coupon'),
    path('coupon/remove/', views.remove_coupon, name='remove_coupon'),
    path('summary/', views.get_cart_summary, name='cart_summary'),
]
