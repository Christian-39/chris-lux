"""
Views for dashboard app.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Sum, Count, Avg, Q
from django.db.models.functions import TruncDate, TruncMonth
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.http import JsonResponse
from datetime import datetime, timedelta
from decimal import Decimal

from orders.models import Order, OrderItem
from products.models import Product, Category
from users.models import User
from payments.models import PaymentReceipt
from notifications.models import Notification
from .models import ActivityLog


def is_staff(user):
    """Check if user is staff."""
    return user.is_staff


@login_required
@user_passes_test(is_staff)
def dashboard_home(request):
    """Main dashboard view."""
    # Date range for analytics
    today = timezone.now().date()
    start_of_month = today.replace(day=1)
    last_30_days = today - timedelta(days=30)
    
    # Sales statistics
    total_sales = Order.objects.filter(
        status__in=['verified', 'processing', 'shipped', 'delivered']
    ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0')
    
    monthly_sales = Order.objects.filter(
        status__in=['verified', 'processing', 'shipped', 'delivered'],
        created_at__date__gte=start_of_month
    ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0')
    
    daily_sales = Order.objects.filter(
        status__in=['verified', 'processing', 'shipped', 'delivered'],
        created_at__date=today
    ).aggregate(total=Sum('total_amount'))['total'] or Decimal('0')
    
    # Order statistics
    total_orders = Order.objects.count()
    pending_orders = Order.objects.filter(status='pending_payment').count()
    processing_orders = Order.objects.filter(status__in=['payment_uploaded', 'verified', 'processing']).count()
    shipped_orders = Order.objects.filter(status='shipped').count()
    delivered_orders = Order.objects.filter(status='delivered').count()
    
    # Recent orders
    recent_orders = Order.objects.select_related('user').prefetch_related('items').order_by('-created_at')[:10]
    
    # Pending receipts
    pending_receipts = PaymentReceipt.objects.filter(
        status='pending'
    ).select_related('order', 'user').order_by('-created_at')[:5]
    pending_receipts_count = PaymentReceipt.objects.filter(status='pending').count()
    
    # Low stock products
    low_stock_products = Product.objects.filter(
        track_inventory=True,
        stock_quantity__lte=5,
        is_active=True
    ).order_by('stock_quantity')[:5]
    low_stock_count = Product.objects.filter(
        track_inventory=True,
        stock_quantity__lte=5,
        is_active=True
    ).count()
    
    # Customer statistics
    total_customers = User.objects.filter(is_staff=False).count()
    new_customers_this_month = User.objects.filter(
        is_staff=False,
        date_joined__date__gte=start_of_month
    ).count()
    
    # Top products
    top_products = OrderItem.objects.filter(
        order__status__in=['verified', 'processing', 'shipped', 'delivered']
    ).values(
        'product__name', 'product__slug'
    ).annotate(
        total_sold=Sum('quantity'),
        total_revenue=Sum('price')
    ).order_by('-total_sold')[:5]
    
    # Sales chart data (last 30 days)
    sales_data = Order.objects.filter(
        status__in=['verified', 'processing', 'shipped', 'delivered'],
        created_at__date__gte=last_30_days
    ).annotate(
        date=TruncDate('created_at')
    ).values('date').annotate(
        total=Sum('total_amount')
    ).order_by('date')
    
    # Activity logs
    recent_activity = ActivityLog.objects.select_related('user').order_by('-created_at')[:10]
    
    context = {
        # Sales
        'total_sales': total_sales,
        'monthly_sales': monthly_sales,
        'daily_sales': daily_sales,
        
        # Orders
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'processing_orders': processing_orders,
        'shipped_orders': shipped_orders,
        'delivered_orders': delivered_orders,
        
        # Recent data
        'recent_orders': recent_orders,
        'pending_receipts': pending_receipts,
        'pending_receipts_count': pending_receipts_count,
        'low_stock_products': low_stock_products,
        'low_stock_count': low_stock_count,
        
        # Customers
        'total_customers': total_customers,
        'new_customers_this_month': new_customers_this_month,
        
        # Products
        'top_products': top_products,
        
        # Chart data
        'sales_chart_labels': [d['date'].strftime('%b %d') for d in sales_data],
        'sales_chart_data': [float(d['total']) for d in sales_data],
        
        # Activity
        'recent_activity': recent_activity,
    }
    
    return render(request, 'dashboard/dashboard.html', context)


@login_required
@user_passes_test(is_staff)
def orders_management(request):
    """Order management view."""
    # Filters
    status = request.GET.get('status', '')
    search = request.GET.get('search', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    orders = Order.objects.select_related('user').prefetch_related('items')
    
    if status:
        orders = orders.filter(status=status)
    
    if search:
        orders = orders.filter(
            Q(order_number__icontains=search) |
            Q(user__username__icontains=search) |
            Q(user__email__icontains=search)
        )
    
    if date_from:
        orders = orders.filter(created_at__date__gte=parse_date(date_from))
    
    if date_to:
        orders = orders.filter(created_at__date__lte=parse_date(date_to))
    
    orders = orders.order_by('-created_at')
    
    # Status counts
    status_counts = {
        'all': Order.objects.count(),
        'pending_payment': Order.objects.filter(status='pending_payment').count(),
        'payment_uploaded': Order.objects.filter(status='payment_uploaded').count(),
        'verified': Order.objects.filter(status='verified').count(),
        'processing': Order.objects.filter(status='processing').count(),
        'shipped': Order.objects.filter(status='shipped').count(),
        'delivered': Order.objects.filter(status='delivered').count(),
        'cancelled': Order.objects.filter(status='cancelled').count(),
    }
    
    return render(request, 'dashboard/orders.html', {
        'orders': orders,
        'status_counts': status_counts,
        'current_status': status,
        'search': search,
        'date_from': date_from,
        'date_to': date_to,
    })


@login_required
@user_passes_test(is_staff)
def order_detail(request, order_id):
    """Order detail view for admin."""
    order = get_object_or_404(
        Order.objects.select_related('user').prefetch_related(
            'items', 'status_history', 'receipts'
        ),
        id=order_id
    )
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        note = request.POST.get('note', '')
        tracking_number = request.POST.get('tracking_number', '')
        
        if new_status and new_status != order.status:
            old_status = order.status
            order.status = new_status
            
            if tracking_number:
                order.tracking_number = tracking_number
            
            if new_status == 'shipped':
                order.shipped_at = timezone.now()
            elif new_status == 'delivered':
                order.delivered_at = timezone.now()
            
            order.save()
            
            # Create status history
            from orders.models import OrderStatusHistory
            OrderStatusHistory.objects.create(
                order=order,
                old_status=old_status,
                new_status=new_status,
                changed_by=request.user,
                note=note,
            )
            
            # Create notification
            Notification.objects.create(
                user=order.user,
                notification_type='order',
                title=f'Order {new_status.replace("_", " ").title()}',
                message=f'Your order {order.order_number} status has been updated to {new_status.replace("_", " ").title()}.',
                order=order,
            )
            
            messages.success(request, 'Order status updated successfully!')
        
        return redirect('dashboard:order_detail', order_id=order.id)
    
    return render(request, 'dashboard/order_detail.html', {
        'order': order,
    })


@login_required
@user_passes_test(is_staff)
def products_management(request):
    """Product management view."""
    # Filters
    category = request.GET.get('category', '')
    status = request.GET.get('status', '')
    search = request.GET.get('search', '')
    stock = request.GET.get('stock', '')
    
    products = Product.objects.select_related('category').prefetch_related('images')
    
    if category:
        products = products.filter(category__slug=category)
    
    if status == 'active':
        products = products.filter(is_active=True)
    elif status == 'inactive':
        products = products.filter(is_active=False)
    
    if search:
        products = products.filter(
            Q(name__icontains=search) |
            Q(sku__icontains=search) |
            Q(description__icontains=search)
        )
    
    if stock == 'low':
        products = products.filter(track_inventory=True, stock_quantity__lte=5)
    elif stock == 'out':
        products = products.filter(track_inventory=True, stock_quantity=0)
    
    products = products.order_by('-created_at')
    
    categories = Category.objects.filter(is_active=True)
    
    return render(request, 'dashboard/products.html', {
        'products': products,
        'categories': categories,
        'current_category': category,
        'current_status': status,
        'search': search,
        'current_stock': stock,
    })


@login_required
@user_passes_test(is_staff)
def customers_management(request):
    """Customer management view."""
    search = request.GET.get('search', '')
    
    customers = User.objects.filter(is_staff=False).annotate(
        orders_count=Count('orders'),
        total_spent=Sum('orders__total_amount', filter=Q(orders__status__in=['verified', 'delivered']))
    ).order_by('-date_joined')
    
    if search:
        customers = customers.filter(
            Q(username__icontains=search) |
            Q(email__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search)
        )
    
    return render(request, 'dashboard/customers.html', {
        'customers': customers,
        'search': search,
    })


@login_required
@user_passes_test(is_staff)
def sales_analytics(request):
    """Sales analytics view."""
    # Date range
    period = request.GET.get('period', 'month')
    
    if period == 'week':
        start_date = timezone.now().date() - timedelta(days=7)
    elif period == 'month':
        start_date = timezone.now().date().replace(day=1)
    elif period == 'year':
        start_date = timezone.now().date().replace(month=1, day=1)
    else:
        start_date = timezone.now().date() - timedelta(days=30)
    
    # Sales by date
    sales_by_date = Order.objects.filter(
        status__in=['verified', 'processing', 'shipped', 'delivered'],
        created_at__date__gte=start_date
    ).annotate(
        date=TruncDate('created_at')
    ).values('date').annotate(
        total=Sum('total_amount'),
        count=Count('id')
    ).order_by('date')
    
    # Sales by category
    sales_by_category = OrderItem.objects.filter(
        order__status__in=['verified', 'processing', 'shipped', 'delivered'],
        order__created_at__date__gte=start_date
    ).values(
        'product__category__name'
    ).annotate(
        total=Sum('price'),
        count=Count('id')
    ).order_by('-total')
    
    # Sales by product type
    sales_by_type = OrderItem.objects.filter(
        order__status__in=['verified', 'processing', 'shipped', 'delivered'],
        order__created_at__date__gte=start_date
    ).values(
        'product__product_type'
    ).annotate(
        total=Sum('price'),
        count=Count('id')
    ).order_by('-total')
    
    # Top customers
    top_customers = User.objects.filter(
        is_staff=False,
        orders__status__in=['verified', 'processing', 'shipped', 'delivered'],
        orders__created_at__date__gte=start_date
    ).annotate(
        total_orders=Count('orders'),
        total_spent=Sum('orders__total_amount')
    ).order_by('-total_spent')[:10]
    
    return render(request, 'dashboard/analytics.html', {
        'period': period,
        'sales_by_date': sales_by_date,
        'sales_by_category': sales_by_category,
        'sales_by_type': sales_by_type,
        'top_customers': top_customers,
    })


@login_required
@user_passes_test(is_staff)
def activity_logs(request):
    """Activity logs view."""
    logs = ActivityLog.objects.select_related('user').order_by('-created_at')[:100]
    return render(request, 'dashboard/activity_logs.html', {
        'logs': logs,
    })


@login_required
@user_passes_test(is_staff)
def inventory_report(request):
    """Inventory report view."""
    # Low stock products
    low_stock = Product.objects.filter(
        track_inventory=True,
        stock_quantity__lte=5,
        is_active=True
    ).order_by('stock_quantity')
    
    # Out of stock products
    out_of_stock = Product.objects.filter(
        track_inventory=True,
        stock_quantity=0,
        is_active=True
    )
    
    # Inventory value
    inventory_value = Product.objects.filter(
        track_inventory=True
    ).aggregate(
        total=Sum('stock_quantity' * 'cost_per_item')
    )['total'] or Decimal('0')
    
    return render(request, 'dashboard/inventory.html', {
        'low_stock': low_stock,
        'out_of_stock': out_of_stock,
        'inventory_value': inventory_value,
    })
