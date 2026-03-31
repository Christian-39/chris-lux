"""
URL configuration for orders app.
"""
from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/<slug:slug>/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/<int:item_id>/', views.update_cart_item, name='update_cart_item'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/clear/', views.clear_cart, name='clear_cart'),
    path('checkout/', views.checkout_view, name='checkout'),
    path('checkout/apply-coupon/', views.apply_coupon, name='apply_coupon'),
    path('checkout/remove-coupon/', views.remove_coupon, name='remove_coupon'),
    path('place-order/', views.place_order, name='place_order'),
    path('confirmation/<int:order_id>/', views.order_confirmation, name='order_confirmation'),
    path('my-orders/', views.OrderListView.as_view(), name='order_list'),
    path('order/<int:pk>/', views.OrderDetailView.as_view(), name='order_detail'),
    path('order/<int:order_id>/cancel/', views.cancel_order, name='cancel_order'),
]
