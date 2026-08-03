/**
 * OYA Autocomplete Component
 * Single, reusable searchable-select used everywhere a form needs to pick
 * a Member or a User: yearly dues, project/general donations, pledges,
 * donation-group assignment, outside-donor referrals, etc.
 *
 * Server-side search only — never preloads the full member list.
 * Backed by members:member_autocomplete_search / accounts:user_search_ajax,
 * both returning: {results: [{id, full_name, serial_number, phone, role, photo_url}]}
 *
 * Markup contract (see templates/widgets/autocomplete_select.html):
 *   [data-autocomplete-wrapper]
 *     input[data-autocomplete-input][data-search-url][data-min-chars]
 *     input[data-autocomplete-value]   (hidden - the real field value)
 *     [data-autocomplete-clear]        (optional)
 *     [data-autocomplete-results]
 */
(function () {
  'use strict';

  function debounce(fn, delay) {
    let t;
    return function (...args) {
      clearTimeout(t);
      t = setTimeout(() => fn.apply(this, args), delay);
    };
  }

  function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text == null ? '' : String(text);
    return div.innerHTML;
  }

  class MemberAutocomplete {
    constructor(wrapper) {
      this.wrapper = wrapper;
      this.input = wrapper.querySelector('[data-autocomplete-input]');
      this.hidden = wrapper.querySelector('[data-autocomplete-value]');
      this.resultsBox = wrapper.querySelector('[data-autocomplete-results]');
      this.clearBtn = wrapper.querySelector('[data-autocomplete-clear]');
      if (!this.input || !this.hidden || !this.resultsBox) return;

      this.searchUrl = this.input.dataset.searchUrl;
      this.minChars = parseInt(this.input.dataset.minChars || '1', 10);
      this.items = [];
      this.activeIndex = -1;
      this.abortController = null;

      this.init();
    }

    init() {
      this.input.addEventListener('input', debounce(() => this.onType(), 250));
      this.input.addEventListener('keydown', (e) => this.onKeydown(e));
      this.input.addEventListener('focus', () => {
        if (this.items.length) this.showResults();
      });
      document.addEventListener('click', (e) => {
        if (!this.wrapper.contains(e.target)) this.hideResults();
      });
      if (this.clearBtn) {
        this.clearBtn.addEventListener('click', () => this.clear());
      }
      // If the field was pre-filled (edit form), typing again should
      // invalidate the stale selection until a new one is confirmed.
      this.input.addEventListener('input', () => {
        if (!this.input.value) this.hidden.value = '';
      });
    }

    onType() {
      const q = this.input.value.trim();
      this.hidden.value = '';
      if (q.length < this.minChars) {
        this.hideResults();
        return;
      }
      this.search(q);
    }

    search(q) {
      if (this.abortController) this.abortController.abort();
      this.abortController = new AbortController();

      if (!this.searchUrl) {
        // The widget couldn't resolve its search endpoint (e.g. a bad
        // search_url_name on the server side) — this is a configuration
        // problem, not a transient network issue, so say so distinctly
        // rather than the generic message.
        console.error('OYA Autocomplete: no search URL configured for this field.', this.input);
        this.resultsBox.innerHTML = '<div class="autocomplete-item autocomplete-empty">Search is not configured for this field.</div>';
        this.showResults();
        return;
      }

      this.resultsBox.innerHTML = '<div class="autocomplete-item autocomplete-loading">Searching…</div>';
      this.showResults();

      fetch(`${this.searchUrl}?q=${encodeURIComponent(q)}`, {
        signal: this.abortController.signal,
        headers: { 'X-Requested-With': 'XMLHttpRequest' },
        redirect: 'manual'
      })
        .then((r) => {
          // redirect: 'manual' makes a redirected response come back as
          // an opaque type 'opaqueredirect' instead of silently following
          // it to (usually) the login page's HTML — that's what was
          // previously causing "Search unavailable": the fetch succeeded
          // with a 200, but the body was a login page, not JSON.
          if (r.type === 'opaqueredirect') {
            const err = new Error('redirected');
            err.isRedirect = true;
            throw err;
          }
          if (!r.ok) {
            const err = new Error(`HTTP ${r.status}`);
            err.status = r.status;
            throw err;
          }
          const contentType = r.headers.get('content-type') || '';
          if (!contentType.includes('application/json')) {
            const err = new Error('non-JSON response');
            err.notJson = true;
            throw err;
          }
          return r.json();
        })
        .then((data) => {
          this.items = Array.isArray(data.results) ? data.results : [];
          this.render(q);
        })
        .catch((err) => {
          if (err.name === 'AbortError') return;
          console.error('OYA Autocomplete search failed:', err);
          let message = 'Search unavailable. Try again.';
          if (err.isRedirect || err.status === 401 || err.status === 403) {
            message = 'Your session has expired. Please refresh the page and log in again.';
          } else if (err.status >= 500) {
            message = 'Search is temporarily unavailable. Please try again shortly.';
          }
          this.resultsBox.innerHTML = `<div class="autocomplete-item autocomplete-empty">${message}</div>`;
          this.showResults();
        });
    }

    render(q) {
      this.activeIndex = -1;
      if (!this.items.length) {
        this.resultsBox.innerHTML = `<div class="autocomplete-item autocomplete-empty">No matches for "${escapeHtml(q)}"</div>`;
        this.showResults();
        return;
      }
      this.resultsBox.innerHTML = '';
      this.items.forEach((item, idx) => {
        const el = document.createElement('div');
        el.className = 'autocomplete-item';
        el.setAttribute('role', 'option');
        el.dataset.index = idx;
        const subtitleParts = [item.serial_number, item.phone].filter(Boolean);
        el.innerHTML = `
          <span class="autocomplete-item-name">${escapeHtml(item.full_name)}</span>
          <span class="autocomplete-item-sub">${escapeHtml(subtitleParts.join(' · '))}</span>
        `;
        el.addEventListener('mousedown', (e) => {
          e.preventDefault();
          this.select(item);
        });
        this.resultsBox.appendChild(el);
      });
      this.showResults();
    }

    onKeydown(e) {
      if (this.resultsBox.classList.contains('hidden')) return;
      const rows = this.resultsBox.querySelectorAll('.autocomplete-item[data-index]');
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        this.activeIndex = Math.min(this.activeIndex + 1, rows.length - 1);
        this.highlight(rows);
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        this.activeIndex = Math.max(this.activeIndex - 1, 0);
        this.highlight(rows);
      } else if (e.key === 'Enter') {
        if (this.activeIndex >= 0 && this.items[this.activeIndex]) {
          e.preventDefault();
          this.select(this.items[this.activeIndex]);
        }
      } else if (e.key === 'Escape') {
        this.hideResults();
      }
    }

    highlight(rows) {
      rows.forEach((r, i) => r.classList.toggle('active', i === this.activeIndex));
      const active = rows[this.activeIndex];
      if (active) active.scrollIntoView({ block: 'nearest' });
    }

    select(item) {
      this.hidden.value = item.id;
      this.input.value = item.full_name;
      this.hideResults();
      this.wrapper.dispatchEvent(new CustomEvent('autocomplete:select', { detail: item, bubbles: true }));
    }

    clear() {
      this.hidden.value = '';
      this.input.value = '';
      this.items = [];
      this.hideResults();
      this.input.focus();
      this.wrapper.dispatchEvent(new CustomEvent('autocomplete:clear', { bubbles: true }));
    }

    showResults() {
      this.resultsBox.classList.remove('hidden');
    }

    hideResults() {
      this.resultsBox.classList.add('hidden');
    }
  }

  function initAll(root) {
    (root || document).querySelectorAll('[data-autocomplete-wrapper]').forEach((wrapper) => {
      if (wrapper.dataset.autocompleteInit) return;
      wrapper.dataset.autocompleteInit = '1';
      new MemberAutocomplete(wrapper);
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => initAll());
  } else {
    initAll();
  }

  // Expose for dynamically-injected forms (e.g. modals loaded via AJAX)
  window.OYAAutocomplete = { init: initAll, MemberAutocomplete };
})();