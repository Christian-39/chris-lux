"""
Products URL Configuration
"""
from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    # Product List
    path('', views.product_list_view, name='product_list'),
    
    # Product Detail
    path('<slug:slug>/', views.product_detail_view, name='product_detail'),
    
    # Categories
    path('category/<slug:slug>/', views.category_view, name='category'),
    
    # Brands
    path('brand/<slug:slug>/', views.brand_view, name='brand'),
    
    # Deals
    path('deals/hot/', views.hot_deals_view, name='hot_deals'),
    path('deals/new-arrivals/', views.new_arrivals_view, name='new_arrivals'),
    path('deals/flash-sales/', views.flash_sales_view, name='flash_sales'),
    
    # Reviews
    path('<slug:product_slug>/review/', views.add_review_view, name='add_review'),
    
    # Wishlist
    path('<slug:product_slug>/add-to-wishlist/', views.add_to_wishlist_view, name='add_to_wishlist'),
    path('<slug:product_slug>/remove-from-wishlist/', views.remove_from_wishlist_view, name='remove_from_wishlist'),
    
    # Recently Viewed
    path('recently-viewed/', views.recently_viewed_view, name='recently_viewed'),
    
    # AJAX
    path('ajax/check-availability/', views.check_availability, name='check_availability'),
    path('ajax/get-price/', views.get_product_price, name='get_product_price'),
]
