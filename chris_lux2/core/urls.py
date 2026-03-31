"""
URL configuration for core app.
"""
from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('faq/', views.faq, name='faq'),
    path('shipping/', views.shipping_info, name='shipping_info'),
    path('returns/', views.returns_policy, name='returns_policy'),
    path('privacy/', views.privacy_policy, name='privacy_policy'),
    path('terms/', views.terms_of_service, name='terms_of_service'),
    path('size-guide/', views.size_guide, name='size_guide'),
    path('hair-care/', views.hair_care, name='hair_care'),
    path('newsletter/subscribe/', views.subscribe_newsletter, name='subscribe_newsletter'),
    path('search/', views.search, name='search'),
]
