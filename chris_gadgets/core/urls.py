"""
Core URL Configuration
"""
from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # Home
    path('', views.home_view, name='home'),

    # Static Pages
    path('about/', views.about_view, name='about'),
    path('contact/', views.contact_view, name='contact'),
    path('faq/', views.faq_view, name='faq'),
    path('terms/', views.terms_view, name='terms'),
    path('privacy/', views.privacy_view, name='privacy'),
    path('shipping/', views.shipping_info_view, name='shipping'),
    path('returns/', views.returns_policy_view, name='returns'),
    
    # Search
    path('search/', views.search_view, name='search'),
    
    # Newsletter
    path('newsletter/subscribe/', views.newsletter_subscribe_view, name='newsletter_subscribe'),
    path('newsletter/unsubscribe/<str:email>/', views.newsletter_unsubscribe_view, name='newsletter_unsubscribe'),
    
    # AJAX
    path('ajax/cart-count/', views.get_cart_count, name='cart_count'),
    path('ajax/wishlist-count/', views.get_wishlist_count, name='wishlist_count'),
    path('ajax/notification-count/', views.get_notification_count, name='notification_count'),
]
