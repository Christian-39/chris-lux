"""
URL configuration for payments app.
"""
from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    # Customer URLs
    path('upload/<int:order_id>/', views.upload_receipt, name='upload_receipt'),
    path('receipt/<int:pk>/', views.ReceiptDetailView.as_view(), name='receipt_detail'),
    path('receipts/', views.ReceiptListView.as_view(), name='receipt_list'),
    path('history/<int:order_id>/', views.receipt_history, name='receipt_history'),
    
    # Admin URLs
    path('admin/pending/', views.PendingReceiptsView.as_view(), name='pending_receipts'),
    path('admin/all/', views.AllReceiptsView.as_view(), name='all_receipts'),
    path('admin/approve/<int:receipt_id>/', views.approve_receipt, name='approve_receipt'),
    path('admin/reject/<int:receipt_id>/', views.reject_receipt, name='reject_receipt'),
]
