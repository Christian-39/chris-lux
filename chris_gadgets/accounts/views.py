"""
Accounts Views - Authentication and Profile Views
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.core.mail import send_mail
from django.conf import settings
from django.views.decorators.http import require_POST
from django.http import JsonResponse
import uuid

from .models import User, Address, UserActivity, UserSession
from .forms import (
    UserRegistrationForm, UserLoginForm, UserProfileForm,
    UserSettingsForm, AddressForm, CustomPasswordResetForm,
    CustomSetPasswordForm, CustomPasswordChangeForm
)
from .tokens import account_activation_token


def register_view(request):
    """User Registration View"""
    if request.user.is_authenticated:
        return redirect('core:home')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False  # Deactivate until email verification
            user.verification_token = str(uuid.uuid4())
            user.save()
            
            # Send verification email
            send_verification_email(request, user)
            
            messages.success(
                request,
                'Registration successful! Please check your email to verify your account.'
            )
            return redirect('accounts:login')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'accounts/register.html', {'form': form})


def send_verification_email(request, user):
    """Send email verification link"""
    current_site = get_current_site(request)
    subject = 'Verify your email - Gadgets Store'
    message = render_to_string('accounts/emails/verification_email.html', {
        'user': user,
        'domain': current_site.domain,
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': account_activation_token.make_token(user),
    })
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])


def verify_email_view(request, uidb64, token):
    """Email Verification View"""
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    
    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.email_verified = True
        user.is_verified = True
        user.save()
        messages.success(request, 'Your email has been verified! You can now log in.')
        return redirect('accounts:login')
    else:
        messages.error(request, 'The verification link is invalid or has expired.')
        return redirect('accounts:login')


def login_view(request):
    """User Login View"""
    if request.user.is_authenticated:
        return redirect('core:home')
    
    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            remember_me = form.cleaned_data.get('remember_me')
            
            user = authenticate(request, email=email, password=password)
            
            if user is not None:
                if user.is_active:
                    login(request, user)
                    
                    # Set session expiry based on remember me
                    if not remember_me:
                        request.session.set_expiry(0)
                    
                    # Log activity
                    UserActivity.objects.create(
                        user=user,
                        activity_type='login',
                        description='User logged in',
                        ip_address=get_client_ip(request),
                        user_agent=request.META.get('HTTP_USER_AGENT', '')
                    )
                    
                    messages.success(request, f'Welcome back, {user.first_name}!')
                    
                    # Redirect to next page if specified
                    next_url = request.GET.get('next')
                    if next_url:
                        return redirect(next_url)
                    return redirect('core:home')
                else:
                    messages.error(request, 'Your account is not active. Please verify your email.')
            else:
                messages.error(request, 'Invalid email or password.')
    else:
        form = UserLoginForm()
    
    return render(request, 'accounts/login.html', {'form': form})


@login_required
def logout_view(request):
    """User Logout View"""
    # Log activity
    UserActivity.objects.create(
        user=request.user,
        activity_type='logout',
        description='User logged out',
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )
    
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('core:home')


@login_required
def profile_view(request):
    """User Profile View"""
    user = request.user
    
    # Get user statistics
    orders_count = user.orders.filter(status__in=['confirmed', 'shipped', 'delivered']).count()
    wishlist_count = user.wishlist.count()
    addresses_count = user.addresses.filter(is_active=True).count()
    
    context = {
        'user': user,
        'orders_count': orders_count,
        'wishlist_count': wishlist_count,
        'addresses_count': addresses_count,
    }
    
    return render(request, 'accounts/profile.html', context)


@login_required
def edit_profile_view(request):
    """Edit Profile View"""
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            
            # Log activity
            UserActivity.objects.create(
                user=request.user,
                activity_type='profile_update',
                description='Profile updated',
                ip_address=get_client_ip(request)
            )
            
            messages.success(request, 'Your profile has been updated successfully.')
            return redirect('accounts:profile')
    else:
        form = UserProfileForm(instance=request.user)
    
    return render(request, 'accounts/edit_profile.html', {'form': form})


@login_required
def settings_view(request):
    """User Settings View"""
    if request.method == 'POST':
        form = UserSettingsForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your settings have been updated.')
            return redirect('accounts:settings')
    else:
        form = UserSettingsForm(instance=request.user)
    
    return render(request, 'accounts/settings.html', {'form': form})


@login_required
def change_password_view(request):
    """Change Password View"""
    if request.method == 'POST':
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            form.save()
            
            # Log activity
            UserActivity.objects.create(
                user=request.user,
                activity_type='password_change',
                description='Password changed',
                ip_address=get_client_ip(request)
            )
            
            messages.success(request, 'Your password has been changed successfully.')
            return redirect('accounts:profile')
    else:
        form = CustomPasswordChangeForm(request.user)
    
    return render(request, 'accounts/change_password.html', {'form': form})


@login_required
def addresses_view(request):
    """User Addresses View"""
    addresses = request.user.addresses.filter(is_active=True)
    return render(request, 'accounts/addresses.html', {'addresses': addresses})


@login_required
def add_address_view(request):
    """Add Address View"""
    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            address.save()
            messages.success(request, 'Address added successfully.')
            
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('accounts:addresses')
    else:
        form = AddressForm()
    
    return render(request, 'accounts/add_address.html', {'form': form})


@login_required
def edit_address_view(request, address_id):
    """Edit Address View"""
    address = get_object_or_404(Address, id=address_id, user=request.user)
    
    if request.method == 'POST':
        form = AddressForm(request.POST, instance=address)
        if form.is_valid():
            form.save()
            messages.success(request, 'Address updated successfully.')
            return redirect('accounts:addresses')
    else:
        form = AddressForm(instance=address)
    
    return render(request, 'accounts/edit_address.html', {
        'form': form,
        'address': address
    })


@login_required
def delete_address_view(request, address_id):
    """Delete Address View"""
    address = get_object_or_404(Address, id=address_id, user=request.user)
    
    if request.method == 'POST':
        address.is_active = False
        address.save()
        messages.success(request, 'Address deleted successfully.')
        return redirect('accounts:addresses')
    
    return render(request, 'accounts/delete_address.html', {'address': address})


@login_required
def set_default_address_view(request, address_id):
    """Set Default Address View"""
    address = get_object_or_404(Address, id=address_id, user=request.user)
    address.is_default = True
    address.save()
    messages.success(request, 'Default address updated.')
    return redirect('accounts:addresses')


@login_required
def order_history_view(request):
    """Order History View"""
    orders = request.user.orders.all().select_related('payment')
    return render(request, 'accounts/order_history.html', {'orders': orders})


@login_required
def wishlist_view(request):
    """Wishlist View"""
    wishlist_items = request.user.wishlist.select_related('product')
    return render(request, 'accounts/wishlist.html', {'wishlist_items': wishlist_items})


@login_required
def remove_from_wishlist_view(request, product_id):
    """Remove from Wishlist View"""
    from products.models import Wishlist
    wishlist_item = get_object_or_404(Wishlist, user=request.user, product_id=product_id)
    wishlist_item.delete()
    messages.success(request, 'Item removed from wishlist.')
    return redirect('accounts:wishlist')


def password_reset_view(request):
    """Password Reset View"""
    if request.method == 'POST':
        form = CustomPasswordResetForm(request.POST)
        if form.is_valid():
            form.save(
                request=request,
                use_https=request.is_secure(),
                email_template_name='accounts/emails/password_reset_email.html'
            )
            messages.success(
                request,
                'Password reset instructions have been sent to your email.'
            )
            return redirect('accounts:login')
    else:
        form = CustomPasswordResetForm()
    
    return render(request, 'accounts/password_reset.html', {'form': form})


def password_reset_confirm_view(request, uidb64, token):
    """Password Reset Confirm View"""
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    
    if user is not None and account_activation_token.check_token(user, token):
        if request.method == 'POST':
            form = CustomSetPasswordForm(user, request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, 'Your password has been reset successfully.')
                return redirect('accounts:login')
        else:
            form = CustomSetPasswordForm(user)
        
        return render(request, 'accounts/password_reset_confirm.html', {'form': form})
    else:
        messages.error(request, 'The password reset link is invalid or has expired.')
        return redirect('accounts:password_reset')


@login_required
def delete_account_view(request):
    """Delete Account View"""
    if request.method == 'POST':
        user = request.user
        logout(request)
        user.is_active = False
        user.save()
        messages.success(request, 'Your account has been deleted.')
        return redirect('core:home')
    
    return render(request, 'accounts/delete_account.html')


def get_client_ip(request):
    """Get client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


# AJAX Views
@login_required
@require_POST
def update_theme_preference(request):
    """Update theme preference via AJAX"""
    theme = request.POST.get('theme')
    if theme in ['light', 'dark', 'system']:
        request.user.theme_preference = theme
        request.user.save(update_fields=['theme_preference'])
        return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'error': 'Invalid theme'})
