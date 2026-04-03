/**
 * Gadgets Store - Main JavaScript
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    initTooltips();
    
    // Initialize lazy loading
    initLazyLoading();
    
    // Initialize product card hover effects
    initProductCards();
    
    // Initialize mobile menu
    initMobileMenu();
    
    // Initialize search suggestions
    initSearchSuggestions();
    
    // Update cart and wishlist counts
    updateCounts();
});

/**
 * Initialize Bootstrap tooltips
 */
function initTooltips() {
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    tooltipTriggerList.forEach(function(tooltipTriggerEl) {
        new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * Initialize lazy loading for images
 */
function initLazyLoading() {
    if ('IntersectionObserver' in window) {
        const lazyImages = document.querySelectorAll('img[data-src]');
        
        const imageObserver = new IntersectionObserver(function(entries, observer) {
            entries.forEach(function(entry) {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src;
                    img.removeAttribute('data-src');
                    observer.unobserve(img);
                }
            });
        });
        
        lazyImages.forEach(function(img) {
            imageObserver.observe(img);
        });
    }
}

/**
 * Initialize product card interactions
 */
function initProductCards() {
    // Wishlist buttons
    document.querySelectorAll('.wishlist-btn').forEach(function(btn) {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const productId = this.dataset.productId;
            toggleWishlist(productId, this);
        });
    });
}

/**
 * Toggle wishlist item
 */
function toggleWishlist(productId, button) {
    const icon = button.querySelector('i');
    const isInWishlist = icon.classList.contains('fas');
    
    fetch(`/products/${productId}/${isInWishlist ? 'remove-from-wishlist' : 'add-to-wishlist'}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCsrfToken(),
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            if (isInWishlist) {
                icon.classList.remove('fas');
                icon.classList.add('far');
            } else {
                icon.classList.remove('far');
                icon.classList.add('fas');
            }
            updateWishlistCount();
            showToast(data.message, 'success');
        } else {
            showToast(data.message || 'Please login to add items to wishlist', 'info');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('An error occurred. Please try again.', 'error');
    });
}

/**
 * Initialize mobile menu
 */
function initMobileMenu() {
    const mobileMenuToggle = document.querySelector('.mobile-menu-toggle');
    if (mobileMenuToggle) {
        mobileMenuToggle.addEventListener('click', function() {
            document.body.classList.toggle('mobile-menu-open');
        });
    }
}

/**
 * Initialize search suggestions
 */
function initSearchSuggestions() {
    const searchInput = document.querySelector('.search-form input[name="q"]');
    if (searchInput) {
        let debounceTimer;
        
        searchInput.addEventListener('input', function() {
            clearTimeout(debounceTimer);
            debounceTimer = setTimeout(function() {
                // Could implement search suggestions here
            }, 300);
        });
    }
}

/**
 * Update cart and wishlist counts
 */
function updateCounts() {
    updateCartCount();
    updateWishlistCount();
    updateNotificationCount();
}

/**
 * Update cart count
 */
function updateCartCount() {
    fetch('/ajax/cart-count/')
        .then(response => response.json())
        .then(data => {
            const cartCounts = document.querySelectorAll('.cart-count, .cart-count-mobile');
            cartCounts.forEach(function(el) {
                if (data.count > 0) {
                    el.textContent = data.count;
                    el.hidden = false;
                } else {
                    el.hidden = true;
                }
            });
        })
        .catch(error => console.error('Error:', error));
}

/**
 * Update wishlist count
 */
function updateWishlistCount() {
    fetch('/ajax/wishlist-count/')
        .then(response => response.json())
        .then(data => {
            const wishlistCounts = document.querySelectorAll('.wishlist-count, .wishlist-count-mobile');
            wishlistCounts.forEach(function(el) {
                if (data.count > 0) {
                    el.textContent = data.count;
                    el.hidden = false;
                } else {
                    el.hidden = true;
                }
            });
        })
        .catch(error => console.error('Error:', error));
}

/**
 * Update notification count
 */
function updateNotificationCount() {
    fetch('/ajax/notification-count/')
        .then(response => response.json())
        .then(data => {
            const notificationCounts = document.querySelectorAll('.notification-count');
            notificationCounts.forEach(function(el) {
                if (data.count > 0) {
                    el.textContent = data.count;
                    el.hidden = false;
                } else {
                    el.hidden = true;
                }
            });
        })
        .catch(error => console.error('Error:', error));
}

/**
 * Get CSRF token from cookie
 */
function getCsrfToken() {
    const name = 'csrftoken';
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

/**
 * Show toast notification
 */
function showToast(message, type = 'info') {
    const toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) {
        const container = document.createElement('div');
        container.className = 'toast-container position-fixed top-0 end-0 p-3';
        container.style.zIndex = '9999';
        document.body.appendChild(container);
    }
    
    const toastId = 'toast-' + Date.now();
    const bgClass = type === 'success' ? 'bg-success' : type === 'error' ? 'bg-danger' : 'bg-info';
    
    const toastHTML = `
        <div id="${toastId}" class="toast align-items-center ${bgClass} text-white border-0" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        </div>
    `;
    
    document.querySelector('.toast-container').insertAdjacentHTML('beforeend', toastHTML);
    
    const toast = new bootstrap.Toast(document.getElementById(toastId), {
        delay: 5000
    });
    toast.show();
    
    // Remove from DOM after hiding
    document.getElementById(toastId).addEventListener('hidden.bs.toast', function() {
        this.remove();
    });
}

/**
 * Format price with currency
 */
function formatPrice(price, currency = '₦') {
    return currency + parseFloat(price).toLocaleString('en-NG', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}

/**
 * Debounce function
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Throttle function
 */
function throttle(func, limit) {
    let inThrottle;
    return function(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// Export functions for use in other scripts
window.GadgetsStore = {
    updateCartCount,
    updateWishlistCount,
    updateNotificationCount,
    showToast,
    formatPrice,
    getCsrfToken,
    debounce,
    throttle
};
