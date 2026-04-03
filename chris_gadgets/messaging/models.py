"""
Messaging Models - User to Admin Messaging System
"""
from django.db import models
from django.conf import settings
import uuid


class Conversation(models.Model):
    """Conversation/Chat Thread Model"""
    
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('pending', 'Pending'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    SUBJECT_CHOICES = [
        ('general', 'General Inquiry'),
        ('order', 'Order Related'),
        ('payment', 'Payment Issue'),
        ('product', 'Product Question'),
        ('shipping', 'Shipping/Delivery'),
        ('return', 'Return/Refund'),
        ('technical', 'Technical Support'),
        ('complaint', 'Complaint'),
        ('feedback', 'Feedback'),
        ('other', 'Other'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subject = models.CharField(max_length=100, choices=SUBJECT_CHOICES, default='general')
    custom_subject = models.CharField(max_length=255, blank=True, null=True)
    
    # Participants
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='conversations_as_customer'
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='assigned_conversations'
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='open'
    )
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='medium'
    )
    
    # Related Objects
    related_order = models.ForeignKey(
        'orders.Order',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='conversations'
    )
    related_product = models.ForeignKey(
        'products.Product',
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='conversations'
    )
    
    # Tracking
    is_read_by_customer = models.BooleanField(default=False)
    is_read_by_admin = models.BooleanField(default=False)
    last_message_at = models.DateTimeField(blank=True, null=True)
    customer_last_seen = models.DateTimeField(blank=True, null=True)
    admin_last_seen = models.DateTimeField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        ordering = ['-last_message_at', '-created_at']
    
    def __str__(self):
        subject = self.custom_subject or self.get_subject_display()
        return f"{self.customer.get_full_name()} - {subject}"
    
    @property
    def display_subject(self):
        return self.custom_subject or self.get_subject_display()
    
    @property
    def unread_count_customer(self):
        """Count unread messages for customer"""
        return self.messages.filter(is_from_admin=True, is_read=False).count()
    
    @property
    def unread_count_admin(self):
        """Count unread messages for admin"""
        return self.messages.filter(is_from_admin=False, is_read=False).count()
    
    @property
    def last_message(self):
        """Get last message in conversation"""
        return self.messages.order_by('-created_at').first()


class Message(models.Model):
    """Individual Message Model"""
    
    MESSAGE_TYPE_CHOICES = [
        ('text', 'Text'),
        ('image', 'Image'),
        ('file', 'File'),
        ('system', 'System'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_messages'
    )
    
    # Message Content
    message_type = models.CharField(
        max_length=20,
        choices=MESSAGE_TYPE_CHOICES,
        default='text'
    )
    content = models.TextField()
    attachment = models.FileField(
        upload_to='messages/attachments/%Y/%m/',
        blank=True,
        null=True
    )
    attachment_name = models.CharField(max_length=255, blank=True, null=True)
    
    # Status
    is_from_admin = models.BooleanField(default=False)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(blank=True, null=True)
    
    # Edited
    is_edited = models.BooleanField(default=False)
    edited_at = models.DateTimeField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.sender.get_full_name()}: {self.content[:50]}..."
    
    def mark_as_read(self):
        """Mark message as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = models.DateTimeField().auto_now
            self.save(update_fields=['is_read', 'read_at'])


class ContactMessage(models.Model):
    """Contact Form Messages from Non-Logged In Users"""
    
    STATUS_CHOICES = [
        ('new', 'New'),
        ('read', 'Read'),
        ('replied', 'Replied'),
        ('spam', 'Spam'),
        ('archived', 'Archived'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=17, blank=True, null=True)
    subject = models.CharField(max_length=255)
    message = models.TextField()
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='new'
    )
    
    # Reply
    reply_message = models.TextField(blank=True, null=True)
    replied_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='contact_replies'
    )
    replied_at = models.DateTimeField(blank=True, null=True)
    
    # Metadata
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.subject}"


class SupportFAQ(models.Model):
    """Frequently Asked Questions for Support"""
    
    CATEGORY_CHOICES = [
        ('general', 'General'),
        ('orders', 'Orders'),
        ('payments', 'Payments'),
        ('shipping', 'Shipping'),
        ('returns', 'Returns & Refunds'),
        ('products', 'Products'),
        ('account', 'Account'),
        ('technical', 'Technical'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default='general'
    )
    question = models.CharField(max_length=500)
    answer = models.TextField()
    is_active = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)
    view_count = models.PositiveIntegerField(default=0)
    helpful_count = models.PositiveIntegerField(default=0)
    not_helpful_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Support FAQ'
        verbose_name_plural = 'Support FAQs'
        ordering = ['category', 'display_order', 'question']
    
    def __str__(self):
        return self.question


class WhatsAppChat(models.Model):
    """WhatsApp Chat Integration Model"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='whatsapp_chats',
        blank=True,
        null=True
    )
    phone_number = models.CharField(max_length=17)
    name = models.CharField(max_length=255, blank=True, null=True)
    message = models.TextField()
    is_from_user = models.BooleanField(default=True)
    whatsapp_message_id = models.CharField(max_length=100, blank=True, null=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"WhatsApp - {self.phone_number}"
