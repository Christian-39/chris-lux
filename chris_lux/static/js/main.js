/**
 * Chris-Lux - Main JavaScript
 * Premium Hair E-Commerce
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all components
    initMobileMenu();
    initSearchSuggestions();
    initNotifications();
    initMessages();
    initScrollAnimations();
    initQuantityInputs();
    initImageGallery();
    initTabs();
    initAccordions();
});

/**
 * Mobile Menu Toggle
 */
function initMobileMenu() {
    const menuBtn = document.getElementById('mobile-menu-btn');
    const navMenu = document.getElementById('nav-menu');
    
    if (menuBtn && navMenu) {
        menuBtn.addEventListener('click', function() {
            navMenu.classList.toggle('active');
            const icon = this.querySelector('i');
            if (navMenu.classList.contains('active')) {
                icon.classList.remove('fa-bars');
                icon.classList.add('fa-times');
            } else {
                icon.classList.remove('fa-times');
                icon.classList.add('fa-bars');
            }
        });
    }
}

/**
 * Search Suggestions
 */
function initSearchSuggestions() {
    const searchInput = document.getElementById('search-input');
    const suggestionsContainer = document.getElementById('search-suggestions');
    
    if (!searchInput || !suggestionsContainer) return;
    
    let debounceTimer;
    
    searchInput.addEventListener('input', function() {
        clearTimeout(debounceTimer);
        const query = this.value.trim();
        
        if (query.length < 2) {
            suggestionsContainer.innerHTML = '';
            suggestionsContainer.classList.remove('active');
            return;
        }
        
        debounceTimer = setTimeout(() => {
            fetch(`/products/search/suggestions/?q=${encodeURIComponent(query)}`)
                .then(response => response.text())
                .then(html => {
                    suggestionsContainer.innerHTML = html;
                    suggestionsContainer.classList.add('active');
                })
                .catch(error => console.error('Search error:', error));
        }, 300);
    });
    
    // Close suggestions on click outside
    document.addEventListener('click', function(e) {
        if (!searchInput.contains(e.target) && !suggestionsContainer.contains(e.target)) {
            suggestionsContainer.classList.remove('active');
        }
    });
}

/**
 * Notifications
 */
function initNotifications() {
    const notificationBtn = document.getElementById('notification-btn');
    const notificationMenu = document.getElementById('notification-menu');
    
    if (!notificationBtn || !notificationMenu) return;
    
    // Toggle notification menu
    notificationBtn.addEventListener('click', function(e) {
        e.stopPropagation();
        notificationMenu.classList.toggle('active');
    });
    
    // Close on click outside
    document.addEventListener('click', function(e) {
        if (!notificationBtn.contains(e.target) && !notificationMenu.contains(e.target)) {
            notificationMenu.classList.remove('active');
        }
    });
    
    // Fetch notifications periodically
    fetchNotifications();
    setInterval(fetchNotifications, 30000); // Every 30 seconds
}

function fetchNotifications() {
    fetch('/notifications/ajax/', {
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        updateNotificationBadge(data.unread_count);
    })
    .catch(error => console.error('Notification fetch error:', error));
}

function updateNotificationBadge(count) {
    const badge = document.querySelector('.notification-btn .badge');
    if (badge) {
        if (count > 0) {
            badge.textContent = count > 99 ? '99+' : count;
            badge.style.display = 'flex';
        } else {
            badge.style.display = 'none';
        }
    }
}

/**
 * Auto-dismiss Messages
 */
function initMessages() {
    const messages = document.querySelectorAll('.message');
    
    messages.forEach(message => {
        setTimeout(() => {
            message.style.opacity = '0';
            message.style.transform = 'translateX(100%)';
            setTimeout(() => message.remove(), 300);
        }, 5000);
    });
}

/**
 * Scroll Animations
 */
function initScrollAnimations() {
    const animatedElements = document.querySelectorAll('[data-animate]');
    
    if (animatedElements.length === 0) return;
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const animation = entry.target.dataset.animate;
                entry.target.classList.add(`animate-${animation}`);
                observer.unobserve(entry.target);
            }
        });
    }, {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    });
    
    animatedElements.forEach(el => observer.observe(el));
}

/**
 * Quantity Input Controls
 */
function initQuantityInputs() {
    const quantityWrappers = document.querySelectorAll('.quantity-wrapper');
    
    quantityWrappers.forEach(wrapper => {
        const input = wrapper.querySelector('.quantity-input');
        const decreaseBtn = wrapper.querySelector('.quantity-decrease');
        const increaseBtn = wrapper.querySelector('.quantity-increase');
        
        if (!input) return;
        
        const min = parseInt(input.dataset.min) || 1;
        const max = parseInt(input.dataset.max) || 999;
        
        if (decreaseBtn) {
            decreaseBtn.addEventListener('click', () => {
                let value = parseInt(input.value) || min;
                if (value > min) {
                    input.value = value - 1;
                    input.dispatchEvent(new Event('change'));
                }
            });
        }
        
        if (increaseBtn) {
            increaseBtn.addEventListener('click', () => {
                let value = parseInt(input.value) || min;
                if (value < max) {
                    input.value = value + 1;
                    input.dispatchEvent(new Event('change'));
                }
            });
        }
        
        input.addEventListener('change', () => {
            let value = parseInt(input.value) || min;
            value = Math.max(min, Math.min(max, value));
            input.value = value;
        });
    });
}

