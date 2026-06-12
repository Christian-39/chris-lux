/**
 * OYA Search & Filter Module
 * Advanced search, filters, and data grid functionality
 */

(function() {
  'use strict';

  // ─── Debounce Utility ───
  function debounce(fn, delay) {
    let timeout;
    return function(...args) {
      clearTimeout(timeout);
      timeout = setTimeout(() => fn.apply(this, args), delay);
    };
  }

  // ─── Table Search with Highlight ───
  class TableSearch {
    constructor(input, table) {
      this.input = input;
      this.table = table;
      this.rows = table.querySelectorAll('tbody tr');
      this.init();
    }

    init() {
      this.input.addEventListener('input', debounce(() => this.search(), 200));
    }

    search() {
      const query = this.input.value.toLowerCase().trim();
      let visibleCount = 0;

      this.rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        const match = !query || text.includes(query);
        row.style.display = match ? '' : 'none';
        if (match) visibleCount++;

        // Highlight matches
        if (query && match) {
          this.highlightCells(row, query);
        } else {
          this.clearHighlight(row);
        }
      });

      // Show empty state if no results
      this.toggleEmptyState(visibleCount === 0);
    }

    highlightCells(row, query) {
      row.querySelectorAll('td').forEach(cell => {
        const text = cell.textContent;
        const regex = new RegExp(`(${query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
        if (regex.test(text) && !cell.querySelector('mark')) {
          cell.innerHTML = text.replace(regex, '<mark style="background:rgba(11,61,145,0.15);color:var(--oya-primary);padding:1px 2px;border-radius:3px;">$1</mark>');
        }
      });
    }

    clearHighlight(row) {
      row.querySelectorAll('td').forEach(cell => {
        const mark = cell.querySelector('mark');
        if (mark) {
          cell.textContent = cell.textContent;
        }
      });
    }

    toggleEmptyState(show) {
      let emptyRow = this.table.querySelector('.search-empty-row');
      if (show) {
        if (!emptyRow) {
          const colCount = this.table.querySelector('thead tr')?.children.length || 1;
          emptyRow = document.createElement('tr');
          emptyRow.className = 'search-empty-row';
          emptyRow.innerHTML = `
            <td colspan="${colCount}" style="text-align:center;padding:3rem 1rem;">
              <div style="color:var(--oya-text-muted);">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="margin-bottom:0.75rem;opacity:0.5;">
                  <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
                </svg>
                <p style="font-weight:500;">No results found</p>
                <p style="font-size:0.8125rem;margin-top:0.25rem;">Try adjusting your search terms</p>
              </div>
            </td>
          `;
          this.table.querySelector('tbody').appendChild(emptyRow);
        }
        emptyRow.style.display = '';
      } else if (emptyRow) {
        emptyRow.style.display = 'none';
      }
    }
  }

  // ─── Column Filter ───
  class ColumnFilter {
    constructor(select, table, columnIndex) {
      this.select = select;
      this.table = table;
      this.columnIndex = columnIndex;
      this.init();
    }

    init() {
      this.select.addEventListener('change', () => this.filter());
    }

    filter() {
      const value = this.select.value.toLowerCase();
      const rows = this.table.querySelectorAll('tbody tr:not(.search-empty-row)');

      rows.forEach(row => {
        const cell = row.children[this.columnIndex];
        if (!cell) return;

        const cellText = cell.textContent.toLowerCase().trim();
        const match = !value || cellText === value;

        // Check if row already hidden by other filters
        const currentDisplay = row.style.display;
        if (!match) {
          row.style.display = 'none';
        } else if (currentDisplay === 'none') {
          // Only show if no other filters are hiding it
          row.style.display = '';
        }
      });
    }
  }

  // ─── Sortable Table ───
  class SortableTable {
    constructor(table) {
      this.table = table;
      this.tbody = table.querySelector('tbody');
      this.headers = table.querySelectorAll('thead th[data-sort]');
      this.init();
    }

    init() {
      this.headers.forEach((header, index) => {
        header.style.cursor = 'pointer';
        header.style.userSelect = 'none';

        // Add sort icon
        const icon = document.createElement('span');
        icon.className = 'sort-icon';
        icon.innerHTML = ' \u2195';
        icon.style.color = 'var(--oya-text-muted)';
        icon.style.fontSize = '0.75rem';
        header.appendChild(icon);

        header.addEventListener('click', () => this.sort(index, header.dataset.sort));
      });
    }

    sort(columnIndex, type) {
      const rows = Array.from(this.tbody.querySelectorAll('tr:not(.search-empty-row)'));
      const isAsc = !this.tbody.classList.contains('sorted-asc');

      rows.sort((a, b) => {
        const aVal = this.getValue(a.children[columnIndex], type);
        const bVal = this.getValue(b.children[columnIndex], type);

        if (aVal < bVal) return isAsc ? -1 : 1;
        if (aVal > bVal) return isAsc ? 1 : -1;
        return 0;
      });

      // Update sort indicators
      this.headers.forEach(h => {
        const icon = h.querySelector('.sort-icon');
        if (icon) icon.innerHTML = ' \u2195';
      });

      const currentIcon = this.headers[columnIndex]?.querySelector('.sort-icon');
      if (currentIcon) {
        currentIcon.innerHTML = isAsc ? ' \u2191' : ' \u2193';
      }

      this.tbody.classList.toggle('sorted-asc', isAsc);
      rows.forEach(row => this.tbody.appendChild(row));
    }

    getValue(cell, type) {
      const text = cell.textContent.trim();

      if (type === 'number') {
        return parseFloat(text.replace(/[^\d.-]/g, '')) || 0;
      }
      if (type === 'date') {
        return new Date(text).getTime() || 0;
      }
      return text.toLowerCase();
    }
  }

  // ─── Initialize Search Inputs ───
  function initSearchInputs() {
    document.querySelectorAll('[data-search-table]').forEach(input => {
      const tableId = input.dataset.searchTable;
      const table = document.getElementById(tableId);
      if (table) {
        new TableSearch(input, table);
      }
    });
  }

  // ─── Initialize Column Filters ───
  function initColumnFilters() {
    document.querySelectorAll('[data-filter-table]').forEach(select => {
      const tableId = select.dataset.filterTable;
      const column = parseInt(select.dataset.filterColumn, 10);
      const table = document.getElementById(tableId);
      if (table && !isNaN(column)) {
        new ColumnFilter(select, table, column);
      }
    });
  }

  // ─── Initialize Sortable Tables ───
  function initSortableTables() {
    document.querySelectorAll('table[data-sortable]').forEach(table => {
      new SortableTable(table);
    });
  }

  // ─── Global Search (Topbar) ───
  function initGlobalSearch() {
    const searchInput = document.getElementById('globalSearch');
    if (!searchInput) return;

    const resultsContainer = document.getElementById('searchResults');

    searchInput.addEventListener('input', debounce(() => {
      const query = searchInput.value.trim();
      if (query.length < 2) {
        if (resultsContainer) resultsContainer.classList.add('hidden');
        return;
      }

      // Simulate search results
      if (resultsContainer) {
        resultsContainer.classList.remove('hidden');
        resultsContainer.innerHTML = `
          <div class="dropdown-item">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
            <span>Search members for "${query}"</span>
          </div>
          <div class="dropdown-item">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="3" width="20" height="14" rx="2" ry="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg>
            <span>Search records for "${query}"</span>
          </div>
        `;
      }
    }, 300));

    // Hide results on outside click
    document.addEventListener('click', (e) => {
      if (!searchInput.contains(e.target) && resultsContainer && !resultsContainer.contains(e.target)) {
        resultsContainer.classList.add('hidden');
      }
    });
  }

  // ─── Initialize ───
  function init() {
    initSearchInputs();
    initColumnFilters();
    initSortableTables();
    initGlobalSearch();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  // Expose classes for manual initialization
  window.OYASearch = {
    TableSearch,
    ColumnFilter,
    SortableTable
  };
})();
