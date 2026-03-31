"""
Views for core app.
"""
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.generic import ListView
from django.db.models import Q

from products.models import Product, Category
from .models import Banner, Testimonial, FAQ, ContactMessage, NewsletterSubscriber


def home(request):
    """Home page view."""
    # Featured products
    featured_products = Product.objects.filter(
        is_featured=True,
        is_active=True
    ).prefetch_related('images')[:8]
    
    # New arrivals
    new_arrivals = Product.objects.filter(
        is_new_arrival=True,
        is_active=True
    ).prefetch_related('images')[:8]
    
    # Bestsellers
    bestsellers = Product.objects.filter(
        is_bestseller=True,
        is_active=True
    ).prefetch_related('images')[:8]
    
    # Banners
    banners = Banner.objects.filter(is_active=True).order_by('display_order')
    
    # Categories
    categories = Category.objects.filter(is_active=True)[:6]
    
    # Testimonials
    testimonials = Testimonial.objects.filter(is_active=True).order_by('display_order')[:5]
    
    context = {
        'featured_products': featured_products,
        'new_arrivals': new_arrivals,
        'bestsellers': bestsellers,
        'banners': banners,
        'categories': categories,
        'testimonials': testimonials,
    }
    
    return render(request, 'core/home.html', context)


def about(request):
    """About page view."""
    return render(request, 'core/about.html')


def contact(request):
    """Contact page view."""
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone', '')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        
        if name and email and subject and message:
            ContactMessage.objects.create(
                name=name,
                email=email,
                phone=phone,
                subject=subject,
                message=message
            )
            messages.success(
                request,
                'Thank you for contacting us! We will get back to you soon.'
            )
            return redirect('core:contact')
        else:
            messages.error(request, 'Please fill in all required fields.')
    
    return render(request, 'core/contact.html')


def faq(request):
    """FAQ page view."""
    faqs = FAQ.objects.filter(is_active=True).order_by('display_order')
    return render(request, 'core/faq.html', {'faqs': faqs})


def shipping_info(request):
    """Shipping information page view."""
    return render(request, 'core/shipping_info.html')


def returns_policy(request):
    """Returns policy page view."""
    return render(request, 'core/returns_policy.html')


def privacy_policy(request):
    """Privacy policy page view."""
    return render(request, 'core/privacy_policy.html')


def terms_of_service(request):
    """Terms of service page view."""
    return render(request, 'core/terms_of_service.html')


def size_guide(request):
    """Size guide page view."""
    return render(request, 'core/size_guide.html')


def hair_care(request):
    """Hair care guide page view."""
    return render(request, 'core/hair_care.html')


def subscribe_newsletter(request):
    """Handle newsletter subscription."""
    if request.method == 'POST':
        email = request.POST.get('email')
        
        if email:
            subscriber, created = NewsletterSubscriber.objects.get_or_create(
                email=email,
                defaults={'is_active': True}
            )
            
            if created:
                messages.success(
                    request,
                    'Thank you for subscribing to our newsletter!'
                )
            else:
                if subscriber.is_active:
                    messages.info(
                        request,
                        'You are already subscribed to our newsletter.'
                    )
                else:
                    subscriber.is_active = True
                    subscriber.save()
                    messages.success(
                        request,
                        'Welcome back! Your subscription has been reactivated.'
                    )
        else:
            messages.error(request, 'Please provide a valid email address.')
    
    return redirect('core:home')


def search(request):
    """Search results page."""
    query = request.GET.get('q', '')
    
    if query:
        products = Product.objects.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(short_description__icontains=query) |
            Q(meta_keywords__icontains=query),
            is_active=True
        ).prefetch_related('images')
    else:
        products = Product.objects.none()
    
    return render(request, 'core/search_results.html', {
        'query': query,
        'products': products,
        'count': products.count(),
    })
