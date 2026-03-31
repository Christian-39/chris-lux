"""
Views for products app.
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView
from django.db.models import Q, Avg
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator

from .models import Product, Category, ProductReview, Wishlist


class ProductListView(ListView):
    """Display list of products with filtering."""
    
    model = Product
    template_name = 'products/product_list.html'
    context_object_name = 'products'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = Product.objects.filter(is_active=True).prefetch_related('images')
        
        # Filter by category
        category_slug = self.request.GET.get('category')
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        
        # Filter by product type
        product_type = self.request.GET.get('type')
        if product_type:
            queryset = queryset.filter(product_type=product_type)
        
        # Filter by hair texture
        texture = self.request.GET.get('texture')
        if texture:
            queryset = queryset.filter(hair_texture=texture)
        
        # Filter by hair origin
        origin = self.request.GET.get('origin')
        if origin:
            queryset = queryset.filter(hair_origin=origin)
        
        # Filter by length
        min_length = self.request.GET.get('min_length')
        max_length = self.request.GET.get('max_length')
        if min_length:
            queryset = queryset.filter(length__gte=min_length)
        if max_length:
            queryset = queryset.filter(length__lte=max_length)
        
        # Filter by price
        min_price = self.request.GET.get('min_price')
        max_price = self.request.GET.get('max_price')
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        
        # Search
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search) |
                Q(short_description__icontains=search) |
                Q(meta_keywords__icontains=search)
            )
        
        # Sorting
        sort = self.request.GET.get('sort', '-created_at')
        if sort == 'price_low':
            queryset = queryset.order_by('price')
        elif sort == 'price_high':
            queryset = queryset.order_by('-price')
        elif sort == 'name_asc':
            queryset = queryset.order_by('name')
        elif sort == 'name_desc':
            queryset = queryset.order_by('-name')
        elif sort == 'popular':
            queryset = queryset.order_by('-is_bestseller', '-created_at')
        else:
            queryset = queryset.order_by('-created_at')
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.filter(is_active=True)
        context['product_types'] = Product.PRODUCT_TYPES
        context['hair_textures'] = Product.HAIR_TEXTURES
        context['hair_origins'] = Product.HAIR_ORIGINS
        context['lengths'] = Product.LENGTHS
        
        # Preserve filter params for pagination
        query_params = self.request.GET.copy()
        if 'page' in query_params:
            del query_params['page']
        context['query_params'] = query_params.urlencode()
        
        return context


class ProductDetailView(DetailView):
    """Display product details."""
    
    model = Product
    template_name = 'products/product_detail.html'
    context_object_name = 'product'
    slug_url_kwarg = 'slug'
    
    def get_queryset(self):
        return Product.objects.filter(is_active=True).prefetch_related(
            'images', 'videos', 'reviews__user'
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.get_object()
        
        # Related products
        context['related_products'] = product.get_related_products()
        
        # Reviews
        context['reviews'] = product.reviews.filter(is_approved=True)
        context['review_count'] = product.reviews.filter(is_approved=True).count()
        
        # Average rating
        avg_rating = product.reviews.filter(is_approved=True).aggregate(
            avg=Avg('rating')
        )['avg']
        context['average_rating'] = avg_rating or 0
        
        # Check if user has wishlisted this product
        if self.request.user.is_authenticated:
            context['in_wishlist'] = Wishlist.objects.filter(
                user=self.request.user,
                product=product
            ).exists()
        
        # Check if user can review
        if self.request.user.is_authenticated:
            from orders.models import OrderItem
            context['can_review'] = OrderItem.objects.filter(
                order__user=self.request.user,
                product=product,
                order__status='delivered'
            ).exists()
        
        return context


class CategoryListView(ListView):
    """Display products by category."""
    
    model = Product
    template_name = 'products/category_detail.html'
    context_object_name = 'products'
    paginate_by = 12
    
    def get_queryset(self):
        self.category = get_object_or_404(Category, slug=self.kwargs['slug'])
        return Product.objects.filter(
            category=self.category,
            is_active=True
        ).prefetch_related('images')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        context['categories'] = Category.objects.filter(is_active=True)
        return context


def search_suggestions(request):
    """AJAX endpoint for search suggestions."""
    query = request.GET.get('q', '')
    suggestions = []
    
    if query and len(query) >= 2:
        products = Product.objects.filter(
            Q(name__icontains=query) |
            Q(short_description__icontains=query),
            is_active=True
        )[:5]
        
        for product in products:
            suggestions.append({
                'id': product.id,
                'name': product.name,
                'slug': product.slug,
                'price': str(product.price),
                'image': product.primary_image.image.url if product.primary_image else None,
            })
    
    return render(request, 'products/search_suggestions.html', {
        'suggestions': suggestions
    })


@login_required
def add_review(request, slug):
    """Add a product review."""
    product = get_object_or_404(Product, slug=slug)
    
    if request.method == 'POST':
        rating = request.POST.get('rating')
        title = request.POST.get('title', '')
        comment = request.POST.get('comment', '')
        
        if rating and comment:
            # Check if user already reviewed
            existing_review = ProductReview.objects.filter(
                product=product,
                user=request.user
            ).first()
            
            if existing_review:
                existing_review.rating = rating
                existing_review.title = title
                existing_review.comment = comment
                existing_review.save()
                messages.success(request, 'Your review has been updated!')
            else:
                ProductReview.objects.create(
                    product=product,
                    user=request.user,
                    rating=rating,
                    title=title,
                    comment=comment
                )
                messages.success(request, 'Thank you for your review!')
        else:
            messages.error(request, 'Please provide both rating and comment.')
    
    return redirect('products:product_detail', slug=slug)


@login_required
def toggle_wishlist(request, slug):
    """Toggle product in wishlist."""
    product = get_object_or_404(Product, slug=slug)
    
    wishlist_item = Wishlist.objects.filter(
        user=request.user,
        product=product
    ).first()
    
    if wishlist_item:
        wishlist_item.delete()
        messages.success(request, f'{product.name} removed from wishlist.')
    else:
        Wishlist.objects.create(user=request.user, product=product)
        messages.success(request, f'{product.name} added to wishlist.')
    
    return redirect('products:product_detail', slug=slug)


@login_required
def wishlist_view(request):
    """Display user's wishlist."""
    wishlist_items = Wishlist.objects.filter(
        user=request.user
    ).select_related('product').prefetch_related('product__images')
    
    return render(request, 'products/wishlist.html', {
        'wishlist_items': wishlist_items
    })


def featured_products(request):
    """Display featured products."""
    products = Product.objects.filter(
        is_featured=True,
        is_active=True
    ).prefetch_related('images')[:8]
    
    return render(request, 'products/featured.html', {
        'products': products
    })


def new_arrivals(request):
    """Display new arrival products."""
    products = Product.objects.filter(
        is_new_arrival=True,
        is_active=True
    ).prefetch_related('images')[:8]
    
    return render(request, 'products/new_arrivals.html', {
        'products': products
    })


def bestsellers(request):
    """Display bestseller products."""
    products = Product.objects.filter(
        is_bestseller=True,
        is_active=True
    ).prefetch_related('images')[:8]
    
    return render(request, 'products/bestsellers.html', {
        'products': products
    })
