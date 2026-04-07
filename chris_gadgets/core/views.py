"""
Core Views - Home, About, Contact, and Other Pages
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.db.models import Count, Avg, Q, Sum
from django.core.paginator import Paginator
from django.utils import timezone

from products.models import Product, Category, Brand, FlashSale, Coupon, ProductReview
from orders.models import Cart, CartItem, Order, OrderItem
from payments.models import Payment, BankAccount
from accounts.models import User
from core.models import Banner
from messaging.models import ContactMessage, Conversation
from notifications.models import Notification, NotificationTemplate, BulkNotification
from notifications.forms import NotificationForm, NotificationTemplateForm, BulkNotificationForm
from .models import SiteSetting, Banner, Testimonial, TrustBadge, PageContent, NewsletterSubscriber, ActivityLog


    
def home_view(request):
    """Home Page View"""
    # Hero Banners
    hero_banners = Banner.objects.filter(
        is_active=True,
        position='hero'
    ).order_by('display_order')

    # Featured Products
    featured_products = Product.objects.filter(
        is_active=True,
        is_featured=True
    ).select_related('category', 'brand').prefetch_related('images')[:8]
    
    # New Arrivals
    new_arrivals = Product.objects.filter(
        is_active=True,
        is_new_arrival=True
    ).select_related('category', 'brand').prefetch_related('images')[:8]
    
    # Hot Deals
    hot_deals = Product.objects.filter(
        is_active=True,
        is_hot_deal=True
    ).select_related('category', 'brand').prefetch_related('images')[:8]
    
    # Flash Sales
    flash_sales = FlashSale.objects.filter(
        is_active=True,
        starts_at__lte=timezone.now(),
        ends_at__gte=timezone.now()
    ).select_related('product')[:4]
    
    # Categories
    categories = Category.objects.filter(
        is_active=True,
        parent=None
    ).prefetch_related('subcategories')[:8]
    
    # Featured Brands
    brands = Brand.objects.filter(is_active=True, is_featured=True)[:6]
    
    # Testimonials
    testimonials = Testimonial.objects.filter(
        is_active=True,
        is_featured=True
    )[:6]
    
    # Trust Badges
    trust_badges = TrustBadge.objects.filter(is_active=True)[:4]
    
    context = {
        'featured_products': featured_products,
        'new_arrivals': new_arrivals,
        'hot_deals': hot_deals,
        'flash_sales': flash_sales,
        'categories': categories,
        'brands': brands,
        'hero_banners': hero_banners,
        'testimonials': testimonials,
        'trust_badges': trust_badges,
    }
    
    return render(request, 'core/home.html', context)


def about_view(request):
    """About Page View"""
    page_content = PageContent.objects.filter(page='about').first()
    testimonials = Testimonial.objects.filter(is_active=True)[:6]
    
    context = {
        'page_content': page_content,
        'testimonials': testimonials,
    }
    
    return render(request, 'core/about.html', context)


def contact_view(request):
    """Contact Page View"""
    from messaging.models import ContactMessage
    from messaging.forms import ContactForm
    
    site_settings = SiteSetting.get_settings()
    
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
        'site_settings': site_settings,
    }
    
    return render(request, 'core/contact.html', context)


def faq_view(request):
    """FAQ Page View"""
    from messaging.models import SupportFAQ
    
    faqs = SupportFAQ.objects.filter(is_active=True)
    
    context = {
        'faqs': faqs,
    }
    
    return render(request, 'core/faq.html', context)


def terms_view(request):
    """Terms & Conditions Page View"""
    page_content = PageContent.objects.filter(page='terms').first()
    return render(request, 'core/terms.html', {'page_content': page_content})


def privacy_view(request):
    """Privacy Policy Page View"""
    page_content = PageContent.objects.filter(page='privacy').first()
    return render(request, 'core/privacy.html', {'page_content': page_content})


def shipping_info_view(request):
    """Shipping Information Page View"""
    page_content = PageContent.objects.filter(page='shipping').first()
    site_settings = SiteSetting.get_settings()
    
    context = {
        'page_content': page_content,
        'site_settings': site_settings,
    }
    
    return render(request, 'core/shipping.html', context)


def returns_policy_view(request):
    """Returns Policy Page View"""
    page_content = PageContent.objects.filter(page='returns').first()
    return render(request, 'core/returns.html', {'page_content': page_content})


def search_view(request):
    """Search Products View"""
    query = request.GET.get('q', '')
    category_id = request.GET.get('category', '')
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')
    brand_id = request.GET.get('brand', '')
    sort_by = request.GET.get('sort', 'relevance')
    
    products = Product.objects.filter(is_active=True)
    
    # Apply search query
    if query:
        products = products.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(sku__icontains=query) |
            Q(brand__name__icontains=query)
        )
    
    # Apply filters
    if category_id:
        products = products.filter(category_id=category_id)
    
    if brand_id:
        products = products.filter(brand_id=brand_id)
    
    if min_price:
        products = products.filter(price__gte=min_price)
    
    if max_price:
        products = products.filter(price__lte=max_price)
    
    # Apply sorting
    if sort_by == 'price_low':
        products = products.order_by('price')
    elif sort_by == 'price_high':
        products = products.order_by('-price')
    elif sort_by == 'newest':
        products = products.order_by('-created_at')
    elif sort_by == 'popular':
        products = products.order_by('-sales_count')
    elif sort_by == 'rating':
        products = products.order_by('-average_rating')
    
    # Pagination
    paginator = Paginator(products, 24)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get filter options
    categories = Category.objects.filter(is_active=True)
    brands = Brand.objects.filter(is_active=True)
    
    context = {
        'query': query,
        'products': page_obj,
        'categories': categories,
        'brands': brands,
        'page_obj': page_obj,
        'paginator': paginator,
        'total_results': paginator.count,
    }
    
    return render(request, 'core/search.html', context)


def newsletter_subscribe_view(request):
    """Newsletter Subscribe View"""
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
            elif not subscriber.is_active:
                subscriber.is_active = True
                subscriber.save()
                messages.success(
                    request,
                    'Welcome back! You have been resubscribed.'
                )
            else:
                messages.info(
                    request,
                    'You are already subscribed to our newsletter.'
                )
        else:
            messages.error(request, 'Please enter a valid email address.')
    
    return redirect(request.META.get('HTTP_REFERER', 'core:home'))


def newsletter_unsubscribe_view(request, email):
    """Newsletter Unsubscribe View"""
    from django.utils import timezone
    
    try:
        subscriber = NewsletterSubscriber.objects.get(email=email)
        subscriber.is_active = False
        subscriber.unsubscribed_at = timezone.now()
        subscriber.save()
        messages.success(request, 'You have been unsubscribed from our newsletter.')
    except NewsletterSubscriber.DoesNotExist:
        messages.error(request, 'Email not found in our subscriber list.')
    
    return redirect('core:home')


# Error Views
def custom_404(request, exception=None):
    """Custom 404 Error View"""
    return render(request, '404.html', status=404)


def custom_500(request):
    """Custom 500 Error View"""
    return render(request, '500.html', status=500)


# AJAX Views
def get_cart_count(request):
    """Get cart count via AJAX"""
    count = 0
    
    if request.user.is_authenticated:
        try:
            cart = Cart.objects.get(user=request.user)
            count = cart.item_count
        except Cart.DoesNotExist:
            pass
    else:
        # Handle session-based cart
        cart_data = request.session.get('cart', {})
        count = sum(item['quantity'] for item in cart_data.values())
    
    return JsonResponse({'count': count})


def get_wishlist_count(request):
    """Get wishlist count via AJAX"""
    count = 0
    
    if request.user.is_authenticated:
        count = request.user.wishlist.count()
    
    return JsonResponse({'count': count})


def get_notification_count(request):
    """Get unread notification count via AJAX"""
    count = 0
    
    if request.user.is_authenticated:
        count = request.user.notifications.filter(is_read=False).count()
    
    return JsonResponse({'count': count})


def get_client_ip(request):
    """Get client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


