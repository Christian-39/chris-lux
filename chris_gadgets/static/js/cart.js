/**
 * Gadgets Store - Cart Management
 */

document.addEventListener('DOMContentLoaded', function() {
    initCart();
});

/**
 * Initialize cart functionality
 */
function initCart() {
    // Quantity inputs
    document.querySelectorAll('.cart-quantity-input').forEach(function(input) {
        input.addEventListener('change', function() {
            const itemId = this.dataset.itemId;
            const quantity = parseInt(this.value);
            updateCartItem(itemId, quantity);
        });
    });
    
    // Quantity buttons
    document.querySelectorAll('.cart-quantity-btn').forEach(function(btn) {
        btn.addEventListener('click', function() {
            const itemId = this.dataset.itemId;
            const action = this.dataset.action;
            const input = document.querySelector(`.cart-quantity-input[data-item-id="${itemId}"]`);
            let quantity = parseInt(input.value);
            
            if (action === 'increase') {
                quantity++;
            } else if (action === 'decrease' && quantity > 1) {
                quantity--;
            }
            
            input.value = quantity;
            updateCartItem(itemId, quantity);
        });
    });
    
    // Remove buttons
    document.querySelectorAll('.cart-remove-btn').forEach(function(btn) {
        btn.addEventListener('click', function() {
            const itemId = this.dataset.itemId;
            removeCartItem(itemId);
        });
    });
}

/**
 * Update cart item quantity
 */
function updateCartItem(itemId, quantity) {
    const csrfToken = getCsrfToken();
    
    fetch('/orders/ajax/update-quantity/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': csrfToken,
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: `item_id=${itemId}&quantity=${quantity}`
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Update item total
            const itemTotalEl = document.querySelector(`.cart-item-total[data-item-id="${itemId}"]`);
            if (itemTotalEl) {
                itemTotalEl.textContent = formatPrice(data.item_total);
            }
            
            // Update cart total
            const cartTotalEl = document.querySelector('.cart-total');
            if (cartTotalEl) {
                cartTotalEl.textContent = formatPrice(data.cart_total);
            }
            
            // Update cart count
            updateCartCountDisplay(data.cart_count);
            
            // If quantity is 0, remove the row
            if (quantity === 0) {
                const itemRow = document.querySelector(`.cart-item[data-item-id="${itemId}"]`);
                if (itemRow) {
                    itemRow.remove();
                }
            }
            
            showToast('Cart updated', 'success');
        } else {
            showToast(data.message || 'Failed to update cart', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('An error occurred. Please try again.', 'error');
    });
}

/**
 * Remove item from cart
 */
function removeCartItem(itemId) {
    if (!confirm('Are you sure you want to remove this item?')) {
        return;
    }
    
    const csrfToken = getCsrfToken();
    
    fetch('/orders/ajax/remove-item/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': csrfToken,
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: `item_id=${itemId}`
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Remove item row
            const itemRow = document.querySelector(`.cart-item[data-item-id="${itemId}"]`);
            if (itemRow) {
                itemRow.remove();
            }
            
            // Update cart total
            const cartTotalEl = document.querySelector('.cart-total');
            if (cartTotalEl) {
                cartTotalEl.textContent = formatPrice(data.cart_total);
            }
            
            // Update cart count
            updateCartCountDisplay(data.cart_count);
            
            // Check if cart is empty
            const cartItems = document.querySelectorAll('.cart-item');
            if (cartItems.length === 0) {
                location.reload(); // Reload to show empty cart message
            }
            
            showToast('Item removed from cart', 'success');
        } else {
            showToast(data.message || 'Failed to remove item', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('An error occurred. Please try again.', 'error');
    });
}

/**
 * Update cart count display
 */
function updateCartCountDisplay(count) {
    const cartCounts = document.querySelectorAll('.cart-count, .cart-count-mobile');
    cartCounts.forEach(function(el) {
        if (count > 0) {
            el.textContent = count;
            el.hidden = false;
        } else {
            el.hidden = true;
        }
    });
}

/**
 * Add item to cart (for product pages)
 */
function addToCart(productSlug, quantity = 1) {
    const csrfToken = getCsrfToken();
    
    fetch(`/orders/cart/add/${productSlug}/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': csrfToken,
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: `quantity=${quantity}`
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            updateCartCountDisplay(data.cart_count);
            showToast(data.message || 'Item added to cart', 'success');
        } else {
            showToast(data.message || 'Failed to add item', 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showToast('An error occurred. Please try again.', 'error');
    });
}

/**
 * Format price with currency
 */
function formatPrice(price) {
    return '₦' + parseFloat(price).toLocaleString('en-NG', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}

/**
 * Show toast notification
 */
function showToast(message, type = 'info') {
    // Use the showToast function from main.js if available
    if (window.GadgetsStore && window.GadgetsStore.showToast) {
        window.GadgetsStore.showToast(message, type);
        return;
    }
    
    // Fallback toast
    alert(message);
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
 * Update cart count from server
 */
function updateCartCount() {
    if (window.GadgetsStore && window.GadgetsStore.updateCartCount) {
        window.GadgetsStore.updateCartCount();
    }
}

// Export for use in other scripts
window.CartManager = {
    updateCartItem,
    removeCartItem,
    addToCart,
    updateCartCount
};
