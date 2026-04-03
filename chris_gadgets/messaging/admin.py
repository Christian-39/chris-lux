"""
Messaging Admin Configuration
"""
from django.contrib import admin
from .models import (
    Conversation, Message, ContactMessage,
    SupportFAQ, WhatsAppChat
)


class MessageInline(admin.TabularInline):
    """Message Inline"""
    model = Message
    extra = 0
    readonly_fields = ['sender', 'content', 'is_from_admin', 'is_read', 'created_at']
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    """Conversation Admin"""
    
    list_display = [
        'display_subject', 'customer', 'assigned_to',
        'status', 'priority', 'unread_count_admin', 'last_message_at'
    ]
    list_filter = ['status', 'priority', 'subject', 'created_at']
    search_fields = [
        'customer__email', 'customer__first_name',
        'custom_subject', 'assigned_to__email'
    ]
    raw_id_fields = ['customer', 'assigned_to', 'related_order', 'related_product']
    inlines = [MessageInline]
    date_hierarchy = 'created_at'
    
    actions = ['assign_to_me', 'mark_as_resolved', 'mark_as_closed']
    
    def assign_to_me(self, request, queryset):
        queryset.update(assigned_to=request.user)
    assign_to_me.short_description = 'Assign selected conversations to me'
    
    def mark_as_resolved(self, request, queryset):
        from django.utils import timezone
        queryset.update(status='resolved', resolved_at=timezone.now())
    mark_as_resolved.short_description = 'Mark selected as resolved'
    
    def mark_as_closed(self, request, queryset):
        queryset.update(status='closed')
    mark_as_closed.short_description = 'Mark selected as closed'


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    """Message Admin"""
    
    list_display = [
        'conversation', 'sender', 'message_type',
        'is_from_admin', 'is_read', 'created_at'
    ]
    list_filter = ['message_type', 'is_from_admin', 'is_read', 'created_at']
    search_fields = ['content', 'sender__email']
    raw_id_fields = ['conversation', 'sender']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at']


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    """Contact Message Admin"""
    
    list_display = [
        'name', 'email', 'subject', 'status', 'created_at'
    ]
    list_filter = ['status', 'created_at']
    search_fields = ['name', 'email', 'subject', 'message']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Sender Information', {
            'fields': ('name', 'email', 'phone')
        }),
        ('Message', {
            'fields': ('subject', 'message')
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Reply', {
            'fields': ('reply_message', 'replied_by', 'replied_at')
        }),
        ('Metadata', {
            'fields': ('ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'replied_at', 'ip_address', 'user_agent']
    actions = ['mark_as_replied', 'mark_as_spam']
    
    def mark_as_replied(self, request, queryset):
        from django.utils import timezone
        queryset.update(
            status='replied',
            replied_by=request.user,
            replied_at=timezone.now()
        )
    mark_as_replied.short_description = 'Mark selected as replied'
    
    def mark_as_spam(self, request, queryset):
        queryset.update(status='spam')
    mark_as_spam.short_description = 'Mark selected as spam'


@admin.register(SupportFAQ)
class SupportFAQAdmin(admin.ModelAdmin):
    """Support FAQ Admin"""
    
    list_display = [
        'question', 'category', 'is_active',
        'display_order', 'view_count', 'helpful_count'
    ]
    list_filter = ['category', 'is_active']
    search_fields = ['question', 'answer']
    list_editable = ['display_order', 'is_active']


@admin.register(WhatsAppChat)
class WhatsAppChatAdmin(admin.ModelAdmin):
    """WhatsApp Chat Admin"""
    
    list_display = [
        'phone_number', 'name', 'is_from_user',
        'is_read', 'created_at'
    ]
    list_filter = ['is_from_user', 'is_read', 'created_at']
    search_fields = ['phone_number', 'name', 'message']
    raw_id_fields = ['user']
    date_hierarchy = 'created_at'
