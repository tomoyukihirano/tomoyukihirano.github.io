(() => {
  'use strict';
  const payload = JSON.parse(document.getElementById('publication-data').textContent);
  const records = payload.records;
  const byId = new Map(records.map(record => [record.id, record]));
  const $ = id => document.getElementById(id);
  const escape = value => String(value ?? '').replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
  const normalize = value => String(value ?? '').normalize('NFKC').toLocaleLowerCase().replace(/\s+/g, ' ').trim();
  const kinds = {journal_article:'Journal article',review:'Review',preprint:'Preprint'};
  const allYears = [...new Set(records.filter(record => record.year !== null).map(record => record.year))].sort((a,b) => b-a);
  const state = {q:'',year:'all',type:'all',role:'all',sort:'newest'};
  const collections = [
    {id:'all',title:'All Publications',type:'all',role:'all'},
    {id:'journal',title:'Journal Articles',type:'journal_article',role:'all'},
    {id:'reviews',title:'Reviews',type:'review',role:'all'},
    {id:'preprints',title:'Preprints',type:'preprint',role:'all'},
    {id:'first',title:'First-author Publications',type:'all',role:'first'},
    {id:'lead',title:'First or Corresponding Author',type:'all',role:'first-corresponding'}
  ];
  const normalizedText = new Map(records.map(record => [record.id, normalize(record.search_text + ' ' + compactId(record) + ' ' + (record.presentation?.topics ?? []).join(' '))]));

  function yearKey(record) { return record.year === null ? (record.year_label === 'In press' ? 'in-press' : 'undated') : String(record.year); }
  function yearLabel(key) { return key === 'in-press' ? 'In press' : key === 'undated' ? 'Year not specified' : key; }
  function compareYears(a, b, sort = 'newest') {
    if (a === b) return 0;
    return a === 'in-press' ? -1 : b === 'in-press' ? 1 : a === 'undated' ? 1 : b === 'undated' ? -1 : sort === 'oldest' ? Number(a) - Number(b) : Number(b) - Number(a);
  }
  function compactId(record) { return record.paper_id || (record.type === 'review' ? 'R' + record.id.split('-').pop().slice(-3) : 'Preprint'); }
  function metricNote(metric, kind) {
    const months = ['January','February','March','April','May','June','July','August','September','October','November','December'];
    const parts = (metric.checked_month || '').match(/^(\d{4})-(\d{2})$/);
    const checked = parts ? `checked ${months[Number(parts[2])-1]} ${parts[1]}` : 'check month not recorded';
    const year = kind === 'IF' ? metric.metric_year : metric.jcr_release_year;
    return `Registered ${kind === 'IF' ? 'impact factor' : 'JCR quartile'}; ${checked}. ${kind === 'IF' ? 'Metric year' : 'JCR edition'} ${year ?? 'not confirmed'}.`;
  }
  function metricMarkup(record) {
    const metric = record.metrics || {};
    const badges = [];
    if (metric.impact_factor !== null && metric.impact_factor !== undefined) badges.push(`<span class="metric" title="${escape(metricNote(metric,'IF'))}">IF ${escape(metric.impact_factor)}</span>`);
    if (metric.jcr_quartile) badges.push(`<span class="metric" title="${escape(metricNote(metric,'JCR'))}">${escape(metric.jcr_quartile)}</span>`);
    if (metric.top10_percent === true) badges.push('<span class="metric top10" title="Existing article citation-ranking classification. A qualifying subject category is sufficient.">Top 10%</span>');
    return badges.length ? `<span class="metrics" aria-label="Existing evaluation data">${badges.join('')}</span>` : '';
  }
  function dateMarkup(record) {
    if (!record.dates) return '';
    const labels = {submitted:'Submitted',accepted:'Accepted',published_online:'Published online'};
    return `<dl class="date-grid">${Object.entries(labels).map(([key,label]) => {
      const date = record.dates[key] || {display:'N/A'};
      return `<div><dt>${label}</dt><dd>${escape(date.display)}${date.status === 'conflict' ? '<span class="date-note">Under review</span>' : ''}</dd></div>`;
    }).join('')}</dl>`;
  }
  function renderRecord(record, number) {
    const role = record.first_author && record.corresponding ? 'First & corresponding' : record.first_author ? 'First author' : record.corresponding ? 'Corresponding author' : '';
    const presentation = record.presentation || {};
    const typeBadge = `<span class="sr-only">${escape(kinds[record.type])}: </span>`;
    const numberLink = `<a class="publication-record-link" href="#${escape(record.id)}" aria-label="Link to publication ${number}">${number}</a>`;
    const body = record.display_fallback
      ? `<h3 class="sr-only">${escape(compactId(record))}</h3><div class="publication-heading"><p class="fallback-citation">${typeBadge}${record.citation_html}</p>${numberLink}</div>`
      : `<div class="publication-heading"><h3 class="publication-title">${typeBadge}${record.title_html || escape(record.title)}</h3>${numberLink}</div><p class="authors">${record.authors_html || ''}</p><p class="bibliography">${record.bibliography_html || ''}</p>`;
    const links = (record.links || []).map(link => {
      const cls = link.kind === 'preprint' ? ' preprint' : link.kind === 'publisher' && link.status === 'open' ? ' oa' : '';
      return `<a class="paper-link${cls}" href="${escape(link.url)}" target="_blank" rel="noopener"${link.license ? ` title="${escape(link.license)}"` : ''}>${escape(link.label)}</a>`;
    }).join('');
    const topics = presentation.topics?.length ? `<div class="topics">${presentation.topics.map(topic => `<span class="topic">${escape(topic)}</span>`).join('')}</div>` : '';
    return `<article class="publication" id="${escape(record.id)}" data-publication-id="${escape(record.id)}">
      <div class="publication-body">
      ${body}${presentation.summary ? `<p class="paper-summary">${escape(presentation.summary)}</p>` : ''}${topics}
      <div class="paper-actions">${links}${metricMarkup(record)}<details class="publication-details"><summary>${record.dates ? 'Dates & citation' : 'Full citation'}</summary><div class="detail-panel">${dateMarkup(record)}<h4>Original citation</h4><p class="citation">${record.citation_html}</p>${record.doi ? `<p class="doi-line">DOI: ${escape(record.doi)}</p>` : ''}<p class="record-meta"><a class="paper-id" href="#${escape(record.id)}" title="Permanent publication identifier">${escape(compactId(record))}</a>${role ? `<span class="author-role">${escape(role)}</span>` : ''}</p></div></details></div>
      </div></article>`;
  }
  function matches(record, filters = state) {
    if (filters.type !== 'all' && record.type !== filters.type) return false;
    if (filters.year !== 'all' && yearKey(record) !== filters.year) return false;
    if (filters.role === 'first' && record.first_author !== true) return false;
    if (filters.role === 'first-corresponding' && !record.first_author && !record.corresponding) return false;
    const words = normalize(filters.q).split(' ').filter(Boolean);
    return words.every(word => normalizedText.get(record.id).includes(word));
  }
  function syncCollections() {
    const active = collections.find(collection => collection.type === state.type && collection.role === state.role);
    for (const collection of collections) {
      const button = document.querySelector(`[data-collection="${collection.id}"]`);
      button.setAttribute('aria-pressed',String(collection === active));
      const count = records.filter(record => matches(record,{...state,type:collection.type,role:collection.role})).length;
      button.querySelector('.collection-count').textContent = count;
    }
    $('results-title').textContent = active?.title || 'Filtered Publications';
  }
  function renderChart(filtered) {
    $('year-chart').innerHTML = window.PublicationChart.render(filtered, {years: allYears, selectedYear: state.year});
  }
  function writeUrl() {
    try {
      const url = new URL(location.href);
      for (const [key,value] of Object.entries(state)) {
        if (!value || value === 'all' || key === 'sort' && value === 'newest') url.searchParams.delete(key);
        else url.searchParams.set(key,value);
      }
      history.replaceState(null,'',url.href);
    } catch (_) { /* Filters also work when opened as a local file. */ }
  }
  function render(updateUrl = true) {
    const filtered = records.filter(record => matches(record));
    const groupKeys = [...new Set(filtered.map(yearKey))].sort((a,b) => compareYears(a,b,state.sort));
    let number = filtered.length;
    $('publication-list').innerHTML = groupKeys.map(key => {
      const group = filtered.filter(record => yearKey(record) === key);
      return `<section class="year-group" id="year-${escape(key)}" aria-labelledby="heading-${escape(key)}"><h2 id="heading-${escape(key)}">${escape(yearLabel(key))}<span>${group.length}</span></h2>${group.map(record => renderRecord(record, number--)).join('')}</section>`;
    }).join('');
    $('year-nav').innerHTML = groupKeys.map(key => `<a href="#year-${escape(key)}">${escape(yearLabel(key))}</a>`).join('');
    $('result-count').textContent = `Showing ${filtered.length} of ${records.length} publications`;
    syncCollections();
    $('empty-state').hidden = filtered.length > 0;
    document.querySelector('.publications-layout').hidden = filtered.length === 0;
    renderChart(filtered);
    if (updateUrl) writeUrl();
  }
  function syncInputs() {
    $('search').value = state.q;
    $('year-filter').value = state.year;
    $('type-filter').value = state.type;
    $('role-filter').value = state.role;
    $('sort-filter').value = state.sort;
  }
  function reset() {
    Object.assign(state,{q:'',year:'all',type:'all',role:'all',sort:'newest'});
    syncInputs(); render();
  }
  function focusSearch() {
    $('advanced-filters').open = true;
    $('search').focus();
  }
  function readUrl() {
    const query = new URLSearchParams(location.search);
    state.q = query.get('q') || '';
    state.year = ['all','in-press','undated',...allYears.map(String)].includes(query.get('year')) ? query.get('year') : 'all';
    state.type = ['all',...Object.keys(kinds)].includes(query.get('type')) ? query.get('type') : 'all';
    state.role = ['all','first','first-corresponding'].includes(query.get('role')) ? query.get('role') : 'all';
    state.sort = query.get('sort') === 'oldest' ? 'oldest' : 'newest';
    $('advanced-filters').open = Boolean(state.q || state.year !== 'all' || state.sort !== 'newest' || !collections.some(item => item.type === state.type && item.role === state.role));
  }
  function revealAnchor() {
    let id;
    try { id = decodeURIComponent(location.hash.slice(1)); } catch (_) { return; }
    if (id === 'reviews' || id === 'preprints') {
      Object.assign(state,{q:'',year:'all',role:'all',type:id === 'reviews' ? 'review' : 'preprint'});
      syncInputs();render();
      requestAnimationFrame(() => $('publication-list').scrollIntoView({block:'start',behavior:'auto'}));
      return;
    }
    if (id === 'book-chapters-3-in-total' || id === 'others') {
      const section = $(id);
      if (section) { section.open = true; requestAnimationFrame(() => section.scrollIntoView({block:'start',behavior:'auto'})); }
      return;
    }
    if (!byId.has(id)) return;
    if (!$(id)) reset();
    requestAnimationFrame(() => $(id)?.scrollIntoView({block:'start',behavior:'auto'}));
  }
  $('search').addEventListener('input',event => {state.q = event.target.value;render();});
  $('collection-filters').addEventListener('click',event => {
    const button = event.target.closest('[data-collection]');
    if (!button) return;
    const collection = collections.find(item => item.id === button.dataset.collection);
    if (!collection) return;
    state.type = collection.type;
    state.role = collection.role;
    syncInputs();render();
  });
  $('year-filter').addEventListener('change',event => {state.year = event.target.value;render();});
  $('type-filter').addEventListener('change',event => {state.type = event.target.value;render();});
  $('role-filter').addEventListener('change',event => {state.role = event.target.value;render();});
  $('sort-filter').addEventListener('change',event => {state.sort = event.target.value;render();});
  $('year-chart').addEventListener('click',event => {
    const button = event.target.closest('[data-year]');
    if (!button) return;
    state.year = state.year === button.dataset.year ? 'all' : button.dataset.year;
    syncInputs();render();
  });
  $('reset').addEventListener('click',reset);
  $('empty-reset').addEventListener('click',() => {reset();focusSearch();});
  document.addEventListener('keydown',event => {
    if (event.key === '/' && !$('view-publications').hidden && !/INPUT|TEXTAREA|SELECT/.test(document.activeElement.tagName) && !document.activeElement.isContentEditable) {
      event.preventDefault();focusSearch();
    }
  });
  window.addEventListener('popstate',() => {readUrl();syncInputs();render(false);revealAnchor();});
  window.addEventListener('hashchange',revealAnchor);
  window.addEventListener('scroll',() => {$('back-to-top').hidden = window.scrollY < 800;},{passive:true});
  $('back-to-top').addEventListener('click',() => window.scrollTo({top:0,behavior:matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth'}));
  readUrl();syncInputs();render(false);revealAnchor();
  window.revealPublicationAnchor = revealAnchor;
})();
