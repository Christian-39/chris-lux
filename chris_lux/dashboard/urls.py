"""
URL configuration for dashboard app.
"""
from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_home, name='home'),
    path('orders/', views.orders_management, name='orders'),
    path('orders/<int:order_id>/', views.order_detail, name='order_detail'),
    path('products/', views.products_management, name='products'),
    path('customers/', views.customers_management, name='customers'),
    path('analytics/', views.sales_analytics, name='analytics'),
    path('activity-logs/', views.activity_logs, name='activity_logs'),
    path('inventory/', views.inventory_report, name='inventory'),
]