/**
 * Image Gallery (Product Detail)
 */
function initImageGallery() {
    const gallery = document.querySelector('.product-gallery');
    if (!gallery) return;
    
    const mainImage = gallery.querySelector('.gallery-main-image');
    const thumbnails = gallery.querySelectorAll('.gallery-thumbnail');
    
    thumbnails.forEach(thumb => {
        thumb.addEventListener('click', function() {
            const imageUrl = this.dataset.image;
            if (mainImage && imageUrl) {
                mainImage.src = imageUrl;
                thumbnails.forEach(t => t.classList.remove('active'));
                this.classList.add('active');
            }
        });
    });
    
    // Video thumbnail click
    const videoThumbnails = gallery.querySelectorAll('.gallery-video-thumb');
    const videoContainer = gallery.querySelector('.gallery-video-container');
    
    videoThumbnails.forEach(thumb => {
        thumb.addEventListener('click', function() {
            const videoUrl = this.dataset.video;
            if (videoContainer && videoUrl) {
                videoContainer.innerHTML = `<video controls autoplay><source src="${videoUrl}" type="video/mp4"></video>`;
                videoContainer.style.display = 'block';
                if (mainImage) mainImage.style.display = 'none';
            }
        });
    });
}

/**
 * Tabs
 */
function initTabs() {
    const tabGroups = document.querySelectorAll('[data-tabs]');
    
    tabGroups.forEach(group => {
        const tabs = group.querySelectorAll('[data-tab]');
        const panels = group.querySelectorAll('[data-tab-panel]');
        
        tabs.forEach(tab => {
            tab.addEventListener('click', function() {
                const targetPanel = this.dataset.tab;
                
                // Update active tab
                tabs.forEach(t => t.classList.remove('active'));
                this.classList.add('active');
                
                // Show target panel
                panels.forEach(panel => {
                    panel.classList.remove('active');
                    if (panel.dataset.tabPanel === targetPanel) {
                        panel.classList.add('active');
                    }
                });
            });
        });
    });
}

/**
 * Accordions
 */
function initAccordions() {
    const accordions = document.querySelectorAll('.accordion');
    
    accordions.forEach(accordion => {
        const headers = accordion.querySelectorAll('.accordion-header');
        
        headers.forEach(header => {
            header.addEventListener('click', function() {
                const item = this.parentElement;
                const isActive = item.classList.contains('active');
                
                // Close all items
                accordion.querySelectorAll('.accordion-item').forEach(i => {
                    i.classList.remove('active');
                });
                
                // Open clicked item if it wasn't active
                if (!isActive) {
                    item.classList.add('active');
                }
            });
        });
    });
}

/**
 * Copy to Clipboard
 */
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showToast('Copied to clipboard!');
    }).catch(err => {
        console.error('Failed to copy:', err);
    });
}

/**
 * Toast Notification
 */
function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : 'info-circle'}"></i>
        <span>${message}</span>
    `;
    
    document.body.appendChild(toast);
    
    // Animate in
    setTimeout(() => toast.classList.add('show'), 10);
    
    // Remove after delay
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

/**
 * Confirm Action
 */
function confirmAction(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

/**
 * Format Currency
 */
function formatCurrency(amount, symbol = '$') {
    return `${symbol}${parseFloat(amount).toFixed(2)}`;
}

/**
 * Debounce Function
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
 * Throttle Function
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

/**
 * Lazy Load Images
 */
function initLazyLoad() {
    const lazyImages = document.querySelectorAll('img[data-src]');
    
    const imageObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.removeAttribute('data-src');
                imageObserver.unobserve(img);
            }
        });
    });
    
    lazyImages.forEach(img => imageObserver.observe(img));
}

// Initialize lazy load
initLazyLoad();

/**
 * Smooth Scroll to Element
 */
function scrollToElement(selector, offset = 80) {
    const element = document.querySelector(selector);
    if (element) {
        const top = element.getBoundingClientRect().top + window.pageYOffset - offset;
        window.scrollTo({ top, behavior: 'smooth' });
    }
}

/**
 * AJAX Form Submit
 */
function submitFormAjax(form, successCallback, errorCallback) {
    const formData = new FormData(form);
    const url = form.action;
    const method = form.method || 'POST';
    
    fetch(url, {
        method: method,
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (successCallback) successCallback(data);
    })
    .catch(error => {
        if (errorCallback) errorCallback(error);
    });
}

/**
 * Dark Mode Toggle
 */
function initDarkMode() {
    const darkModeToggle = document.getElementById('dark-mode-toggle');
    if (!darkModeToggle) return;
    
    darkModeToggle.addEventListener('change', function() {
        const isDark = this.checked;
        document.documentElement.setAttribute('data-theme', isDark ? 'dark' : 'light');
        
        // Save preference
        fetch('/users/preferences/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': getCsrfToken()
            },
            body: `dark_mode=${isDark}`
        });
    });
}

/**
 * Get CSRF Token
 */
function getCsrfToken() {
    const token = document.querySelector('[name=csrfmiddlewaretoken]');
    return token ? token.value : '';
}

// Initialize dark mode
initDarkMode();
