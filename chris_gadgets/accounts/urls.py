"""
Accounts URL Configuration
"""
from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # Authentication
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Email Verification
    path('verify-email/<uidb64>/<token>/', views.verify_email_view, name='verify_email'),
    
    # Password Reset
    path('password-reset/', views.password_reset_view, name='password_reset'),
    path('password-reset-confirm/<uidb64>/<token>/', views.password_reset_confirm_view, name='password_reset_confirm'),
    
    # Profile
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.edit_profile_view, name='edit_profile'),
    path('profile/settings/', views.settings_view, name='settings'),
    path('profile/change-password/', views.change_password_view, name='change_password'),
    path('profile/delete-account/', views.delete_account_view, name='delete_account'),
    
    # Addresses
    path('addresses/', views.addresses_view, name='addresses'),
    path('addresses/add/', views.add_address_view, name='add_address'),
    path('addresses/edit/<uuid:address_id>/', views.edit_address_view, name='edit_address'),
    path('addresses/delete/<uuid:address_id>/', views.delete_address_view, name='delete_address'),
    path('addresses/set-default/<uuid:address_id>/', views.set_default_address_view, name='set_default_address'),
    
    # Orders & Wishlist
    path('orders/', views.order_history_view, name='order_history'),
    path('wishlist/', views.wishlist_view, name='wishlist'),
    path('wishlist/remove/<uuid:product_id>/', views.remove_from_wishlist_view, name='remove_from_wishlist'),
    
    # AJAX
    path('ajax/update-theme/', views.update_theme_preference, name='update_theme'),
]
