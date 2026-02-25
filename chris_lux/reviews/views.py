"""
Reviews views for Chris Lux.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from chris_lux.products.models import Product
from chris_lux.orders.models import Order
from .models import Review, ReviewImage, ReviewHelpful
from .forms import ReviewForm


@login_required
def add_review(request, product_slug):
    """Add a review for a product."""
    product = get_object_or_404(Product, slug=product_slug, is_active=True)
    
    # Check if user already reviewed this product
    existing_review = Review.objects.filter(product=product, user=request.user).first()
    if existing_review:
        messages.error(request, 'You have already reviewed this product.')
        return redirect('product_detail', slug=product_slug)
    
    # Check if user has purchased this product
    has_purchased = Order.objects.filter(
        user=request.user,
        items__product=product,
        payment_status='paid'
    ).exists()
    
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.product = product
            review.user = request.user
            review.is_verified_purchase = has_purchased
            review.save()
            
            # Handle review images
            images = request.FILES.getlist('images')
            for image in images[:5]:  # Max 5 images
                ReviewImage.objects.create(review=review, image=image)
            
            messages.success(request, 'Thank you for your review! It will be published after approval.')
            return redirect('product_detail', slug=product_slug)
    else:
        form = ReviewForm()
    
    return render(request, 'reviews/add_review.html', {
        'form': form,
        'product': product,
        'has_purchased': has_purchased
    })


@login_required
def edit_review(request, review_id):
    """Edit a review."""
    review = get_object_or_404(Review, id=review_id, user=request.user)
    
    if request.method == 'POST':
        form = ReviewForm(request.POST, instance=review)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your review has been updated.')
            return redirect('product_detail', slug=review.product.slug)
    else:
        form = ReviewForm(instance=review)
    
    return render(request, 'reviews/edit_review.html', {
        'form': form,
        'review': review
    })


@login_required
def delete_review(request, review_id):
    """Delete a review."""
    review = get_object_or_404(Review, id=review_id, user=request.user)
    product_slug = review.product.slug
    review.delete()
    messages.success(request, 'Your review has been deleted.')
    return redirect('product_detail', slug=product_slug)


@require_POST
def mark_helpful(request):
    """Mark a review as helpful via AJAX."""
    if not request.user.is_authenticated:
        return JsonResponse({
            'success': False,
            'message': 'Please login to mark reviews as helpful.',
            'login_required': True
        })
    
    review_id = request.POST.get('review_id')
    if not review_id:
        return JsonResponse({'success': False, 'message': 'Review ID is required.'})
    
    try:
        review = Review.objects.get(id=review_id, is_approved=True)
    except Review.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Review not found.'})
    
    helpful_vote, created = ReviewHelpful.objects.get_or_create(
        review=review,
        user=request.user
    )
    
    if not created:
        helpful_vote.delete()
        review.helpful_count -= 1
        review.save()
        return JsonResponse({
            'success': True,
            'action': 'removed',
            'helpful_count': review.helpful_count
        })
    
    review.helpful_count += 1
    review.save()
    return JsonResponse({
        'success': True,
        'action': 'added',
        'helpful_count': review.helpful_count
    })
