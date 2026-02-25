"""
Orders URL configuration.
"""

from django.urls import path
from . import views

urlpatterns = [
    path('checkout/', views.CheckoutView.as_view(), name='checkout'),
    path('payment/verify/', views.verify_payment, name='verify_payment'),
    path('success/<slug:order_number>/', views.OrderSuccessView.as_view(), name='order_success'),
    path('detail/<slug:order_number>/', views.OrderDetailView.as_view(), name='order_detail'),
]
