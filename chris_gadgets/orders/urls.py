"""
Orders URL Configuration
"""
from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    # Cart
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/<slug:product_slug>/', views.add_to_cart_view, name='add_to_cart'),
    path('cart/update/<uuid:item_id>/', views.update_cart_item_view, name='update_cart_item'),
    path('cart/remove/<uuid:item_id>/', views.remove_from_cart_view, name='remove_from_cart'),
    path('cart/clear/', views.clear_cart_view, name='clear_cart'),
    
    # Checkout
    path('checkout/', views.checkout_view, name='checkout'),
    path('checkout/apply-coupon/', views.apply_coupon_view, name='apply_coupon'),
    path('checkout/remove-coupon/', views.remove_coupon_view, name='remove_coupon'),
    
    # Orders
    path('detail/<uuid:order_id>/', views.order_detail_view, name='order_detail'),
    path('cancel/<uuid:order_id>/', views.cancel_order_view, name='cancel_order'),
    path('track/<uuid:order_id>/', views.track_order_view, name='track_order'),
    
    # AJAX
    path('ajax/update-quantity/', views.update_cart_quantity_ajax, name='update_quantity_ajax'),
    path('ajax/remove-item/', views.remove_cart_item_ajax, name='remove_item_ajax'),
]
