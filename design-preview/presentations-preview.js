/* Filter only canonical public presentation cards; no network or database writes. */
(() => {
  'use strict';

  const normalize = value => String(value).normalize('NFKC').toLocaleLowerCase();

  function initializePresentationPreview() {
    const page = document.getElementById('presentations-page');
    if (!page || page.dataset.prInitialized === 'true') return;

    const controls = page.querySelector('.pr-controls');
    const search = page.querySelector('#pr-search');
    const year = page.querySelector('#pr-year-filter');
    const invitation = page.querySelector('#pr-invited-filter');
    const buttons = [...page.querySelectorAll('[data-pr-scope]')];
    const reset = page.querySelector('.pr-reset');
    const status = page.querySelector('.pr-status');
    const empty = page.querySelector('.pr-empty');
    const sidebar = page.querySelector('.pr-year-sidebar');
    const yearLinks = [...page.querySelectorAll('[data-pr-year-link]')];
    const groups = [...page.querySelectorAll('[data-pr-year]')];
    const records = [...page.querySelectorAll('.pr-record')].map(element => ({
      element,
      year: element.dataset.year,
      scope: element.dataset.conferenceScope,
      invited: element.dataset.invited === 'true',
      search: normalize(element.dataset.search || element.textContent),
    }));
    let scope = 'all';

    function applyFilters() {
      const tokens = normalize(search.value).trim().split(/\s+/).filter(Boolean);
      const visibleYears = new Map();
      let visible = 0;
      for (const record of records) {
        const match = (year.value === 'all' || year.value === record.year)
          && (scope === 'all' || scope === record.scope)
          && (invitation.value === 'all' || record.invited)
          && tokens.every(token => record.search.includes(token));
        record.element.hidden = !match;
        if (match) {
          visible += 1;
          visibleYears.set(record.year, (visibleYears.get(record.year) || 0) + 1);
        }
      }
      for (const group of groups) {
        const count = visibleYears.get(group.dataset.prYear) || 0;
        group.hidden = count === 0;
        group.querySelector('[data-pr-year-count]').textContent = String(count);
      }
      for (const link of yearLinks) {
        link.hidden = !visibleYears.has(link.dataset.prYearLink);
      }
      for (const button of buttons) {
        button.setAttribute('aria-pressed', String(button.dataset.prScope === scope));
      }
      const active = search.value.length > 0 || year.value !== 'all'
        || invitation.value !== 'all' || scope !== 'all';
      reset.disabled = !active;
      empty.hidden = visible > 0;
      sidebar.hidden = visible === 0;
      status.replaceChildren();
      const count = document.createElement('strong');
      count.textContent = String(visible);
      status.append(count, ` of ${records.length} presentations`);
    }

    function resetFilters() {
      search.value = '';
      year.value = 'all';
      invitation.value = 'all';
      scope = 'all';
      applyFilters();
    }

    search.addEventListener('input', applyFilters);
    year.addEventListener('change', applyFilters);
    invitation.addEventListener('change', applyFilters);
    for (const button of buttons) {
      button.addEventListener('click', () => {
        scope = button.dataset.prScope;
        applyFilters();
      });
    }
    reset.addEventListener('click', resetFilters);
    page.querySelector('.pr-empty-reset').addEventListener('click', () => {
      resetFilters();
      search.focus();
    });
    page.dataset.prInitialized = 'true';
    controls.hidden = false;
    applyFilters();
  }

  window.initializePresentationPreview = initializePresentationPreview;
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializePresentationPreview, { once: true });
  } else {
    initializePresentationPreview();
  }
})();
