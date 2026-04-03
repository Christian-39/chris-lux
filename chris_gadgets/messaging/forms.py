"""
Messaging Forms - Contact and Message Forms
"""
from django import forms
from .models import ContactMessage, Message, Conversation


class ContactForm(forms.ModelForm):
    """Contact Form"""
    
    name = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your Name'
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your Email'
        })
    )
    phone = forms.CharField(
        max_length=17,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your Phone (Optional)'
        })
    )
    subject = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Subject'
        })
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Your Message',
            'rows': 5
        })
    )
    
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'phone', 'subject', 'message']


class MessageForm(forms.ModelForm):
    """Message Form"""
    
    content = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Type your message...',
            'rows': 3
        })
    )
    attachment = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*,.pdf,.doc,.docx'
        })
    )
    
    class Meta:
        model = Message
        fields = ['content', 'attachment']


class ConversationForm(forms.ModelForm):
    """Start Conversation Form"""
    
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
    
    subject = forms.ChoiceField(
        choices=SUBJECT_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    custom_subject = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Specify if Other'
        })
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Describe your issue or question...',
            'rows': 5
        })
    )
    
    class Meta:
        model = Conversation
        fields = ['subject', 'custom_subject']
