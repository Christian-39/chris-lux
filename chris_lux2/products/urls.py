"""
URL configuration for products app.
"""
from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    path('', views.ProductListView.as_view(), name='product_list'),
    path('search/suggestions/', views.search_suggestions, name='search_suggestions'),
    path('featured/', views.featured_products, name='featured'),
    path('new-arrivals/', views.new_arrivals, name='new_arrivals'),
    path('bestsellers/', views.bestsellers, name='bestsellers'),
    path('wishlist/', views.wishlist_view, name='wishlist'),
    path('wishlist/toggle/<slug:slug>/', views.toggle_wishlist, name='toggle_wishlist'),
    path('category/<slug:slug>/', views.CategoryListView.as_view(), name='category_detail'),
    path('<slug:slug>/', views.ProductDetailView.as_view(), name='product_detail'),
    path('<slug:slug>/review/', views.add_review, name='add_review'),
]
