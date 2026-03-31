"""
Views for user authentication and profile management.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import DetailView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy

from .models import User
from .forms import (
    UserRegistrationForm,
    UserLoginForm,
    UserProfileForm,
    UserAddressForm,
    UserPreferencesForm
)


def register_view(request):
    """Handle user registration."""
    if request.user.is_authenticated:
        return redirect('core:home')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome to Chris-Lux, {user.first_name}!')
            return redirect('core:home')
        else:
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = UserRegistrationForm()
    
    return render(request, 'users/register.html', {'form': form})


def login_view(request):
    """Handle user login."""
    if request.user.is_authenticated:
        return redirect('core:home')
    
    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {user.first_name}!')
                next_url = request.GET.get('next', 'core:home')
                return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = UserLoginForm()
    
    return render(request, 'users/login.html', {'form': form})


@login_required
def logout_view(request):
    """Handle user logout."""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('core:home')


class ProfileView(LoginRequiredMixin, DetailView):
    """Display user profile."""
    model = User
    template_name = 'users/profile.html'
    context_object_name = 'profile_user'
    
    def get_object(self):
        return self.request.user
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['orders'] = self.request.user.orders.all()[:5]
        return context


@login_required
def profile_edit_view(request):
    """Handle profile editing."""
    user = request.user
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('users:profile')
        else:
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = UserProfileForm(instance=user)
    
    return render(request, 'users/profile_edit.html', {'form': form})


@login_required
def address_edit_view(request):
    """Handle address editing."""
    user = request.user
    
    if request.method == 'POST':
        form = UserAddressForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Address updated successfully!')
            return redirect('users:profile')
        else:
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = UserAddressForm(instance=user)
    
    return render(request, 'users/address_edit.html', {'form': form})


@login_required
def preferences_view(request):
    """Handle user preferences."""
    user = request.user
    
    if request.method == 'POST':
        form = UserPreferencesForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Preferences updated successfully!')
            return redirect('users:profile')
        else:
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = UserPreferencesForm(instance=user)
    
    return render(request, 'users/preferences.html', {'form': form})


@login_required
def order_history_view(request):
    """Display user's order history."""
    orders = request.user.orders.all().prefetch_related('items')
    return render(request, 'users/order_history.html', {'orders': orders})
