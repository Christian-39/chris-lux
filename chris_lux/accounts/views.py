"""
Accounts views for Chris Lux.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import View, TemplateView
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .forms import UserRegistrationForm, UserLoginForm, UserProfileForm, CustomPasswordChangeForm
from .models import Wishlist
from chris_lux.products.models import Product
from chris_lux.orders.models import Order


class RegisterView(View):
    """User registration view."""
    template_name = 'accounts/register.html'
    
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('home')
        form = UserRegistrationForm()
        return render(request, self.template_name, {'form': form})
    
    def post(self, request):
        if request.user.is_authenticated:
            return redirect('home')
        
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome to Chris Lux, {user.first_name}!')
            return redirect('home')
        
        return render(request, self.template_name, {'form': form})


class LoginView(View):
    """User login view."""
    template_name = 'accounts/login.html'
    
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('home')
        form = UserLoginForm()
        return render(request, self.template_name, {'form': form})
    
    def post(self, request):
        if request.user.is_authenticated:
            return redirect('home')
        
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Welcome back, {user.first_name}!')
            
            # Redirect to next URL if provided
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('home')
        
        return render(request, self.template_name, {'form': form})


def logout_view(request):
    """User logout view."""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')


class ProfileView(LoginRequiredMixin, View):
    """User profile view."""
    template_name = 'accounts/profile.html'
    
    def get(self, request):
        form = UserProfileForm(instance=request.user)
        password_form = CustomPasswordChangeForm(request.user)
        
        # Get recent orders
        recent_orders = Order.objects.filter(user=request.user)[:5]
        
        context = {
            'form': form,
            'password_form': password_form,
            'recent_orders': recent_orders,
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        password_form = CustomPasswordChangeForm(request.user)
        
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated successfully.')
            return redirect('profile')
        
        context = {
            'form': form,
            'password_form': password_form,
        }
        return render(request, self.template_name, context)


@login_required
def change_password(request):
    """Change password view."""
    if request.method == 'POST':
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password has been changed successfully.')
            return redirect('profile')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CustomPasswordChangeForm(request.user)
    
    return render(request, 'accounts/change_password.html', {'form': form})


class OrderHistoryView(LoginRequiredMixin, TemplateView):
    """Order history view."""
    template_name = 'accounts/order_history.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['orders'] = Order.objects.filter(user=self.request.user).prefetch_related('items')
        return context


@login_required
def wishlist_view(request):
    """Wishlist view."""
    wishlist_items = Wishlist.objects.filter(user=request.user).select_related('product')
    wishlist_count = wishlist_items.count()
    return render(request, 'accounts/wishlist.html', {
        'wishlist_items': wishlist_items,
        'wishlist_count': wishlist_count,
        })


@require_POST
def toggle_wishlist(request):
    """Toggle wishlist item via AJAX."""
    if not request.user.is_authenticated:
        return JsonResponse({
            'success': False,
            'message': 'Please login to add items to your wishlist.',
            'login_required': True
        })
    
    product_id = request.POST.get('product_id')
    if not product_id:
        return JsonResponse({'success': False, 'message': 'Product ID is required.'})
    
    try:
        product = Product.objects.get(id=product_id, is_active=True)
    except Product.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Product not found.'})
    
    wishlist_item, created = Wishlist.objects.get_or_create(
        user=request.user,
        product=product
    )
    
    if not created:
        wishlist_item.delete()
        return JsonResponse({
            'success': True,
            'action': 'removed',
            'message': f'{product.name} removed from your wishlist.'
        })
    
    return JsonResponse({
        'success': True,
        'action': 'added',
        'message': f'{product.name} added to your wishlist.'
    })
