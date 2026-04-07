"""
Admin Dashboard URL Configuration
"""
from django.urls import path
from . import views

app_name = 'admin_dashboard'

urlpatterns = [
    # Dashboard Home
    path('', views.admin_dashboard_view, name='dashboard'),
    
    # Products
    path('products/', views.admin_products_view, name='products'),
    path('products/add/', views.admin_product_create_view, name='product_add'),
    path('products/create/', views.admin_product_create_view, name='product_create'),
    path('products/edit/<uuid:product_id>/', views.admin_product_edit_view, name='product_edit'),
    path('products/<uuid:product_id>/', views.admin_product_detail_view, name='product_detail'),
    path('products/delete/<uuid:product_id>/', views.admin_product_delete_view, name='product_delete'),
    path('products/bulk-action/', views.admin_product_bulk_action_view, name='product_bulk_action'),
    path('products/image/<uuid:image_id>/delete/', views.admin_product_image_delete_view, name='product_image_delete'),
    
    # Orders
    path('orders/', views.admin_orders_view, name='orders'),
    path('orders/<uuid:order_id>/', views.admin_order_detail_view, name='order_detail'),
    path('orders/<uuid:order_id>/status/', views.admin_order_status_update_view, name='order_status_update'),
    path('orders/<uuid:order_id>/note/', views.admin_order_add_note_view, name='order_add_note'),
    path('orders/<uuid:order_id>/invoice/', views.admin_order_invoice_view, name='order_invoice'),
    path('orders/export/', views.admin_order_export_view, name='order_export'),
    
    # Payments
    path('payments/', views.admin_payments_view, name='payments'),
    path('payments/<uuid:payment_id>/', views.admin_payment_detail_view, name='payment_detail'),
    path('payments/<uuid:payment_id>/verify/', views.admin_payment_verify_view, name='payment_verify'),
    path('payments/<uuid:payment_id>/reject/', views.admin_payment_reject_view, name='payment_reject'),
    path('payments/export/', views.admin_payment_export_view, name='payment_export'),
    
    # Customers
    path('customers/', views.admin_customers_view, name='customers'),
    path('customers/<uuid:customer_id>/', views.admin_customer_detail_view, name='customer_detail'),
    path('customers/<uuid:customer_id>/edit/', views.admin_customer_edit_view, name='customer_edit'),
    path('customers/<uuid:customer_id>/deactivate/', views.admin_customer_deactivate_view, name='customer_deactivate'),
    path('customers/<uuid:customer_id>/activate/', views.admin_customer_activate_view, name='customer_activate'),
    path('customers/export/', views.admin_customer_export_view, name='customer_export'),
    
    # Categories
    path('categories/', views.admin_categories_view, name='categories'),
    path('categories/add/', views.admin_category_add_view, name='category_add'),
    path('categories/<uuid:category_id>/edit/', views.admin_category_edit_view, name='category_edit'),
    path('categories/<uuid:category_id>/delete/', views.admin_category_delete_view, name='category_delete'),
    path('categories/<uuid:category_id>/toggle/', views.admin_category_toggle_view, name='category_toggle'),
    
    # Brands
    path('brands/', views.admin_brands_view, name='brands'),
    path('brands/add/', views.admin_brand_add_view, name='brand_add'),
    path('brands/<uuid:brand_id>/edit/', views.admin_brand_edit_view, name='brand_edit'),
    path('brands/<uuid:brand_id>/delete/', views.admin_brand_delete_view, name='brand_delete'),
    
    # Reviews
    path('reviews/', views.admin_reviews_view, name='reviews'),
    path('reviews/<uuid:review_id>/approve/', views.admin_review_approve_view, name='review_approve'),
    path('reviews/<uuid:review_id>/reject/', views.admin_review_reject_view, name='review_reject'),
    path('reviews/<uuid:review_id>/delete/', views.admin_review_delete_view, name='review_delete'),
    
    # Messages & Support
    path('messages/', views.admin_messages_view, name='messages'),
    path('messages/<uuid:conversation_id>/', views.admin_message_detail_view, name='message_detail'),
    path('conversations/', views.admin_conversations_view, name='conversations'),
    path('conversations/<uuid:conversation_id>/', views.admin_conversation_detail_view, name='conversation_detail'),
    path('conversations/<uuid:conversation_id>/close/', views.admin_conversation_close_view, name='conversation_close'),
    
    # Notification Management (Admin)
    path('notifications/', views.admin_notifications_list_view, name='notifications_list'),
    path('notifications/create/', views.admin_notification_create_view, name='notification_create'),
    path('notifications/<uuid:notification_id>/', views.admin_notification_detail_view, name='notification_detail'),
    path('notifications/<uuid:notification_id>/edit/', views.admin_notification_edit_view, name='notification_edit'),
    path('notifications/<uuid:notification_id>/delete/', views.admin_notification_delete_view, name='notification_delete'),
    path('notifications/bulk-action/', views.admin_notification_bulk_action_view, name='notification_bulk_action'),
    
    # Notification Templates (Admin)
    path('notification-templates/', views.admin_notification_templates_view, name='notification_templates'),
    path('notification-templates/create/', views.admin_notification_template_create_view, name='notification_template_create'),
    path('notification-templates/<int:template_id>/edit/', views.admin_notification_template_edit_view, name='notification_template_edit'),
    path('notification-templates/<int:template_id>/delete/', views.admin_notification_template_delete_view, name='notification_template_delete'),
    
    # Bulk Notifications (Admin)
    path('bulk-notifications/', views.admin_bulk_notifications_view, name='bulk_notifications'),
    path('bulk-notifications/create/', views.admin_bulk_notification_create_view, name='bulk_notification_create'),
    path('bulk-notifications/<int:bulk_id>/send/', views.admin_bulk_notification_send_view, name='bulk_notification_send'),
    path('bulk-notifications/<int:bulk_id>/delete/', views.admin_bulk_notification_delete_view, name='bulk_notification_delete'),
    
    # Settings
    path('settings/', views.admin_settings_view, name='settings'),
    path('settings/save/', views.admin_settings_save_view, name='settings_save'),
    
    # Reports
    path('reports/', views.admin_reports_view, name='reports'),
    path('reports/sales/', views.admin_sales_report_view, name='sales_report'),
    path('reports/products/', views.admin_products_report_view, name='products_report'),
    path('reports/customers/', views.admin_customers_report_view, name='customers_report'),
]