"""
Accounts URL configuration.
"""

from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/change-password/', views.change_password, name='change_password'),
    path('orders/', views.OrderHistoryView.as_view(), name='order_history'),
    path('wishlist/', views.wishlist_view, name='wishlist'),
    path('wishlist/toggle/', views.toggle_wishlist, name='toggle_wishlist'),
]
