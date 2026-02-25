"""
Products views for Chris Lux.
"""

from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView
from django.db.models import Q, Min, Max
from django.core.paginator import Paginator
from django.http import JsonResponse

from .models import Category, Product, Variation


class ShopView(ListView):
    """Shop page with product listing and filtering."""
    model = Product
    template_name = 'products/shop.html'
    context_object_name = 'products'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = Product.objects.filter(is_active=True).prefetch_related('images', 'variations')
        
        # Search
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(tags__icontains=search_query) |
                Q(category__name__icontains=search_query)
            )
        
        # Category filter
        category_slug = self.request.GET.get('category')
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        
        # Price filter
        min_price = self.request.GET.get('min_price')
        max_price = self.request.GET.get('max_price')
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        
        # Variation filters
        length = self.request.GET.get('length')
        texture = self.request.GET.get('texture')
        if length:
            queryset = queryset.filter(variations__variation_type='length', variations__value=length)
        if texture:
            queryset = queryset.filter(variations__variation_type='texture', variations__value=texture)
        
        # Sorting
        sort_by = self.request.GET.get('sort', 'newest')
        if sort_by == 'price_low':
            queryset = queryset.order_by('price')
        elif sort_by == 'price_high':
            queryset = queryset.order_by('-price')
        elif sort_by == 'name_asc':
            queryset = queryset.order_by('name')
        elif sort_by == 'name_desc':
            queryset = queryset.order_by('-name')
        elif sort_by == 'popular':
            queryset = queryset.order_by('-is_best_seller', '-created_at')
        else:  # newest
            queryset = queryset.order_by('-is_new', '-created_at')
        
        return queryset.distinct()
    
    def render_to_response(self, context, **response_kwargs):
        # Check if this is an AJAX request for search
        if self.request.GET.get('ajax') == '1' or self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            products = self.get_queryset()[:8]  # Limit to 8 results for quick search
            data = {
                'products': [
                    {
                        'id': p.id,
                        'name': p.name,
                        'price': str(p.display_price),
                        'url': p.get_absolute_url(),
                        'image': p.primary_image.image.url if p.primary_image else None
                    }
                    for p in products
                ],
                'count': len(products)
            }
            return JsonResponse(data)
        return super().render_to_response(context, **response_kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Categories for filter
        context['categories'] = Category.objects.filter(is_active=True)
        
        # Price range
        price_stats = Product.objects.filter(is_active=True).aggregate(
            min_price=Min('price'),
            max_price=Max('price')
        )
        context['min_price'] = price_stats['min_price'] or 0
        context['max_price'] = price_stats['max_price'] or 100000
        
        # Variation options
        context['length_options'] = Variation.objects.filter(
            variation_type='length',
            is_active=True
        ).values_list('value', flat=True).distinct()
        
        context['texture_options'] = Variation.objects.filter(
            variation_type='texture',
            is_active=True
        ).values_list('value', flat=True).distinct()
        
        # Current filters
        context['current_category'] = self.request.GET.get('category')
        context['current_sort'] = self.request.GET.get('sort', 'newest')
        context['search_query'] = self.request.GET.get('q', '')
        
        # Product count
        context['product_count'] = self.get_queryset().count()
        
        return context


class CategoryDetailView(DetailView):
    """Category detail page."""
    model = Category
    template_name = 'products/category.html'
    context_object_name = 'category'
    slug_url_kwarg = 'slug'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get products in this category
        products = Product.objects.filter(
            category=self.object,
            is_active=True
        ).prefetch_related('images', 'variations')
        
        # Pagination
        paginator = Paginator(products, 12)
        page = self.request.GET.get('page')
        context['products'] = paginator.get_page(page)
        
        # Subcategories
        context['subcategories'] = self.object.children.filter(is_active=True)
        
        return context


class ProductDetailView(DetailView):
    """Product detail page."""
    model = Product
    template_name = 'products/product_detail.html'
    context_object_name = 'product'
    slug_url_kwarg = 'slug'
    
    def get_queryset(self):
        return Product.objects.filter(is_active=True).prefetch_related(
            'images', 'variations', 'reviews__user'
        )
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Related products
        context['related_products'] = Product.objects.filter(
            category=self.object.category,
            is_active=True
        ).exclude(id=self.object.id)[:4]
        
        # Variations grouped by type
        variations = {}
        for variation in self.object.variations.filter(is_active=True):
            if variation.variation_type not in variations:
                variations[variation.variation_type] = []
            variations[variation.variation_type].append(variation)
        context['variations'] = variations
        
        # Reviews
        context['reviews'] = self.object.reviews.filter(is_approved=True)
        
        # Check if in wishlist
        if self.request.user.is_authenticated:
            context['in_wishlist'] = self.request.user.wishlist.filter(
                product=self.object
            ).exists()
        
        return context


def get_variation_price(request):
    """AJAX endpoint to get variation price."""
    product_id = request.GET.get('product_id')
    variation_id = request.GET.get('variation_id')
    
    if not product_id or not variation_id:
        return JsonResponse({'error': 'Missing parameters'}, status=400)
    
    try:
        product = Product.objects.get(id=product_id)
        variation = Variation.objects.get(id=variation_id, product=product)
        
        return JsonResponse({
            'price': float(variation.final_price),
            'stock': variation.stock_quantity,
            'in_stock': variation.stock_quantity > 0
        })
    except (Product.DoesNotExist, Variation.DoesNotExist):
        return JsonResponse({'error': 'Product or variation not found'}, status=404)
