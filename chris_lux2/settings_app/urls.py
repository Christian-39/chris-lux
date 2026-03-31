"""
URL configuration for settings app.
"""
from django.urls import path
from . import views

app_name = 'settings'

urlpatterns = [
    path('', views.site_settings_view, name='site_settings'),
    path('bank-details/', views.BankDetailsListView.as_view(), name='bank_details'),
    path('bank-details/add/', views.add_bank_details, name='add_bank_details'),
    path('bank-details/edit/<int:pk>/', views.edit_bank_details, name='edit_bank_details'),
    path('bank-details/delete/<int:pk>/', views.delete_bank_details, name='delete_bank_details'),
    path('email-templates/', views.EmailTemplateListView.as_view(), name='email_templates'),
    path('email-templates/edit/<int:pk>/', views.edit_email_template, name='edit_email_template'),
    path('theme/', views.theme_settings, name='theme_settings'),
]