# ============================================
# ADMIN DASHBOARD VIEWS
# ============================================

def is_admin_or_staff(user):
    """Check if user is admin or staff"""
    return user.is_authenticated and (user.user_type in ['admin', 'staff'] or user.is_superuser)

def get_client_ip(request):
    """Get client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
    
@login_required
@user_passes_test(is_admin_or_staff)
def admin_payment_detail_view(request, payment_id):
    print("=" * 50)
    print(f"VIEW CALLED: {request.method} {request.path}")
    print(f"POST data: {request.POST if request.method == 'POST' else 'N/A'}")
    print("=" * 50)
    
    from payments.models import Payment
    

@login_required
@user_passes_test(is_admin_or_staff, login_url='/')
def admin_dashboard_view(request):
    """Admin Dashboard Home View"""
    today = timezone.now().date()
    
    # Statistics
    stats = {
        'total_products': Product.objects.count(),
        'active_products': Product.objects.filter(is_active=True).count(),
        'low_stock_products': Product.objects.filter(stock_status='low_stock').count(),
        'out_of_stock_products': Product.objects.filter(stock_status='out_of_stock').count(),
        
        'total_orders': Order.objects.count(),
        'pending_orders': Order.objects.filter(status='pending').count(),
        'processing_orders': Order.objects.filter(status='processing').count(),
        'shipped_orders': Order.objects.filter(status='shipped').count(),
        'delivered_orders': Order.objects.filter(status='delivered').count(),
        'cancelled_orders': Order.objects.filter(status='cancelled').count(),
        
        'today_orders': Order.objects.filter(created_at__date=today).count(),
        'today_revenue': Order.objects.filter(
            created_at__date=today,
            payment_status='verified'
        ).aggregate(total=Sum('total'))['total'] or 0,
        
        'total_customers': User.objects.filter(user_type='customer').count(),
        'new_customers_today': User.objects.filter(
            user_type='customer',
            date_joined__date=today
        ).count(),
        
        'pending_payments': Payment.objects.filter(status='pending').count(),
        'awaiting_verification': Payment.objects.filter(status='awaiting_verification').count(),
        'verified_payments': Payment.objects.filter(status='verified').count(),
        
        'unread_messages': ContactMessage.objects.filter(status='new').count(),
        'open_conversations': Conversation.objects.filter(status='open').count(),
        'pending_reviews': ProductReview.objects.filter(is_approved=False).count(),
    }
    
    # Recent Orders
    recent_orders = Order.objects.select_related('user').order_by('-created_at')[:10]
    
    # Recent Payments
    recent_payments = Payment.objects.select_related('order', 'user').order_by('-created_at')[:10]
    
    # Low Stock Products
    low_stock_products = Product.objects.filter(
        stock_status__in=['low_stock', 'out_of_stock']
    ).select_related('category')[:10]
    
    # Recent Customers
    recent_customers = User.objects.filter(user_type='customer').order_by('-date_joined')[:10]
    
    # Sales Chart Data (Last 7 days)
    sales_data = []
    labels = []
    for i in range(6, -1, -1):
        date = today - timezone.timedelta(days=i)
        day_orders = Order.objects.filter(
            created_at__date=date,
            payment_status='verified'
        ).aggregate(total=Sum('total'))['total'] or 0
        sales_data.append(float(day_orders))
        labels.append(date.strftime('%a'))
    
    context = {
        'stats': stats,
        'recent_orders': recent_orders,
        'recent_payments': recent_payments,
        'low_stock_products': low_stock_products,
        'recent_customers': recent_customers,
        'sales_labels': labels,
        'sales_data': sales_data,
    }
    
    return render(request, 'admin_dashboard/dashboard.html', context)


@login_required
@user_passes_test(is_admin_or_staff, login_url='/')
def admin_products_view(request):
    """Admin Products List View"""
    products = Product.objects.select_related('category', 'brand').all()
    
    # Filters
    status = request.GET.get('status')
    category_id = request.GET.get('category')
    search = request.GET.get('search')
    
    if status:
        if status == 'active':
            products = products.filter(is_active=True)
        elif status == 'inactive':
            products = products.filter(is_active=False)
        elif status == 'low_stock':
            products = products.filter(stock_status='low_stock')
        elif status == 'out_of_stock':
            products = products.filter(stock_status='out_of_stock')
    
    if category_id:
        products = products.filter(category_id=category_id)
    
    if search:
        products = products.filter(
            Q(name__icontains=search) |
            Q(sku__icontains=search)
        )
    
    # Pagination
    paginator = Paginator(products, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'products': page_obj,
        'categories': Category.objects.all(),
        'total_products': Product.objects.count(),
        'active_products': Product.objects.filter(is_active=True).count(),
        'inactive_products': Product.objects.filter(is_active=False).count(),
    }
    
    return render(request, 'admin_dashboard/products.html', context)


@login_required
@user_passes_test(is_admin_or_staff, login_url='/')
def admin_product_create_view(request):
    """Admin Product Create View"""
    from products.forms import ProductForm
    from products.models import Category, ProductImage
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)  # Don't save yet
            
            # Handle specifications from form data (JSONField)
            spec_names = request.POST.getlist('spec_name[]')
            spec_values = request.POST.getlist('spec_value[]')
            specifications_dict = {}
            for name, value in zip(spec_names, spec_values):
                if name and value:
                    specifications_dict[name] = value
            
            # Set specifications JSON
            product.specifications = specifications_dict
            
            # Save product
            product.save()
            
            # Handle multiple images
            images = request.FILES.getlist('images')
            for i, image in enumerate(images):
                ProductImage.objects.create(
                    product=product,
                    image=image,
                    is_primary=(i == 0),
                    display_order=i
                )
            
            messages.success(request, f'Product "{product.name}" created successfully!')
            return redirect('admin_dashboard:products')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ProductForm()
    
    context = {
        'form': form,
        'categories': Category.objects.all(),
        'title': 'Create Product',
        'action': 'Create',
    }
    
    return render(request, 'admin_dashboard/product_form.html', context)


@login_required
@user_passes_test(is_admin_or_staff, login_url='/')
def admin_product_edit_view(request, product_id):
    """Admin Product Edit View"""
    from products.forms import ProductForm
    from products.models import Category, Product, ProductImage
    
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            product = form.save(commit=False)
            
            # Handle specifications from form data (JSONField)
            spec_names = request.POST.getlist('spec_name[]')
            spec_values = request.POST.getlist('spec_value[]')
            specifications_dict = {}
            for name, value in zip(spec_names, spec_values):
                if name and value:
                    specifications_dict[name] = value
            
            product.specifications = specifications_dict
            product.save()
            
            # Handle new images
            images = request.FILES.getlist('images')
            for i, image in enumerate(images):
                ProductImage.objects.create(
                    product=product,
                    image=image,
                    is_primary=(i == 0) and not product.images.exists(),
                    display_order=product.images.count() + i
                )
            
            messages.success(request, f'Product "{product.name}" updated successfully!')
            return redirect('admin_dashboard:products')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ProductForm(instance=product)
    
    # Convert specifications dict to list for template
    product_specs = []
    if isinstance(product.specifications, dict):
        product_specs = [{'name': k, 'value': v} for k, v in product.specifications.items()]
    
    context = {
        'form': form,
        'product': product,
        'categories': Category.objects.all(),
        'product_specifications': product_specs,  # Pass as list for template
        'title': 'Edit Product',
        'action': 'Update',
    }
    
    return render(request, 'admin_dashboard/product_form.html', context)


@login_required
@user_passes_test(is_admin_or_staff, login_url='/')
def admin_product_detail_view(request, product_id):
    """Admin Product Detail View"""
    from products.models import Product, ProductReview
    from orders.models import OrderItem  # Import from orders, not products
    
    product = get_object_or_404(Product, id=product_id)
    
    # Get product stats
    total_sales = OrderItem.objects.filter(
        product=product,
        order__payment_status='verified'
    ).aggregate(total=Sum('quantity'))['total'] or 0
    
    total_revenue = OrderItem.objects.filter(
        product=product,
        order__payment_status='verified'
    ).aggregate(total=Sum('total_price'))['total'] or 0
    
    recent_reviews = product.reviews.select_related('user').order_by('-created_at')[:10]
    
    context = {
        'product': product,
        'total_sales': total_sales,
        'total_revenue': total_revenue,
        'recent_reviews': recent_reviews, 
        'images': product.images.all(),
    }
    
    return render(request, 'admin_dashboard/product_detail.html', context)

@login_required
@user_passes_test(is_admin_or_staff, login_url='/')
def admin_product_delete_view(request, product_id):
    """Admin Product Delete View"""
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        product_name = product.name
        product.delete()
        messages.success(request, f'Product "{product_name}" deleted successfully!')
        return redirect('admin_dashboard:products')
    
    context = {
        'product': product,
    }
    
    return render(request, 'admin_dashboard/product_delete.html', context)


@login_required
@user_passes_test(is_admin_or_staff, login_url='/')
def admin_orders_view(request):
    """Admin Orders List View"""
    orders_qs = Order.objects.select_related('user').all()
    
    # 1. Apply Filters
    status = request.GET.get('status')
    payment_status = request.GET.get('payment_status')
    search = request.GET.get('search')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    if status:
        orders_qs = orders_qs.filter(status=status)
    if payment_status:
        orders_qs = orders_qs.filter(payment_status=payment_status)
    if search:
        orders_qs = orders_qs.filter(
            Q(order_number__icontains=search) |
            Q(user__email__icontains=search) |
            Q(user__first_name__icontains=search) |
            Q(user__last_name__icontains=search)
        )
    if date_from:
        orders_qs = orders_qs.filter(created_at__date__gte=date_from)
    if date_to:
        orders_qs = orders_qs.filter(created_at__date__lte=date_to)

    # 2. Optimized Stats (One query to rule them all)
    stats = Order.objects.aggregate(
        pending=Count('id', filter=Q(status='pending')),
        processing=Count('id', filter=Q(status='processing')),
        shipped=Count('id', filter=Q(status='shipped')),
        delivered=Count('id', filter=Q(status='delivered')),
        cancelled=Count('id', filter=Q(status='cancelled')),
        refunded=Count('id', filter=Q(status='refunded')),
    )

    # 3. Pagination
    paginator = Paginator(orders_qs.order_by('-created_at'), 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'orders': page_obj,
        # Mapping aggregate results to the template variables
        'pending_count': stats['pending'],
        'processing_count': stats['processing'],
        'shipped_count': stats['shipped'],
        'delivered_count': stats['delivered'],
        'cancelled_count': stats['cancelled'],
        'refunded_count': stats['refunded'],
    }
    
    return render(request, 'admin_dashboard/orders.html', context)

@login_required
@user_passes_test(is_admin_or_staff, login_url='/')
def admin_order_detail_view(request, order_id):
    """Admin Order Detail View"""
    order = get_object_or_404(
        Order.objects.select_related('user', 'coupon'),
        id=order_id
    )
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        admin_note = request.POST.get('admin_note')
        tracking_number = request.POST.get('tracking_number')
        
        if new_status:
            from orders.models import OrderStatusHistory
            old_status = order.status
            order.status = new_status
            
            if new_status == 'shipped':
                order.shipped_at = timezone.now()
                order.tracking_number = tracking_number
            elif new_status == 'delivered':
                order.delivered_at = timezone.now()
            
            order.save()
            
            # Create status history
            OrderStatusHistory.objects.create(
                order=order,
                status=new_status,
                notes=admin_note,
                created_by=request.user
            )
            
            messages.success(request, f'Order status updated to {order.get_status_display()}')
            return redirect('admin_dashboard:order_detail', order_id=order.id)
    
    context = {
        'order': order,
        'items': order.items.all(),
        'status_history': order.status_history.all(),
    }
    
    return render(request, 'admin_dashboard/order_detail.html', context)


@login_required
@user_passes_test(is_admin_or_staff, login_url='/')
def admin_payments_view(request):
    """Admin Payments List View"""
    payments_qs = Payment.objects.select_related('order', 'user').all()
    
    # 1. Filters (Same as before)
    status = request.GET.get('status')
    search = request.GET.get('search')
    if status:
        payments_qs = payments_qs.filter(status=status)
    if search:
        payments_qs = payments_qs.filter(
            Q(payment_reference__icontains=search) |
            Q(order__order_number__icontains=search) |
            Q(user__email__icontains=search)
        )

    # 2. Stats Calculations
    today = timezone.now().date()
    
    # Total Revenue: Sum of amount where status is verified
    total_revenue = Payment.objects.filter(status='verified').aggregate(
        total=Sum('amount'))['total'] or 0
    
    # Pending Verification: Count of payments waiting for admin review
    pending_count = Payment.objects.filter(
        status__in=['pending', 'awaiting_verification']
    ).count()
    
    # Verified Today: Count of payments verified within the current date
    total_verified = Payment.objects.filter(
        status='verified').count()
    
    # Failed Payments: Count of rejected payments
    failed_count = Payment.objects.filter(status='rejected').count()

    # 3. Pagination
    paginator = Paginator(payments_qs.order_by('-created_at'), 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'payments': page_obj,
        'total_revenue': total_revenue,
        'pending_count': pending_count,
        'total_verified': total_verified,
        'failed_count': failed_count,
    }
    
    return render(request, 'admin_dashboard/payments.html', context)

    
@login_required
@user_passes_test(is_admin_or_staff, login_url='/')
def admin_payment_verify_view(request, payment_id):
    """Admin Payment Verify View"""
    payment = get_object_or_404(Payment, id=payment_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        notes = request.POST.get('verification_notes')
        
        if action == 'verify':
            old_status = payment.status
            payment.status = 'verified'
            payment.verified_by = request.user
            payment.verified_at = timezone.now()
            payment.verification_notes = notes
            payment.save()
            
            # Update order
            payment.order.payment_status = 'verified'
            payment.order.status = 'confirmed'
            payment.order.save()
            
            # Log
            from payments.models import PaymentVerificationLog
            PaymentVerificationLog.objects.create(
                payment=payment,
                action='verified',
                performed_by=request.user,
                old_status=old_status,
                new_status='verified',
                notes=notes
            )
            
            messages.success(request, 'Payment verified successfully!')
            
        elif action == 'reject':
            old_status = payment.status
            rejection_reason = request.POST.get('rejection_reason')
            payment.status = 'rejected'
            payment.rejection_reason = rejection_reason
            payment.save()
            
            # Log
            from payments.models import PaymentVerificationLog
            PaymentVerificationLog.objects.create(
                payment=payment,
                action='rejected',
                performed_by=request.user,
                old_status=old_status,
                new_status='rejected',
                notes=rejection_reason
            )
            
            messages.warning(request, 'Payment has been rejected.')
        
        return redirect('admin_dashboard:payments')
    
    context = {
        'payment': payment,
        'order': payment.order,
    }
    
    return render(request, 'admin_dashboard/payment_verify.html', context)


@login_required
@user_passes_test(is_admin_or_staff, login_url='/')
def admin_customers_view(request):
    """Admin Customers List View"""
    customers = User.objects.filter(user_type='customer')
    
    # Filters
    search = request.GET.get('search')
    status = request.GET.get('status')
    
    if search:
        customers = customers.filter(
            Q(email__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(phone_number__icontains=search)
        )
    
    if status == 'active':
        customers = customers.filter(is_active=True)
    elif status == 'inactive':
        customers = customers.filter(is_active=False)
    elif status == 'verified':
        customers = customers.filter(is_verified=True)
    
    # Pagination
    paginator = Paginator(customers.order_by('-date_joined'), 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'customers': page_obj,
        'total_customers': User.objects.filter(user_type='customer').count(),
        'active_customers': User.objects.filter(user_type='customer', is_active=True).count(),
        'verified_customers': User.objects.filter(user_type='customer', is_verified=True).count(),
    }
    
    return render(request, 'admin_dashboard/customers.html', context)


@login_required
@user_passes_test(is_admin_or_staff, login_url='/')
def admin_customer_detail_view(request, customer_id):
    """Admin Customer Detail View"""
    customer = get_object_or_404(User, id=customer_id, user_type='customer')
    
    context = {
        'customer': customer,
        'orders': customer.orders.all()[:10],
        'addresses': customer.addresses.all(),
        'wishlist': customer.wishlist.all()[:10],
        'activities': customer.activities.all()[:10],
    }
    
    return render(request, 'admin_dashboard/customer_detail.html', context)


@login_required
@user_passes_test(is_admin_or_staff, login_url='/')
def admin_categories_view(request):
    """Admin Categories List View"""
    categories = Category.objects.all()
    
    context = {
        'categories': categories,
    }
    
    return render(request, 'admin_dashboard/categories.html', context)


@login_required
@user_passes_test(is_admin_or_staff, login_url='/')
def admin_brands_view(request):
    """Admin Brands List View"""
    brands = Brand.objects.all()
    
    context = {
        'brands': brands,
    }
    
    return render(request, 'admin_dashboard/brands.html', context)


@login_required
@user_passes_test(is_admin_or_staff, login_url='/')
def admin_reviews_view(request):
    """Admin Reviews List View"""
    reviews = ProductReview.objects.select_related('product', 'user').all()
    
    # Filters
    status = request.GET.get('status')
    
    if status == 'pending':
        reviews = reviews.filter(is_approved=False)
    elif status == 'approved':
        reviews = reviews.filter(is_approved=True)
    
    # Pagination
    paginator = Paginator(reviews.order_by('-created_at'), 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'reviews': page_obj,
        'pending_count': ProductReview.objects.filter(is_approved=False).count(),
        'approved_count': ProductReview.objects.filter(is_approved=True).count(),
    }
    
    return render(request, 'admin_dashboard/reviews.html', context)


@login_required
@user_passes_test(is_admin_or_staff, login_url='/')
def admin_review_approve_view(request, review_id):
    """Admin Review Approve/Reject View"""
    review = get_object_or_404(ProductReview, id=review_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'approve':
            review.is_approved = True
            review.save()
            messages.success(request, 'Review approved successfully!')
        elif action == 'reject':
            review.delete()
            messages.success(request, 'Review rejected and deleted.')
        
        return redirect('admin_dashboard:reviews')
    
    context = {
        'review': review,
    }
    
    return render(request, 'admin_dashboard/review_approve.html', context)


@login_required
@user_passes_test(is_admin_or_staff, login_url='/')
def admin_messages_view(request):
    """Admin Messages/Contact Messages View"""
    messages_list = ContactMessage.objects.all()
    
    # Filters
    status = request.GET.get('status')
    
    if status:
        messages_list = messages_list.filter(status=status)
    
    # Pagination
    paginator = Paginator(messages_list.order_by('-created_at'), 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'messages': page_obj,
        'new_count': ContactMessage.objects.filter(status='new').count(),
        'replied_count': ContactMessage.objects.filter(status='replied').count(),
    }
    
    return render(request, 'admin_dashboard/messages.html', context)


@login_required
@user_passes_test(is_admin_or_staff, login_url='/')
def admin_conversations_view(request):
    """Admin Conversations View"""
    conversations = Conversation.objects.select_related('customer').all()
    
    # Filters
    status = request.GET.get('status')
    assigned = request.GET.get('assigned')
    
    if status:
        conversations = conversations.filter(status=status)
    
    if assigned == 'me':
        conversations = conversations.filter(assigned_to=request.user)
    elif assigned == 'unassigned':
        conversations = conversations.filter(assigned_to=None)
    
    # Pagination
    paginator = Paginator(conversations.order_by('-last_message_at'), 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'conversations': page_obj,
        'open_count': Conversation.objects.filter(status='open').count(),
        'pending_count': Conversation.objects.filter(status='pending').count(),
        'resolved_count': Conversation.objects.filter(status='resolved').count(),
        'my_count': Conversation.objects.filter(assigned_to=request.user).count(),
    }
    
    return render(request, 'admin_dashboard/conversations.html', context)


@login_required
@user_passes_test(is_admin_or_staff, login_url='/')
def admin_conversation_detail_view(request, conversation_id):
    """Admin Conversation Detail View"""
    conversation = get_object_or_404(
        Conversation.objects.select_related('customer'),
        id=conversation_id
    )
    
    if request.method == 'POST':
        from messaging.models import Message
        
        content = request.POST.get('content')
        action = request.POST.get('action')
        
        if content:
            Message.objects.create(
                conversation=conversation,
                sender=request.user,
                content=content,
                is_from_admin=True
            )
            conversation.last_message_at = timezone.now()
            conversation.is_read_by_customer = False
            conversation.save()
            messages.success(request, 'Message sent!')
        
        if action == 'assign':
            conversation.assigned_to = request.user
            conversation.save()
            messages.success(request, 'Conversation assigned to you.')
        elif action == 'resolve':
            conversation.status = 'resolved'
            conversation.resolved_at = timezone.now()
            conversation.save()
            messages.success(request, 'Conversation marked as resolved.')
        elif action == 'close':
            conversation.status = 'closed'
            conversation.save()
            messages.success(request, 'Conversation closed.')
        
        return redirect('admin_dashboard:conversation_detail', conversation_id=conversation.id)
    
    # Mark messages as read
    conversation.messages.filter(is_from_admin=False, is_read=False).update(is_read=True)
    conversation.is_read_by_admin = True
    conversation.admin_last_seen = timezone.now()
    conversation.save()
    
    context = {
        'conversation': conversation,
        'messages': conversation.messages.all(),
    }
    
    return render(request, 'admin_dashboard/conversation_detail.html', context)


@login_required
@user_passes_test(is_admin_or_staff, login_url='/')
def admin_settings_view(request):
    """Admin Site Settings View"""
    site_settings = SiteSetting.get_settings()
    
    if request.method == 'POST':
        site_settings.site_name = request.POST.get('site_name')
        site_settings.site_tagline = request.POST.get('site_tagline')
        site_settings.site_description = request.POST.get('site_description')
        site_settings.contact_email = request.POST.get('contact_email')
        site_settings.contact_phone = request.POST.get('contact_phone')
        site_settings.whatsapp_number = request.POST.get('whatsapp_number')
        site_settings.business_address = request.POST.get('business_address')
        site_settings.business_hours = request.POST.get('business_hours')
        site_settings.facebook_url = request.POST.get('facebook_url')
        site_settings.twitter_url = request.POST.get('twitter_url')
        site_settings.instagram_url = request.POST.get('instagram_url')
        site_settings.free_shipping_threshold = request.POST.get('free_shipping_threshold', 50000)
        site_settings.flat_shipping_rate = request.POST.get('flat_shipping_rate', 2000)
        site_settings.tax_rate = request.POST.get('tax_rate', 0)
        site_settings.enable_reviews = request.POST.get('enable_reviews') == 'on'
        site_settings.enable_wishlist = request.POST.get('enable_wishlist') == 'on'
        site_settings.enable_live_chat = request.POST.get('enable_live_chat') == 'on'
        site_settings.enable_whatsapp = request.POST.get('enable_whatsapp') == 'on'
        
        if request.FILES.get('logo'):
            site_settings.logo = request.FILES.get('logo')
        if request.FILES.get('favicon'):
            site_settings.favicon = request.FILES.get('favicon')
        
        # DELETE banners
        delete_ids = request.POST.getlist('delete_banner_ids[]')

        if delete_ids:
            Banner.objects.filter(id__in=delete_ids).delete()

        # UPDATE existing banners
        banner_ids = request.POST.getlist('banner_id[]')

        for banner_id in banner_ids:
            try:
                banner = Banner.objects.get(id=banner_id)

                banner.title = request.POST.get(f'banner_title_{banner_id}')
                banner.subtitle = request.POST.get(f'banner_subtitle_{banner_id}')
                banner.description = request.POST.get(f'banner_description_{banner_id}')
                banner.link = request.POST.get(f'banner_link_{banner_id}')
                banner.link_text = request.POST.get(f'banner_link_text_{banner_id}')
                banner.position = 'hero'

                # ✅ checkbox fix
                banner.open_in_new_tab = f'banner_new_tab_{banner_id}' in request.POST
                banner.is_active = f'banner_active_{banner_id}' in request.POST

                banner.display_order = int(request.POST.get(f'banner_order_{banner_id}') or 1)

                # image update
                if request.FILES.get(f'banner_image_{banner_id}'):
                    banner.image = request.FILES.get(f'banner_image_{banner_id}')

                banner.save()
            except Banner.DoesNotExist:
                # Handle case where banner was deleted between form load and submit
                continue
            except Exception as e:
                # Log error but continue processing other banners
                print(f"Error updating banner {banner_id}: {e}")
                continue

        # CREATE new banners
        titles = request.POST.getlist('banner_title_new[]')
        subtitles = request.POST.getlist('banner_subtitle_new[]')
        descriptions = request.POST.getlist('banner_description_new[]')
        links = request.POST.getlist('banner_link_new[]')
        link_texts = request.POST.getlist('banner_link_text_new[]')

        images = request.FILES.getlist('banner_image_new[]')

        for i in range(len(titles)):
            Banner.objects.create(
                title=titles[i],
                subtitle=subtitles[i] if i < len(subtitles) else '',
                description=descriptions[i] if i < len(descriptions) else '',
                link=links[i] if i < len(links) else '',
                link_text=link_texts[i] if i < len(link_texts) else 'Learn More',
                image=images[i] if i < len(images) else None,
                position='hero',
                is_active=True if i < len(request.POST.getlist('banner_active_new[]')) else False,
                open_in_new_tab=True if i < len(request.POST.getlist('banner_new_tab_new[]')) else False,
                display_order=i + 1
            )

        site_settings.save()
        messages.success(request, 'Settings updated successfully!')
        return redirect('admin_dashboard:settings')
    
    hero_banners = Banner.objects.filter(position='hero').order_by('display_order')
    context = {
        'settings': site_settings,
        'hero_banners': hero_banners
    }
    
    return render(request, 'admin_dashboard/settings.html', context)


@login_required
@user_passes_test(is_admin_or_staff, login_url='/')
def admin_reports_view(request):
    """Admin Reports/Analytics View"""
    from django.db.models.functions import TruncDate
    
    today = timezone.now().date()
    
    # Sales by date (last 30 days)
    sales_by_date = Order.objects.filter(
        created_at__date__gte=today - timezone.timedelta(days=30),
        payment_status='verified'
    ).annotate(
        date=TruncDate('created_at')
    ).values('date').annotate(
        total=Sum('total'),
        count=Count('id')
    ).order_by('date')
    
    # Top selling products
    top_products = OrderItem.objects.values(
        'product_name'
    ).annotate(
        total_sold=Sum('quantity'),
        total_revenue=Sum('total_price')
    ).order_by('-total_sold')[:10]
    
    # Sales by category
    sales_by_category = OrderItem.objects.filter(
        order__payment_status='verified'
    ).values(
        'product__category__name'
    ).annotate(
        total=Sum('total_price')
    ).order_by('-total')[:10]
    
    context = {
        'sales_by_date': sales_by_date,
        'top_products': top_products,
        'sales_by_category': sales_by_category,
        'total_revenue': Order.objects.filter(payment_status='verified').aggregate(total=Sum('total'))['total'] or 0,
        'total_orders': Order.objects.filter(payment_status='verified').count(),
    }
    
    return render(request, 'admin_dashboard/reports.html', context)


# ============================================
# ADDITIONAL ADMIN DASHBOARD VIEWS
# ============================================

@login_required
@user_passes_test(is_admin_or_staff, login_url='/')
def admin_product_bulk_action_view(request):
    """Admin Product Bulk Action View"""
    if request.method == 'POST':
        action = request.POST.get('action')
        ids = request.POST.get('ids', '').split(',')
        
        if action and ids:
            products = Product.objects.filter(id__in=ids)
            
            if action == 'activate':
                products.update(is_active=True)
                messages.success(request, f'{products.count()} products activated.')
            elif action == 'deactivate':
                products.update(is_active=False)
                messages.success(request, f'{products.count()} products deactivated.')
            elif action == 'delete':
                count = products.count()
                products.delete()
                messages.success(request, f'{count} products deleted.')
    
    return redirect('admin_dashboard:products')


@login_required
@user_passes_test(is_admin_or_staff, login_url='/')
def admin_product_image_delete_view(request, image_id):
    """Admin Product Image Delete View"""
    from products.models import ProductImage
    image = get_object_or_404(ProductImage, id=image_id)
    
    if request.method == 'POST':
        image.delete()
        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False})


@login_required
@user_passes_test(is_admin_or_staff, login_url='/')
def admin_order_status_update_view(request, order_id):
    """Admin Order Status Update View"""
    order = get_object_or_404(Order, id=order_id)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        notes = request.POST.get('notes')
        notify_customer = request.POST.get('notify_customer') == 'true'
        
        if new_status:
            old_status = order.status
            order.status = new_status
            
            if new_status == 'shipped':
                order.shipped_at = timezone.now()
            elif new_status == 'delivered':
                order.delivered_at = timezone.now()
            
            order.save()
            
            # Create order note
            if notes:
                from orders.models import OrderNote
                OrderNote.objects.create(
                    order=order,
                    note=notes,
                    created_by=request.user
                )
            
            # Notify customer if requested
            if notify_customer:
                # TODO: Implement email notification
                pass
            
            messages.success(request, f'Order status updated to {order.get_status_display()}')
    
    return redirect('admin_dashboard:order_detail', order_id=order.id)


@login_required
@user_passes_test(is_admin_or_staff, login_url='/')
def admin_order_add_note_view(request, order_id):
    """Admin Order Add Note View"""
    order = get_object_or_404(Order, id=order_id)
    
    if request.method == 'POST':
        note_text = request.POST.get('note')
        
        if note_text:
            from orders.models import OrderNote
            OrderNote.objects.create(
                order=order,
                note=note_text,
                created_by=request.user
            )
            messages.success(request, 'Note added successfully!')
    
    return redirect('admin_dashboard:order_detail', order_id=order.id)


@login_required
@user_passes_test(is_admin_or_staff, login_url='/')
def admin_order_invoice_view(request, order_id):
    """Admin Order Invoice View"""
    order = get_object_or_404(Order, id=order_id)
    
    context = {
        'order': order,
        'items': order.items.all(),
    }
    
    return render(request, 'admin_dashboard/order_invoice.html', context)


@login_required
@user_passes_test(is_admin_or_staff, login_url='/')
def admin_order_export_view(request):
    """Admin Order Export View"""
    import csv
    from django.http import HttpResponse
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="orders.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Order #', 'Date', 'Customer', 'Email', 'Total', 'Status', 'Payment Status'])
    
    orders = Order.objects.all()
    
    for order in orders:
        writer.writerow([
            order.order_number,
            order.created_at.strftime('%Y-%m-%d %H:%M'),
            order.user.get_full_name(),
            order.user.email,
            order.total,
            order.get_status_display(),
            order.get_payment_status_display(),
        ])
    
    return response


@login_required
@user_passes_test(is_admin_or_staff)
def admin_payment_detail_view(request, payment_id):
    """Admin Payment Detail and Update View"""
    from payments.models import Payment, PaymentVerificationLog
    from decimal import Decimal
    
    payment = get_object_or_404(Payment, id=payment_id)
    order = payment.order
    
    if request.method == 'POST':
        print(f"POST data: {request.POST}")
        
        try:
            old_status = payment.status
            
            # Method field - template sends 'method'
            method = request.POST.get('method')
            if method:
                payment.method = method
            
            # Amount
            amount = request.POST.get('amount')
            if amount:
                payment.amount = Decimal(str(amount))
            
            # Status
            status = request.POST.get('status')
            if status:
                payment.status = status
            
            # Bank details
            payment.bank_name = request.POST.get('bank_name') or None
            payment.account_name = request.POST.get('account_name') or None
            payment.account_number = request.POST.get('account_number') or None
            payment.transfer_reference = request.POST.get('transfer_reference') or None
            
            # Notes
            payment.verification_notes = request.POST.get('verification_notes', '').strip() or None
            payment.rejection_reason = request.POST.get('rejection_reason', '').strip() or None
            
            # Date handling
            transfer_date = request.POST.get('transfer_date')
            transfer_time = request.POST.get('transfer_time', '00:00:00')
            if transfer_date:
                try:
                    from datetime import datetime
                    naive_datetime = datetime.strptime(
                        f"{transfer_date} {transfer_time}", 
                        "%Y-%m-%d %H:%M:%S"
                    )
                    payment.transfer_date = timezone.make_aware(naive_datetime)
                except ValueError as e:
                    print(f"Date error: {e}")
            
            # Files
            if 'receipt' in request.FILES:
                payment.receipt = request.FILES['receipt']
                payment.receipt_uploaded_at = timezone.now()
            
            if 'qr_code' in request.FILES:
                payment.qr_code = request.FILES['qr_code']
            
            # Clear checkboxes
            if request.POST.get('receipt_clear'):
                if payment.receipt:
                    payment.receipt.delete(save=False)
                payment.receipt = None
                payment.receipt_uploaded_at = None
            
            if request.POST.get('qr_code_clear'):
                if payment.qr_code:
                    payment.qr_code.delete(save=False)
                payment.qr_code = None
            
            payment.save()
            
            # Log
            PaymentVerificationLog.objects.create(
                payment=payment,
                action='updated',
                performed_by=request.user,
                old_status=payment.old_status,
                new_status=payment.new_status,
                notes='Payment details updated'
            )
            
            messages.success(request, 'Payment updated successfully!')
            return redirect('admin_dashboard:payment_detail', payment_id=payment.id)
            
        except Exception as e:
            import traceback
            print(f"ERROR: {e}")
            print(traceback.format_exc())
            messages.error(request, f'Error: {str(e)}')
    
    context = {
        'payment': payment,
        'order': order,
    }
    return render(request, 'admin_dashboard/payment_detail.html', context)
@login_required
@user_passes_test(is_admin_or_staff, login_url='/')
def admin_payment_reject_view(request, payment_id):
    """Admin Payment Reject View"""
    payment = get_object_or_404(Payment, id=payment_id)
    
    if request.method == 'POST':
        reason = request.POST.get('reason')
        old_status = payment.status
        
        payment.status = 'rejected'
        payment.rejection_reason = reason
        payment.save()
        
        messages.warning(request, 'Payment has been rejected.')
    
    return redirect('admin_dashboard:payments')


@login_required
@user_passes_test(is_admin_or_staff, login_url='/')
def admin_payment_export_view(request):
    """Admin Payment Export View"""
    import csv
    from django.http import HttpResponse
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="payments.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Reference', 'Order #', 'Customer', 'Amount', 'Method', 'Status', 'Date'])
    
    payments = Payment.objects.all()
    
    for payment in payments:
        writer.writerow([
            payment.reference or 'N/A',
            payment.order.order_number,
            payment.order.user.get_full_name(),
            payment.amount,
            payment.get_payment_method_display(),
            payment.get_status_display(),
            payment.created_at.strftime('%Y-%m-%d %H:%M'),
        ])
    
    return response


@login_required
@user_passes_test(is_admin_or_staff, login_url='/')
def admin_customer_edit_view(request, customer_id):
    """Admin Customer Edit View"""
    customer = get_object_or_404(User, id=customer_id, user_type='customer')
    
    if request.method == 'POST':
        customer.first_name = request.POST.get('first_name', '')
        customer.last_name = request.POST.get('last_name', '')
        customer.email = request.POST.get('email', '')
        customer.phone_number = request.POST.get('phone_number', '')
        customer.save()
        
        messages.success(request, 'Customer updated successfully!')
    
    return redirect('admin_dashboard:customers')


@login_required
@user_passes_test(is_admin_or_staff, login_url='/')
def admin_customer_deactivate_view(request, customer_id):
    """Admin Customer Deactivate View"""
    customer = get_object_or_404(User, id=customer_id, user_type='customer')
    
    if request.method == 'POST':
        customer.is_active = False
        customer.save()
        messages.success(request, f'Customer {customer.get_full_name()} has been deactivated.')
    
    return redirect('admin_dashboard:customers')


@login_required
@user_passes_test(is_admin_or_staff, login_url='/')
def admin_customer_activate_view(request, customer_id):
    """Admin Customer Activate View"""
    customer = get_object_or_404(User, id=customer_id, user_type='customer')
    
    if request.method == 'POST':
        customer.is_active = True
        customer.save()
        messages.success(request, f'Customer {customer.get_full_name()} has been activated.')
    
    return redirect('admin_dashboard:customers')


@login_required
@user_passes_test(is_admin_or_staff, login_url='/')
def admin_customer_export_view(request):
    """Admin Customer Export View"""
    import csv
    from django.http import HttpResponse
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="customers.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Name', 'Email', 'Phone', 'Orders', 'Total Spent', 'Joined', 'Status'])
    
    customers = User.objects.filter(user_type='customer')
    
    for customer in customers:
        writer.writerow([
            customer.get_full_name(),
            customer.email,
            customer.phone_number or 'N/A',
            customer.orders.count(),
            customer.orders.filter(payment_status='verified').aggregate(total=Sum('total'))['total'] or 0,
            customer.date_joined.strftime('%Y-%m-%d'),
            'Active' if customer.is_active else 'Inactive',
        ])
    
    return response


@login_required
@user_passes_test(is_admin_or_staff, login_url='/')
def admin_category_add_view(request):
    """Admin Category Add View"""
    if request.method == 'POST':
        name = request.POST.get('name')
        slug = request.POST.get('slug')
        description = request.POST.get('description')
        icon = request.POST.get('icon')
        parent_id = request.POST.get('parent')
        is_active = request.POST.get('is_active') == 'true'
        
        category = Category.objects.create(
            name=name,
            slug=slug or None,
            description=description,
            icon=icon,
            parent_id=parent_id if parent_id else None,
            is_active=is_active,
        )
        
        if request.FILES.get('image'):
            category.image = request.FILES.get('image')
            category.save()
        
        messages.success(request, f'Category "{name}" created successfully!')
    
    return redirect('admin_dashboard:categories')


@login_required
@user_passes_test(is_admin_or_staff, login_url='/')
def admin_category_edit_view(request, category_id):
    """Admin Category Edit View"""
    category = get_object_or_404(Category, id=category_id)
    
    if request.method == 'POST':
        category.name = request.POST.get('name')
        category.slug = request.POST.get('slug')
        category.description = request.POST.get('description')
        category.icon = request.POST.get('icon')
        
        parent_id = request.POST.get('parent')
        category.parent_id = parent_id if parent_id else None
        
        category.is_active = request.POST.get('is_active') == 'true'
        
        if request.FILES.get('image'):
            category.image = request.FILES.get('image')
        
        category.save()
        messages.success(request, f'Category "{category.name}" updated successfully!')
    
    return redirect('admin_dashboard:categories')


@login_required
@user_passes_test(is_admin_or_staff, login_url='/')
def admin_category_delete_view(request, category_id):
    """Admin Category Delete View"""
    category = get_object_or_404(Category, id=category_id)
    
    if request.method == 'POST':
        category_name = category.name
        category.delete()
        messages.success(request, f'Category "{category_name}" deleted successfully!')
    
    return redirect('admin_dashboard:categories')


@login_required
@user_passes_test(is_admin_or_staff, login_url='/')
def admin_category_toggle_view(request, category_id):
    """Admin Category Toggle Status View"""
    category = get_object_or_404(Category, id=category_id)
    
    if request.method == 'POST':
        import json
        data = json.loads(request.body)
        category.is_active = data.get('is_active', not category.is_active)
        category.save()
        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False})


@login_required
@user_passes_test(is_admin_or_staff, login_url='/')
def admin_brand_add_view(request):
    """Admin Brand Add View"""
    if request.method == 'POST':
        name = request.POST.get('name')
        slug = request.POST.get('slug')
        description = request.POST.get('description')
        website = request.POST.get('website')
        is_active = request.POST.get('is_active') == 'on'
        is_featured = request.POST.get('is_featured') == 'on'
        
        brand = Brand.objects.create(
            name=name,
            slug=slug or None,
            description=description,
            website=website,
            is_active=is_active,
            is_featured=is_featured,
        )
        
        if request.FILES.get('logo'):
            brand.logo = request.FILES.get('logo')
            brand.save()
        
        messages.success(request, f'Brand "{name}" created successfully!')
    
    return redirect('admin_dashboard:brands')


@login_required
@user_passes_test(is_admin_or_staff, login_url='/')
def admin_brand_edit_view(request, brand_id):
    """Admin Brand Edit View"""
    brand = get_object_or_404(Brand, id=brand_id)
    
    if request.method == 'POST':
        brand.name = request.POST.get('name')
        brand.slug = request.POST.get('slug')
        brand.description = request.POST.get('description')
        brand.website = request.POST.get('website')
        brand.is_active = request.POST.get('is_active') == 'on'
        brand.is_featured = request.POST.get('is_featured') == 'on'
        
        if request.FILES.get('logo'):
            brand.logo = request.FILES.get('logo')
        
        brand.save()
        messages.success(request, f'Brand "{brand.name}" updated successfully!')
    
    return redirect('admin_dashboard:brands')


@login_required
@user_passes_test(is_admin_or_staff, login_url='/')
def admin_brand_delete_view(request, brand_id):
    """Admin Brand Delete View"""
    brand = get_object_or_404(Brand, id=brand_id)
    
    if request.method == 'POST':
        brand_name = brand.name
        brand.delete()
        messages.success(request, f'Brand "{brand_name}" deleted successfully!')
    
    return redirect('admin_dashboard:brands')


@login_required
@user_passes_test(is_admin_or_staff, login_url='/')
def admin_review_reject_view(request, review_id):
    """Admin Review Reject View"""
    review = get_object_or_404(ProductReview, id=review_id)
    
    if request.method == 'POST':
        review.status = 'rejected'
        review.save()
        messages.success(request, 'Review rejected.')
    
    return redirect('admin_dashboard:reviews')


@login_required
@user_passes_test(is_admin_or_staff, login_url='/')
def admin_review_delete_view(request, review_id):
    """Admin Review Delete View"""
    review = get_object_or_404(ProductReview, id=review_id)
    
    if request.method == 'POST':
        review.delete()
        messages.success(request, 'Review deleted successfully!')
    
    return redirect('admin_dashboard:reviews')


@login_required
@user_passes_test(is_admin_or_staff, login_url='/')
def admin_message_detail_view(request, conversation_id):
    """Admin Message Detail View"""
    conversation = get_object_or_404(Conversation, id=conversation_id)
    
    context = {
        'conversation': conversation,
        'messages': conversation.messages.all(),
    }
    
    return render(request, 'admin_dashboard/message_detail.html', context)


@login_required
@user_passes_test(is_admin_or_staff, login_url='/')
def admin_conversation_close_view(request, conversation_id):
    """Admin Conversation Close View"""
    conversation = get_object_or_404(Conversation, id=conversation_id)
    
    if request.method == 'POST':
        conversation.status = 'closed'
        conversation.save()
        messages.success(request, 'Conversation closed.')
    
    return redirect('admin_dashboard:messages')


@login_required
@user_passes_test(is_admin_or_staff, login_url='/')
def admin_settings_save_view(request):
    """Admin Settings Save View"""
    site_settings = SiteSetting.get_settings()
    
    if request.method == 'POST':
        site_settings.site_name = request.POST.get('site_name', site_settings.site_name)
        site_settings.site_tagline = request.POST.get('site_tagline', '')
        site_settings.contact_email = request.POST.get('contact_email', '')
        site_settings.contact_phone = request.POST.get('contact_phone', '')
        site_settings.contact_address = request.POST.get('contact_address', '')
        site_settings.business_hours = request.POST.get('business_hours', '')
        site_settings.whatsapp_number = request.POST.get('whatsapp_number', '')
        site_settings.facebook_url = request.POST.get('facebook_url', '')
        site_settings.twitter_url = request.POST.get('twitter_url', '')
        site_settings.instagram_url = request.POST.get('instagram_url', '')
        site_settings.youtube_url = request.POST.get('youtube_url', '')
        site_settings.bank_name = request.POST.get('bank_name', '')
        site_settings.bank_account_number = request.POST.get('bank_account_number', '')
        site_settings.bank_account_name = request.POST.get('bank_account_name', '')
        site_settings.payment_instructions = request.POST.get('payment_instructions', '')
        site_settings.cod_enabled = request.POST.get('cod_enabled') == 'true'
        site_settings.flat_shipping_rate = request.POST.get('flat_shipping_rate', 0)
        site_settings.free_shipping_threshold = request.POST.get('free_shipping_threshold', 0)
        site_settings.meta_title = request.POST.get('meta_title', '')
        site_settings.meta_description = request.POST.get('meta_description', '')
        site_settings.meta_keywords = request.POST.get('meta_keywords', '')
        site_settings.google_analytics_id = request.POST.get('google_analytics_id', '')
        site_settings.maintenance_mode = request.POST.get('maintenance_mode') == 'true'
        site_settings.currency_symbol = request.POST.get('currency_symbol', '₦')
        
        if request.FILES.get('logo'):
            site_settings.logo = request.FILES.get('logo')
        if request.FILES.get('favicon'):
            site_settings.favicon = request.FILES.get('favicon')
        
        site_settings.save()
        messages.success(request, 'Settings saved successfully!')
    
    return redirect('admin_dashboard:settings')


@login_required
@user_passes_test(is_admin_or_staff, login_url='/')
def admin_sales_report_view(request):
    """Admin Sales Report View"""
    context = {
        'report_type': 'sales',
    }
    return render(request, 'admin_dashboard/reports.html', context)


@login_required
@user_passes_test(is_admin_or_staff, login_url='/')
def admin_products_report_view(request):
    """Admin Products Report View"""
    context = {
        'report_type': 'products',
    }
    return render(request, 'admin_dashboard/reports.html', context)


@login_required
@user_passes_test(is_admin_or_staff, login_url='/')
def admin_customers_report_view(request):
    """Admin Customers Report View"""
    context = {
        'report_type': 'customers',
    }
    return render(request, 'admin_dashboard/reports.html', context)


@login_required
@user_passes_test(is_admin_or_staff, login_url='/')
def admin_notifications_list_view(request):
    """Admin view to list all notifications with filtering"""
    from notifications.models import Notification
    
    notifications = Notification.objects.all().select_related('user').order_by('-created_at')
    
    # Filtering
    filter_type = request.GET.get('type', '')
    filter_status = request.GET.get('status', '')
    filter_priority = request.GET.get('priority', '')
    search_query = request.GET.get('q', '')
    
    if filter_type:
        notifications = notifications.filter(notification_type=filter_type)
    if filter_status:
        if filter_status == 'read':
            notifications = notifications.filter(is_read=True)
        elif filter_status == 'unread':
            notifications = notifications.filter(is_read=False)
    if filter_priority:
        notifications = notifications.filter(priority=filter_priority)
    if search_query:
        notifications = notifications.filter(
            Q(title__icontains=search_query) |
            Q(message__icontains=search_query) |
            Q(user__email__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(notifications, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Stats
    total_count = Notification.objects.count()
    unread_count = Notification.objects.filter(is_read=False).count()
    today_count = Notification.objects.filter(created_at__date=timezone.now().date()).count()
    
    # Get choices from the model field using _meta API
    notification_type_field = Notification._meta.get_field('notification_type')
    priority_field = Notification._meta.get_field('priority')
    
    context = {
        'page_obj': page_obj,
        'total_count': total_count,
        'unread_count': unread_count,
        'today_count': today_count,
        'filter_type': filter_type,
        'filter_status': filter_status,
        'filter_priority': filter_priority,
        'search_query': search_query,
        'notification_types': notification_type_field.choices,
        'priority_choices': priority_field.choices,
    }
    return render(request, 'admin_dashboard/notifications/list.html', context)


@login_required
@user_passes_test(is_admin_or_staff, login_url='/')
def admin_notification_create_view(request):
    """Admin view to create new notification"""
    if request.method == 'POST':
        form = NotificationForm(request.POST)
        if form.is_valid():
            notification = form.save()
            messages.success(request, f'Notification created successfully for {notification.user.email}')
            return redirect('admin_dashboard:notifications_list')
    else:
        form = NotificationForm()
    
    context = {
        'form': form,
        'title': 'Create Notification',
    }
    return render(request, 'admin_dashboard/notifications/form.html', context)


@login_required
@user_passes_test(is_admin_or_staff, login_url='/')
def admin_notification_detail_view(request, notification_id):
    """Admin view to view notification details"""
    notification = get_object_or_404(Notification, id=notification_id)
    
    context = {
        'notification': notification,
    }
    return render(request, 'admin_dashboard/notifications/detail.html', context)


@login_required
@user_passes_test(is_admin_or_staff, login_url='/')
def admin_notification_edit_view(request, notification_id):
    """Admin view to edit notification"""
    notification = get_object_or_404(Notification, id=notification_id)
    
    if request.method == 'POST':
        form = NotificationForm(request.POST, instance=notification)
        if form.is_valid():
            form.save()
            messages.success(request, 'Notification updated successfully')
            return redirect('admin_dashboard:notifications_list')
    else:
        form = NotificationForm(instance=notification)
    
    context = {
        'form': form,
        'notification': notification,
        'title': 'Edit Notification',
    }
    return render(request, 'admin_dashboard/notifications/form.html', context)


@login_required
@user_passes_test(is_admin_or_staff, login_url='/')
def admin_notification_delete_view(request, notification_id):
    """Admin view to delete notification"""
    notification = get_object_or_404(Notification, id=notification_id)
    
    if request.method == 'POST':
        notification.delete()
        messages.success(request, 'Notification deleted successfully')
        return redirect('admin_dashboard:notifications_list')
    
    context = {
        'notification': notification,
    }
    return render(request, 'admin_dashboard/notifications/delete_confirm.html', context)


@login_required
@user_passes_test(is_admin_or_staff, login_url='/')
def admin_notification_bulk_action_view(request):
    """Handle bulk actions on notifications"""
    if request.method == 'POST':
        action = request.POST.get('action')
        selected_ids = request.POST.getlist('selected_notifications')
        
        if not selected_ids:
            messages.warning(request, 'No notifications selected')
            return redirect('admin_dashboard:notifications_list')
        
        notifications = Notification.objects.filter(id__in=selected_ids)
        
        if action == 'mark_read':
            count = notifications.update(is_read=True, read_at=timezone.now())
            messages.success(request, f'{count} notifications marked as read')
        elif action == 'mark_unread':
            count = notifications.update(is_read=False, read_at=None)
            messages.success(request, f'{count} notifications marked as unread')
        elif action == 'delete':
            count = notifications.count()
            notifications.delete()
            messages.success(request, f'{count} notifications deleted')
        elif action == 'resend':
            messages.success(request, f'Resending {notifications.count()} notifications')
    
    return redirect('admin_dashboard:notifications_list')


@login_required
@user_passes_test(is_admin_or_staff, login_url='/')
def admin_notification_templates_view(request):
    """List notification templates"""
    templates = NotificationTemplate.objects.all().order_by('-updated_at')
    context = {
        'templates': templates,
    }
    return render(request, 'admin_dashboard/notifications/template_list.html', context)


@login_required
@user_passes_test(is_admin_or_staff, login_url='/')
def admin_notification_template_create_view(request):
    """Create notification template"""
    if request.method == 'POST':
        form = NotificationTemplateForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Template created successfully')
            return redirect('admin_dashboard:notification_templates')
    else:
        form = NotificationTemplateForm()
    
    context = {
        'form': form,
        'title': 'Create Template',
    }
    return render(request, 'admin_dashboard/notifications/template_form.html', context)


@login_required
@user_passes_test(is_admin_or_staff, login_url='/')
def admin_notification_template_edit_view(request, template_id):
    """Edit notification template"""
    template = get_object_or_404(NotificationTemplate, id=template_id)
    
    if request.method == 'POST':
        form = NotificationTemplateForm(request.POST, instance=template)
        if form.is_valid():
            form.save()
            messages.success(request, 'Template updated successfully')
            return redirect('admin_dashboard:notification_templates')
    else:
        form = NotificationTemplateForm(instance=template)
    
    context = {
        'form': form,
        'template': template,
        'title': 'Edit Template',
    }
    return render(request, 'admin_dashboard/notifications/template_form.html', context)


@login_required
@user_passes_test(is_admin_or_staff, login_url='/')
def admin_notification_template_delete_view(request, template_id):
    """Delete notification template"""
    template = get_object_or_404(NotificationTemplate, id=template_id)
    
    if request.method == 'POST':
        template.delete()
        messages.success(request, 'Template deleted successfully')
        return redirect('admin_dashboard:notification_templates')
    
    context = {
        'template': template,
    }
    return render(request, 'admin_dashboard/notifications/template_delete.html', context)


@login_required
@user_passes_test(is_admin_or_staff, login_url='/')
def admin_bulk_notifications_view(request):
    """List bulk notifications"""
    bulk_notifications = BulkNotification.objects.all().order_by('-created_at')
    context = {
        'bulk_notifications': bulk_notifications,
    }
    return render(request, 'admin_dashboard/notifications/bulk_list.html', context)


@login_required
@user_passes_test(is_admin_or_staff, login_url='/')
def admin_bulk_notification_create_view(request):
    """Create bulk notification"""
    if request.method == 'POST':
        form = BulkNotificationForm(request.POST)
        if form.is_valid():
            bulk = form.save(commit=False)
            bulk.save()
            form.save_m2m()
            messages.success(request, 'Bulk notification created successfully')
            return redirect('admin_dashboard:bulk_notifications')
    else:
        form = BulkNotificationForm()
    
    context = {
        'form': form,
        'title': 'Create Bulk Notification',
    }
    return render(request, 'admin_dashboard/notifications/bulk_form.html', context)


@login_required
@user_passes_test(is_admin_or_staff, login_url='/')
def admin_bulk_notification_send_view(request, bulk_id):
    """Send bulk notification"""
    bulk = get_object_or_404(BulkNotification, id=bulk_id)
    
    if bulk.status == 'draft':
        bulk.status = 'sending'
        bulk.sent_at = timezone.now()
        bulk.save()
        messages.success(request, 'Bulk notification is being sent')
    else:
        messages.warning(request, 'This notification has already been sent or is being sent')
    
    return redirect('admin_dashboard:bulk_notifications')


@login_required
@user_passes_test(is_admin_or_staff, login_url='/')
def admin_bulk_notification_delete_view(request, bulk_id):
    """Delete bulk notification"""
    bulk = get_object_or_404(BulkNotification, id=bulk_id)
    
    if request.method == 'POST':
        bulk.delete()
        messages.success(request, 'Bulk notification deleted successfully')
        return redirect('admin_dashboard:bulk_notifications')
    
    context = {
        'bulk': bulk,
    }
    return render(request, 'admin_dashboard/notifications/bulk_delete.html', context)