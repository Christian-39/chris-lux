"""
Core views for Chris Lux.
"""

from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.generic import TemplateView, ListView
from django.core.mail import send_mail
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from chris_lux.products.models import Category, Product
from .models import Testimonial, FAQ, ContactMessage, NewsletterSubscriber
from .forms import ContactForm, NewsletterForm


class HomeView(TemplateView):
    """Homepage view."""
    template_name = 'core/home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['featured_categories'] = Category.objects.filter(is_featured=True, is_active=True)[:4]
        context['best_sellers'] = Product.objects.filter(is_best_seller=True, is_active=True)[:8]
        context['new_arrivals'] = Product.objects.filter(is_new=True, is_active=True)[:8]
        context['testimonials'] = Testimonial.objects.filter(is_active=True)[:6]
        return context


class AboutView(TemplateView):
    """About page view."""
    template_name = 'core/about.html'


class ContactView(TemplateView):
    """Contact page view."""
    template_name = 'core/contact.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = ContactForm()
        return context
    
    def post(self, request, *args, **kwargs):
        form = ContactForm(request.POST)
        if form.is_valid():
            # Save message
            message = ContactMessage.objects.create(
                name=form.cleaned_data['name'],
                email=form.cleaned_data['email'],
                subject=form.cleaned_data['subject'],
                message=form.cleaned_data['message']
            )
            
            # Send email notification
            try:
                send_mail(
                    subject=f"Contact Form: {message.subject}",
                    message=f"From: {message.name} <{message.email}>\n\n{message.message}",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[settings.CONTACT_EMAIL],
                    fail_silently=True,
                )
            except:
                pass
            
            messages.success(request, "Thank you for your message! We'll get back to you soon.")
            return redirect('contact')
        
        return render(request, self.template_name, {'form': form})


class FAQView(ListView):
    """FAQ page view."""
    model = FAQ
    template_name = 'core/faq.html'
    context_object_name = 'faqs'
    
    def get_queryset(self):
        return FAQ.objects.filter(is_active=True)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Group FAQs by category
        categories = {}
        for faq in context['faqs']:
            if faq.category not in categories:
                categories[faq.category] = []
            categories[faq.category].append(faq)
        context['faq_categories'] = categories
        return context


@require_POST
def newsletter_subscribe(request):
    """Handle newsletter subscription via AJAX."""
    form = NewsletterForm(request.POST)
    if form.is_valid():
        email = form.cleaned_data['email']
        subscriber, created = NewsletterSubscriber.objects.get_or_create(email=email)
        if created:
            return JsonResponse({
                'success': True,
                'message': 'Thank you for subscribing to our newsletter!'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'You are already subscribed to our newsletter.'
            })
    return JsonResponse({
        'success': False,
        'message': 'Please enter a valid email address.'
    })
