"""
Messaging URL Configuration
"""
from django.urls import path
from . import views

app_name = 'messaging'

urlpatterns = [
    # Conversations
    path('', views.conversations_view, name='conversations'),
    path('start/', views.start_conversation_view, name='start_conversation'),
    path('<uuid:conversation_id>/', views.conversation_detail_view, name='conversation_detail'),
    
    # Contact & FAQ
    path('contact/', views.contact_view, name='contact'),
    path('faq/', views.faq_view, name='faq'),
    
    # AJAX
    path('ajax/get-messages/', views.get_messages_ajax, name='get_messages_ajax'),
    path('ajax/send-message/', views.send_message_ajax, name='send_message_ajax'),
]
