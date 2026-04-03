"""
Payments URL Configuration
"""
from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    # Payment
    path('<uuid:order_id>/', views.payment_view, name='payment'),
    path('upload-receipt/<uuid:payment_id>/', views.upload_receipt_view, name='upload_receipt'),
    path('status/<uuid:payment_id>/', views.payment_status_view, name='payment_status'),
    path('download-qr/<uuid:payment_id>/', views.download_qr_code_view, name='download_qr'),
    path('resend/<uuid:payment_id>/', views.resend_verification_view, name='resend_verification'),
    
    # AJAX
    path('ajax/check-status/', views.check_payment_status_ajax, name='check_status_ajax'),
    path('ajax/instructions/', views.get_payment_instructions, name='instructions'),
]
