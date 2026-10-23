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
  const state = {q:'',year:'all',type:'all',role:'all'};
  const normalizedText = new Map(records.map(record => [record.id, normalize(record.search_text + ' ' + compactId(record) + ' ' + (record.presentation?.topics ?? []).join(' '))]));

  function yearKey(record) { return record.year === null ? (record.year_label === 'In press' ? 'in-press' : 'undated') : String(record.year); }
  function yearLabel(key) { return key === 'in-press' ? 'In press' : key === 'undated' ? 'Year not specified' : key; }
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
  function renderRecord(record) {
    const role = record.first_author && record.corresponding ? 'First & corresponding' : record.first_author ? 'First author' : record.corresponding ? 'Corresponding author' : '';
    const presentation = record.presentation || {};
    const body = record.display_fallback
      ? `<h3 class="sr-only">${escape(compactId(record))}</h3><p class="fallback-citation">${record.citation_html}</p>`
      : `<h3>${record.title_html || escape(record.title)}</h3><p class="authors">${record.authors_html || ''}</p><p class="bibliography">${record.bibliography_html || ''}</p>`;
    const links = (record.links || []).map(link => {
      const cls = link.kind === 'preprint' ? ' preprint' : link.kind === 'publisher' && link.status === 'open' ? ' oa' : '';
      return `<a class="paper-link${cls}" href="${escape(link.url)}" target="_blank" rel="noopener"${link.license ? ` title="${escape(link.license)}"` : ''}>${escape(link.label)} <span aria-hidden="true">↗</span></a>`;
    }).join('');
    const topics = presentation.topics?.length ? `<div class="topics">${presentation.topics.map(topic => `<span class="topic">${escape(topic)}</span>`).join('')}</div>` : '';
    return `<article class="publication" id="${escape(record.id)}" data-publication-id="${escape(record.id)}">
      <div class="publication-body">
      <div class="paper-topline"><span class="type-badge type-${escape(record.type)}">${escape(kinds[record.type])}</span>${role ? `<span class="role-dot" aria-hidden="true">·</span><span class="author-role">${escape(role)}</span>` : ''}<a class="paper-id" href="#${escape(record.id)}" title="Permanent publication identifier">${escape(compactId(record))}</a></div>
      ${body}${presentation.summary ? `<p class="paper-summary">${escape(presentation.summary)}</p>` : ''}${topics}
      <div class="paper-actions">${links}${metricMarkup(record)}</div>
      <details class="publication-details"><summary>${record.dates ? 'Dates & citation' : 'Full citation'}</summary><div class="detail-panel">${dateMarkup(record)}<h4>Original citation</h4><p class="citation">${record.citation_html}</p>${record.doi ? `<p class="doi-line">DOI: ${escape(record.doi)}</p>` : ''}</div></details>
      </div></article>`;
  }
  function matches(record, includeYear = true) {
    if (state.type !== 'all' && record.type !== state.type) return false;
    if (includeYear && state.year !== 'all' && yearKey(record) !== state.year) return false;
    if (state.role === 'first' && record.first_author !== true) return false;
    if (state.role === 'first-corresponding' && !record.first_author && !record.corresponding) return false;
    const words = normalize(state.q).split(' ').filter(Boolean);
    return words.every(word => normalizedText.get(record.id).includes(word));
  }
  function renderChart(filtered) {
    $('year-chart').innerHTML = window.PublicationChart.render(filtered, {years: allYears, selectedYear: state.year});
  }
  function writeUrl() {
    try {
      const url = new URL(location.href);
      for (const [key,value] of Object.entries(state)) {
        if (!value || value === 'all') url.searchParams.delete(key);
        else url.searchParams.set(key,value);
      }
      history.replaceState(null,'',url.href);
    } catch (_) { /* Filters also work when opened as a local file. */ }
  }
  function render(updateUrl = true) {
    const filtered = records.filter(record => matches(record));
    const groupKeys = [...new Set(filtered.map(yearKey))].sort((a,b) => a === 'in-press' ? -1 : b === 'in-press' ? 1 : a === 'undated' ? 1 : b === 'undated' ? -1 : Number(b)-Number(a));
    $('publication-list').innerHTML = groupKeys.map(key => {
      const group = filtered.filter(record => yearKey(record) === key);
      return `<section class="year-group" id="year-${escape(key)}" aria-labelledby="heading-${escape(key)}"><h2 id="heading-${escape(key)}">${escape(yearLabel(key))}<span>${group.length}</span></h2>${group.map(renderRecord).join('')}</section>`;
    }).join('');
    $('year-nav').innerHTML = groupKeys.map(key => `<a href="#year-${escape(key)}">${escape(yearLabel(key))}</a>`).join('');
    $('result-count').innerHTML = `<strong>${filtered.length}</strong> of ${records.length} publications${state.role !== 'all' ? ' · Tomoyuki Hirano’s authorship' : ''}`;
    $('empty-state').hidden = filtered.length > 0;
    document.querySelector('.publications-layout').hidden = filtered.length === 0;
    $('reset').disabled = !state.q && state.year === 'all' && state.type === 'all' && state.role === 'all';
    document.querySelectorAll('[data-role]').forEach(button => {
      const active = button.dataset.role === state.role;
      button.setAttribute('aria-pressed',String(active));
      button.classList.toggle('active',active);
    });
    renderChart(filtered);
    if (updateUrl) writeUrl();
  }
  function syncInputs() {
    $('search').value = state.q;
    $('year-filter').value = state.year;
    $('type-filter').value = state.type;
  }
  function reset() {
    Object.assign(state,{q:'',year:'all',type:'all',role:'all'});
    syncInputs(); render();
  }
  function readUrl() {
    const query = new URLSearchParams(location.search);
    state.q = query.get('q') || '';
    state.year = ['all','in-press','undated',...allYears.map(String)].includes(query.get('year')) ? query.get('year') : 'all';
    state.type = ['all',...Object.keys(kinds)].includes(query.get('type')) ? query.get('type') : 'all';
    state.role = ['all','first','first-corresponding'].includes(query.get('role')) ? query.get('role') : 'all';
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
  $('year-filter').addEventListener('change',event => {state.year = event.target.value;render();});
  $('type-filter').addEventListener('change',event => {state.type = event.target.value;render();});
  document.querySelectorAll('[data-role]').forEach(button => button.addEventListener('click',() => {state.role = button.dataset.role;render();}));
  $('year-chart').addEventListener('click',event => {
    const button = event.target.closest('[data-year]');
    if (!button) return;
    state.year = state.year === button.dataset.year ? 'all' : button.dataset.year;
    syncInputs();render();
  });
  $('reset').addEventListener('click',reset);
  $('empty-reset').addEventListener('click',() => {reset();$('search').focus();});
  document.addEventListener('keydown',event => {
    if (event.key === '/' && !$('view-publications').hidden && !/INPUT|TEXTAREA|SELECT/.test(document.activeElement.tagName) && !document.activeElement.isContentEditable) {
      event.preventDefault();$('search').focus();
    }
  });
  window.addEventListener('popstate',() => {readUrl();syncInputs();render(false);revealAnchor();});
  window.addEventListener('hashchange',revealAnchor);
  window.addEventListener('scroll',() => {$('back-to-top').hidden = window.scrollY < 800;},{passive:true});
  $('back-to-top').addEventListener('click',() => window.scrollTo({top:0,behavior:matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth'}));
  readUrl();syncInputs();render(false);revealAnchor();
  window.revealPublicationAnchor = revealAnchor;
})();
