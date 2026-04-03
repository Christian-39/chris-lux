/**
 * Gadgets Store - Theme Management
 * Handles dark/light mode switching
 */

document.addEventListener('DOMContentLoaded', function() {
    initTheme();
});

/**
 * Initialize theme based on user preference or system preference
 */
function initTheme() {
    const themeToggle = document.getElementById('themeToggle');
    const themeIcon = document.getElementById('themeIcon');
    const html = document.documentElement;
    
    // Get saved theme or default to system
    let currentTheme = localStorage.getItem('theme') || 'system';
    
    // Apply theme
    applyTheme(currentTheme);
    
    // Theme toggle click handler
    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            // Cycle through themes: light -> dark -> system -> light
            if (currentTheme === 'light') {
                currentTheme = 'dark';
            } else if (currentTheme === 'dark') {
                currentTheme = 'system';
            } else {
                currentTheme = 'light';
            }
            
            applyTheme(currentTheme);
            localStorage.setItem('theme', currentTheme);
            
            // Save to server if logged in
            saveThemePreference(currentTheme);
        });
    }
    
    // Listen for system theme changes
    if (window.matchMedia) {
        const darkModeQuery = window.matchMedia('(prefers-color-scheme: dark)');
        darkModeQuery.addEventListener('change', function(e) {
            if (currentTheme === 'system') {
                applyTheme('system');
            }
        });
    }
}

/**
 * Apply the selected theme
 */
function applyTheme(theme) {
    const html = document.documentElement;
    const themeIcon = document.getElementById('themeIcon');
    const body = document.body;
    
    let effectiveTheme = theme;
    
    // If system preference, check what the system prefers
    if (theme === 'system' && window.matchMedia) {
        effectiveTheme = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }
    
    // Apply theme
    html.setAttribute('data-theme', theme);
    
    // Update body class
    if (effectiveTheme === 'dark') {
        body.classList.add('dark-mode');
    } else {
        body.classList.remove('dark-mode');
    }
    
    // Update icon
    if (themeIcon) {
        if (theme === 'dark') {
            themeIcon.className = 'fas fa-moon';
        } else if (theme === 'light') {
            themeIcon.className = 'fas fa-sun';
        } else {
            themeIcon.className = 'fas fa-desktop';
        }
    }
    
    // Update meta theme-color
    const metaThemeColor = document.querySelector('meta[name="theme-color"]');
    if (metaThemeColor) {
        metaThemeColor.setAttribute('content', effectiveTheme === 'dark' ? '#1f2937' : '#2563eb');
    }
}

/**
 * Save theme preference to server
 */
function saveThemePreference(theme) {
    // Only save if user is logged in (check for CSRF token)
    const csrfToken = getCsrfToken();
    if (!csrfToken) return;
    
    fetch('/accounts/ajax/update-theme/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': csrfToken,
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: 'theme=' + encodeURIComponent(theme)
    })
    .then(response => response.json())
    .then(data => {
        if (!data.success) {
            console.error('Failed to save theme preference');
        }
    })
    .catch(error => {
        console.error('Error saving theme preference:', error);
    });
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

// Export for use in other scripts
window.ThemeManager = {
    applyTheme,
    saveThemePreference
};
