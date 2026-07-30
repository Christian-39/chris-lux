/**
 * OYA Theme Manager - Dark Mode / Light Mode / System
 */
/**
 * OYA Theme Manager - Dark Mode / Light Mode / System
 */
(function() {
  'use strict';

  const STORAGE_KEY = 'oya_theme';

  // Get Saved Choice ('light', 'dark', or 'system')
  function getTheme() {
    return localStorage.getItem(STORAGE_KEY) || 'system';
  }

  // Resolve active theme based on system preference if needed
  function resolveTheme(theme) {
    if (theme === 'system' || theme === 'auto') {
      return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }
    return theme;
  }

  // Apply Theme to Document Element
  function applyTheme(theme) {
    const applied = resolveTheme(theme);
    document.documentElement.setAttribute('data-theme', applied);
  }

  // Set Theme and Persist
  function setTheme(theme) {
    localStorage.setItem(STORAGE_KEY, theme);
    applyTheme(theme);
    updateThemeUI(theme);

    window.dispatchEvent(new CustomEvent('oyathemechange', {
      detail: { theme: theme, applied: resolveTheme(theme) }
    }));
  }

  // Sync Dropdown Options & Toggle Buttons
  function updateThemeUI(theme) {
    const currentTheme = theme || getTheme();
    const applied = resolveTheme(currentTheme);

    // Update active state on option buttons
    document.querySelectorAll('[data-theme-option]').forEach(el => {
      const isActive = el.dataset.themeOption === currentTheme;
      el.classList.toggle('active', isActive);

      const checkIcon = el.querySelector('.dropdown-check');
      if (checkIcon) {
        checkIcon.style.opacity = isActive ? '1' : '0';
      }
    });

    // Update Desktop Toggle Icon
    const desktopBtn = document.getElementById('themeMenuToggle');
    if (desktopBtn) {
      desktopBtn.setAttribute('data-active-theme', currentTheme);
      desktopBtn.querySelectorAll('.theme-icon-light, .theme-icon-dark, .theme-icon-system').forEach(icon => {
        icon.style.display = 'none';
      });
      const activeIcon = desktopBtn.querySelector('.theme-icon-' + currentTheme);
      if (activeIcon) activeIcon.style.display = 'inline-block';
    }

    // Update Mobile Toggle Icon
    const mobileBtn = document.getElementById('mobileThemeBtn');
    if (mobileBtn) {
      mobileBtn.setAttribute('data-active-theme', currentTheme);
      mobileBtn.querySelectorAll('.theme-icon-light, .theme-icon-dark, .theme-icon-system').forEach(icon => {
        icon.style.display = 'none';
      });
      const activeMobileIcon = mobileBtn.querySelector('.theme-icon-' + currentTheme);
      if (activeMobileIcon) activeMobileIcon.style.display = 'inline-block';
    }
  }

  // Initialize Theme System
  function initTheme() {
    const activeTheme = getTheme();
    applyTheme(activeTheme);
    updateThemeUI(activeTheme);

    // Theme Option Click Handlers
    document.querySelectorAll('[data-theme-option]').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.preventDefault();
        setTheme(btn.dataset.themeOption);
      });
    });

    // Handle OS Theme Preference Changes
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
      if (getTheme() === 'system') {
        applyTheme('system');
        updateThemeUI('system');
      }
    });
  }

  // Rest of utility components (Sidebar, Dropdowns, Tabs, Toasts, Modals)...
  function initSidebar() { ... }
  function initDropdowns() { ... }
  function initMobileNav() { ... }
  function initTabs() { ... }

  function init() {
    initTheme();
    initSidebar();
    initDropdowns();
    initMobileNav();
    initTabs();

    // Expose global API securely
    window.OYA = window.OYA || {};
    window.OYA.setTheme = setTheme;
    window.OYA.getTheme = getTheme;
    window.OYA.resolveTheme = resolveTheme;
    window.OYA.theme = {
      set: setTheme,
      getStored: getTheme,
      resolve: resolveTheme
    };
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();