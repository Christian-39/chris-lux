"""
URL configuration for users app.
"""
from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/edit/', views.profile_edit_view, name='profile_edit'),
    path('profile/address/', views.address_edit_view, name='address_edit'),
    path('profile/preferences/', views.preferences_view, name='preferences'),
    path('orders/', views.order_history_view, name='order_history'),
]
