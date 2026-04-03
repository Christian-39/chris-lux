"""
Messaging Views - User to Admin Messaging System
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.utils import timezone

from .models import Conversation, Message, ContactMessage, SupportFAQ
from .forms import ContactForm, MessageForm


@login_required
def conversations_view(request):
    """User Conversations View"""
    conversations = Conversation.objects.filter(
        customer=request.user
    ).order_by('-last_message_at')
    
    context = {
        'conversations': conversations,
    }
    
    return render(request, 'messaging/conversations.html', context)


@login_required
def conversation_detail_view(request, conversation_id):
    """Conversation Detail View"""
    conversation = get_object_or_404(
        Conversation,
        id=conversation_id,
        customer=request.user
    )
    
    # Mark messages as read
    conversation.messages.filter(is_from_admin=True, is_read=False).update(is_read=True)
    
    # Update conversation read status
    conversation.is_read_by_customer = True
    conversation.customer_last_seen = timezone.now()
    conversation.save()
    
    if request.method == 'POST':
        form = MessageForm(request.POST, request.FILES)
        if form.is_valid():
            message = form.save(commit=False)
            message.conversation = conversation
            message.sender = request.user
            message.is_from_admin = False
            message.save()
            
            # Update conversation
            conversation.last_message_at = timezone.now()
            conversation.is_read_by_admin = False
            conversation.status = 'open'
            conversation.save()
            
            messages.success(request, 'Message sent.')
            return redirect('messaging:conversation_detail', conversation_id=conversation.id)
    else:
        form = MessageForm()
    
    context = {
        'conversation': conversation,
        'messages': conversation.messages.all(),
        'form': form,
    }
    
    return render(request, 'messaging/conversation_detail.html', context)


@login_required
def start_conversation_view(request):
    """Start New Conversation View"""
    from orders.models import Order
    from products.models import Product
    
    if request.method == 'POST':
        subject = request.POST.get('subject')
        custom_subject = request.POST.get('custom_subject', '')
        message_content = request.POST.get('message')
        order_id = request.POST.get('order_id')
        product_id = request.POST.get('product_id')
        
        if not message_content:
            messages.error(request, 'Please enter a message.')
            return redirect('messaging:start_conversation')
        
        # Create conversation
        conversation = Conversation.objects.create(
            customer=request.user,
            subject=subject,
            custom_subject=custom_subject if subject == 'other' else None,
        )
        
        # Link to order or product if provided
        if order_id:
            try:
                order = Order.objects.get(id=order_id, user=request.user)
                conversation.related_order = order
            except Order.DoesNotExist:
                pass
        
        if product_id:
            try:
                product = Product.objects.get(id=product_id)
                conversation.related_product = product
            except Product.DoesNotExist:
                pass
        
        conversation.save()
        
        # Create first message
        Message.objects.create(
            conversation=conversation,
            sender=request.user,
            content=message_content,
            is_from_admin=False
        )
        
        conversation.last_message_at = timezone.now()
        conversation.save()
        
        messages.success(request, 'Conversation started. We will respond shortly.')
        return redirect('messaging:conversation_detail', conversation_id=conversation.id)
    
    # Get user's orders and products for selection
    user_orders = Order.objects.filter(user=request.user).order_by('-created_at')[:10]
    
    context = {
        'orders': user_orders,
    }
    
    return render(request, 'messaging/start_conversation.html', context)


def contact_view(request):
    """Contact Form View (Public)"""
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            contact_message = form.save(commit=False)
            if request.user.is_authenticated:
                contact_message.name = request.user.get_full_name()
                contact_message.email = request.user.email
            contact_message.ip_address = get_client_ip(request)
            contact_message.user_agent = request.META.get('HTTP_USER_AGENT', '')
            contact_message.save()
            
            messages.success(
                request,
                'Thank you for contacting us! We will get back to you soon.'
            )
            return redirect('core:contact')
    else:
        initial = {}
        if request.user.is_authenticated:
            initial = {
                'name': request.user.get_full_name(),
                'email': request.user.email,
            }
        form = ContactForm(initial=initial)
    
    context = {
        'form': form,
    }
    
    return render(request, 'messaging/contact.html', {'form': form})


def faq_view(request):
    """FAQ View"""
    faqs = SupportFAQ.objects.filter(is_active=True)
    
    # Group by category
    faqs_by_category = {}
    for faq in faqs:
        category = faq.get_category_display()
        if category not in faqs_by_category:
            faqs_by_category[category] = []
        faqs_by_category[category].append(faq)
    
    context = {
        'faqs_by_category': faqs_by_category,
    }
    
    return render(request, 'messaging/faq.html', context)


# AJAX Views
@login_required
@require_POST
def get_messages_ajax(request):
    """Get new messages via AJAX"""
    conversation_id = request.POST.get('conversation_id')
    last_message_id = request.POST.get('last_message_id')
    
    try:
        conversation = Conversation.objects.get(
            id=conversation_id,
            customer=request.user
        )
        
        messages_qs = conversation.messages.all()
        if last_message_id:
            messages_qs = messages_qs.filter(id__gt=last_message_id)
        
        data = []
        for message in messages_qs:
            data.append({
                'id': str(message.id),
                'content': message.content,
                'is_from_admin': message.is_from_admin,
                'created_at': message.created_at.strftime('%b %d, %Y %H:%M'),
                'sender_name': message.sender.get_full_name(),
            })
        
        # Mark messages as read
        conversation.messages.filter(is_from_admin=True, is_read=False).update(is_read=True)
        
        return JsonResponse({
            'success': True,
            'messages': data,
            'unread_count': conversation.unread_count_customer,
        })
    
    except Conversation.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Conversation not found'
        })


@login_required
@require_POST
def send_message_ajax(request):
    """Send message via AJAX"""
    conversation_id = request.POST.get('conversation_id')
    content = request.POST.get('content')
    
    if not content:
        return JsonResponse({
            'success': False,
            'message': 'Message content is required'
        })
    
    try:
        conversation = Conversation.objects.get(
            id=conversation_id,
            customer=request.user
        )
        
        message = Message.objects.create(
            conversation=conversation,
            sender=request.user,
            content=content,
            is_from_admin=False
        )
        
        # Update conversation
        conversation.last_message_at = timezone.now()
        conversation.is_read_by_admin = False
        conversation.status = 'open'
        conversation.save()
        
        return JsonResponse({
            'success': True,
            'message': {
                'id': str(message.id),
                'content': message.content,
                'created_at': message.created_at.strftime('%b %d, %Y %H:%M'),
            }
        })
    
    except Conversation.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Conversation not found'
        })


def get_client_ip(request):
    """Get client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
