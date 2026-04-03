"""
Products Views - Product Catalog, Categories, Reviews
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Avg, Count
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils import timezone

from .models import Product, Category, Brand, ProductReview, Wishlist, RecentlyViewed, FlashSale
from orders.models import FrequentlyBoughtTogether


def product_list_view(request):
    """Product List View"""
    products = Product.objects.filter(is_active=True)
    
    # Filters
    category_slug = request.GET.get('category')
    brand_slug = request.GET.get('brand')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    condition = request.GET.get('condition')
    in_stock = request.GET.get('in_stock')
    sort_by = request.GET.get('sort', 'newest')
    
    if category_slug:
        category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=category)
    
    if brand_slug:
        brand = get_object_or_404(Brand, slug=brand_slug)
        products = products.filter(brand=brand)
    
    if min_price:
        products = products.filter(price__gte=min_price)
    
    if max_price:
        products = products.filter(price__lte=max_price)
    
    if condition:
        products = products.filter(condition=condition)
    
    if in_stock:
        products = products.filter(stock_status__in=['in_stock', 'low_stock'])
    
    # Sorting
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
    elif sort_by == 'name_asc':
        products = products.order_by('name')
    elif sort_by == 'name_desc':
        products = products.order_by('-name')
    
    # Pagination
    paginator = Paginator(products, 24)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Filter options
    categories = Category.objects.filter(is_active=True, parent=None)
    brands = Brand.objects.filter(is_active=True)
    
    context = {
        'products': page_obj,
        'categories': categories,
        'brands': brands,
        'page_obj': page_obj,
        'paginator': paginator,
        'total_results': paginator.count,
        'current_category': category_slug,
        'current_brand': brand_slug,
        'current_sort': sort_by,
    }
    
    return render(request, 'products/product_list.html', context)


def product_detail_view(request, slug):
    """Product Detail View"""
    product = get_object_or_404(
        Product.objects.select_related('category', 'brand')
        .prefetch_related('images', 'reviews'),
        slug=slug,
        is_active=True
    )
    
    # Increment view count
    product.increment_view()
    
    # Track recently viewed
    if request.user.is_authenticated:
        RecentlyViewed.objects.update_or_create(
            user=request.user,
            product=product,
            defaults={'viewed_at': timezone.now()}
        )
        # Keep only last 10 items
        recently_viewed = RecentlyViewed.objects.filter(
            user=request.user
        ).order_by('-viewed_at')[10:]
        recently_viewed.delete()
    
    # Get reviews
    reviews = product.reviews.filter(is_approved=True).select_related('user')
    review_count = reviews.count()
    average_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
    
    # Rating distribution
    rating_distribution = {}
    for i in range(5, 0, -1):
        rating_distribution[i] = reviews.filter(rating=i).count()
    
    # Related products
    related_products = Product.objects.filter(
        category=product.category,
        is_active=True
    ).exclude(id=product.id)[:8]
    
    # Frequently bought together
    frequently_bought = FrequentlyBoughtTogether.objects.filter(
        primary_product=product,
        is_active=True
    ).select_related('related_product')[:4]
    
    # Check if in wishlist
    in_wishlist = False
    if request.user.is_authenticated:
        in_wishlist = Wishlist.objects.filter(
            user=request.user,
            product=product
        ).exists()
    
    # Check for flash sale
    flash_sale = FlashSale.objects.filter(
        product=product,
        is_active=True,
        starts_at__lte=timezone.now(),
        ends_at__gte=timezone.now()
    ).first()
    
    context = {
        'product': product,
        'reviews': reviews[:10],
        'review_count': review_count,
        'average_rating': round(average_rating, 1),
        'rating_distribution': rating_distribution,
        'related_products': related_products,
        'frequently_bought': frequently_bought,
        'in_wishlist': in_wishlist,
        'flash_sale': flash_sale,
    }
    
    return render(request, 'products/product_detail.html', context)


def category_view(request, slug):
    """Category View"""
    category = get_object_or_404(Category, slug=slug, is_active=True)
    
    # Get products in this category and subcategories
    category_ids = [category.id]
    category_ids.extend(category.subcategories.values_list('id', flat=True))
    
    products = Product.objects.filter(
        category_id__in=category_ids,
        is_active=True
    )
    
    # Apply filters
    brand_slug = request.GET.get('brand')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    sort_by = request.GET.get('sort', 'newest')
    
    if brand_slug:
        products = products.filter(brand__slug=brand_slug)
    
    if min_price:
        products = products.filter(price__gte=min_price)
    
    if max_price:
        products = products.filter(price__lte=max_price)
    
    # Sorting
    if sort_by == 'price_low':
        products = products.order_by('price')
    elif sort_by == 'price_high':
        products = products.order_by('-price')
    elif sort_by == 'newest':
        products = products.order_by('-created_at')
    elif sort_by == 'popular':
        products = products.order_by('-sales_count')
    
    # Pagination
    paginator = Paginator(products, 24)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get brands in this category
    brands = Brand.objects.filter(
        products__category_id__in=category_ids,
        is_active=True
    ).distinct()
    
    context = {
        'category': category,
        'products': page_obj,
        'brands': brands,
        'page_obj': page_obj,
        'paginator': paginator,
        'total_results': paginator.count,
    }
    
    return render(request, 'products/category.html', context)


def brand_view(request, slug):
    """Brand View"""
    brand = get_object_or_404(Brand, slug=slug, is_active=True)
    
    products = Product.objects.filter(brand=brand, is_active=True)
    
    # Apply filters
    category_slug = request.GET.get('category')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    sort_by = request.GET.get('sort', 'newest')
    
    if category_slug:
        products = products.filter(category__slug=category_slug)
    
    if min_price:
        products = products.filter(price__gte=min_price)
    
    if max_price:
        products = products.filter(price__lte=max_price)
    
    # Sorting
    if sort_by == 'price_low':
        products = products.order_by('price')
    elif sort_by == 'price_high':
        products = products.order_by('-price')
    elif sort_by == 'newest':
        products = products.order_by('-created_at')
    elif sort_by == 'popular':
        products = products.order_by('-sales_count')
    
    # Pagination
    paginator = Paginator(products, 24)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'brand': brand,
        'products': page_obj,
        'page_obj': page_obj,
        'paginator': paginator,
        'total_results': paginator.count,
    }
    
    return render(request, 'products/brand.html', context)


def hot_deals_view(request):
    """Hot Deals View"""
    products = Product.objects.filter(
        is_active=True,
        is_hot_deal=True
    )
    
    # Pagination
    paginator = Paginator(products, 24)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'products': page_obj,
        'page_obj': page_obj,
        'paginator': paginator,
        'title': 'Hot Deals',
    }
    
    return render(request, 'products/deals.html', context)


def new_arrivals_view(request):
    """New Arrivals View"""
    products = Product.objects.filter(
        is_active=True,
        is_new_arrival=True
    )
    
    # Pagination
    paginator = Paginator(products, 24)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'products': page_obj,
        'page_obj': page_obj,
        'paginator': paginator,
        'title': 'New Arrivals',
    }
    
    return render(request, 'products/deals.html', context)


def flash_sales_view(request):
    """Flash Sales View"""
    flash_sales = FlashSale.objects.filter(
        is_active=True,
        starts_at__lte=timezone.now(),
        ends_at__gte=timezone.now()
    ).select_related('product')
    
    # Pagination
    paginator = Paginator(flash_sales, 24)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'flash_sales': page_obj,
        'page_obj': page_obj,
        'paginator': paginator,
        'title': 'Flash Sales',
    }
    
    return render(request, 'products/flash_sales.html', context)


@login_required
def add_review_view(request, product_slug):
    """Add Product Review View"""
    product = get_object_or_404(Product, slug=product_slug, is_active=True)
    
    if request.method == 'POST':
        rating = request.POST.get('rating')
        title = request.POST.get('title', '')
        comment = request.POST.get('comment', '')
        
        if rating and comment:
            # Check if user has purchased this product
            has_purchased = request.user.orders.filter(
                items__product=product,
                status='delivered'
            ).exists()
            
            review, created = ProductReview.objects.update_or_create(
                product=product,
                user=request.user,
                defaults={
                    'rating': rating,
                    'title': title,
                    'comment': comment,
                    'is_verified_purchase': has_purchased,
                    'is_approved': True  # Auto-approve for now
                }
            )
            
            if created:
                messages.success(request, 'Your review has been submitted.')
            else:
                messages.success(request, 'Your review has been updated.')
        else:
            messages.error(request, 'Please provide a rating and comment.')
    
    return redirect('products:product_detail', slug=product_slug)


@login_required
def add_to_wishlist_view(request, product_slug):
    """Add to Wishlist View"""
    product = get_object_or_404(Product, slug=product_slug, is_active=True)
    
    wishlist_item, created = Wishlist.objects.get_or_create(
        user=request.user,
        product=product
    )
    
    if created:
        messages.success(request, f'{product.name} has been added to your wishlist.')
    else:
        messages.info(request, f'{product.name} is already in your wishlist.')
    
    next_url = request.GET.get('next')
    if next_url:
        return redirect(next_url)
    
    return redirect('products:product_detail', slug=product_slug)


@login_required
def remove_from_wishlist_view(request, product_slug):
    """Remove from Wishlist View"""
    product = get_object_or_404(Product, slug=product_slug)
    
    Wishlist.objects.filter(user=request.user, product=product).delete()
    messages.success(request, f'{product.name} has been removed from your wishlist.')
    
    next_url = request.GET.get('next')
    if next_url:
        return redirect(next_url)
    
    return redirect('products:product_detail', slug=product_slug)


@login_required
def recently_viewed_view(request):
    """Recently Viewed Products View"""
    recently_viewed = RecentlyViewed.objects.filter(
        user=request.user
    ).select_related('product').order_by('-viewed_at')[:20]
    
    context = {
        'recently_viewed': recently_viewed,
    }
    
    return render(request, 'products/recently_viewed.html', context)


# AJAX Views
@require_POST
def check_availability(request):
    """Check product availability via AJAX"""
    product_id = request.POST.get('product_id')
    quantity = int(request.POST.get('quantity', 1))
    
    try:
        product = Product.objects.get(id=product_id, is_active=True)
        available = product.quantity >= quantity
        
        return JsonResponse({
            'available': available,
            'stock': product.quantity,
            'message': f'{product.quantity} items available' if available else 'Not enough stock'
        })
    except Product.DoesNotExist:
        return JsonResponse({
            'available': False,
            'message': 'Product not found'
        })


@require_POST
def get_product_price(request):
    """Get current product price via AJAX"""
    product_id = request.POST.get('product_id')
    
    try:
        product = Product.objects.get(id=product_id, is_active=True)
        
        # Check for flash sale
        flash_sale = FlashSale.objects.filter(
            product=product,
            is_active=True,
            starts_at__lte=timezone.now(),
            ends_at__gte=timezone.now()
        ).first()
        
        if flash_sale and flash_sale.is_live:
            price = flash_sale.sale_price
            original_price = product.price
            on_sale = True
        else:
            price = product.price
            original_price = product.compare_at_price
            on_sale = product.is_on_sale
        
        return JsonResponse({
            'success': True,
            'price': str(price),
            'original_price': str(original_price) if original_price else None,
            'on_sale': on_sale,
            'discount_percentage': product.discount_percentage if on_sale else 0
        })
    except Product.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Product not found'
        })
