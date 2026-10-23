/* A dependency-free, one-rectangular-unit-per-publication chart.
 * Keep the output equivalent to publication_chart.py for the static fallback.
 * The host app owns filters and handles clicks on [data-year].
 */
(() => {
  'use strict';
  const escape = value => String(value ?? '').replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#x27;'}[char]));
  const numericYear = value => {
    const text = String(value);
    return /^\d+$/.test(text) && Number(text) > 0 && Number(text) < 10000 ? Number(text) : null;
  };
  const yearKey = record => {
    const year = numericYear(record.year);
    return year === null ? (record.year_label === 'In press' ? 'in-press' : 'undated') : String(year);
  };
  const lead = record => record.first_author === true || record.corresponding === true;
  const unknownRole = record => !lead(record) && !(record.first_author === false && record.corresponding === false);
  const units = records => [...records.filter(lead), ...records.filter(record => !lead(record))]
    .map(record => `<span class="publication-square-unit publication-square-${lead(record) ? 'lead' : 'other'}" data-publication-id="${escape(record.id)}"></span>`).join('');
  const description = (label, records, active) => {
    const leadCount = records.filter(lead).length;
    const unknown = records.filter(unknownRole).length;
    const other = records.length - leadCount - unknown;
    const parts = [`${label}: ${records.length} publications`, `${leadCount} first or corresponding author`, `${other} coauthor`];
    if (unknown) parts.push(`${unknown} authorship not recorded`);
    return parts.join('; ') + (active ? '. Clear year filter.' : '. Filter to this group.');
  };
  const scale = maximum => {
    const rawStep = Math.max(1, Math.ceil(maximum / 4));
    const magnitude = 10 ** Math.floor(Math.log10(rawStep));
    const step = [1,2,5,10].map(value => value * magnitude).find(value => value >= rawStep);
    const limit = Math.max(1, Math.ceil(maximum / step)) * step;
    return {limit, ticks:Array.from({length:limit / step + 1}, (_, index) => index * step)};
  };

  function render(records, {years = null, selectedYear = 'all'} = {}) {
    const candidates = years ?? records.map(record => record.year);
    const suppliedYears = [...candidates, ...records.map(record => record.year)].map(numericYear).filter(year => year !== null);
    let axisYears = [...new Set(suppliedYears)].sort((a, b) => a - b);
    if (axisYears.length) axisYears = Array.from({length:axisYears[axisYears.length - 1] - axisYears[0] + 1}, (_, index) => axisYears[0] + index);
    const groups = new Map([...axisYears.map(String), 'in-press', 'undated'].map(key => [key, []]));
    records.forEach(record => groups.get(yearKey(record)).push(record));
    const maximum = Math.max(0, ...axisYears.map(year => groups.get(String(year)).length));
    const {limit, ticks} = scale(maximum);
    const columns = axisYears.map(year => {
      const key = String(year);
      const group = groups.get(key);
      const active = String(selectedYear) === key;
      const label = escape(description(key, group, active));
      return `<button type="button" class="publication-square-column${active ? ' is-selected' : ''}" data-year="${key}" aria-label="${label}" title="${label}" aria-pressed="${active}"><span class="publication-square-plot" aria-hidden="true"><span class="publication-square-stack">${units(group)}</span></span><span class="publication-square-year">${key}</span></button>`;
    }).join('');
    const tickHtml = ticks.map(tick => `<span class="publication-square-y-tick" style="--publication-tick:${tick}">${tick}</span>`).join('');
    const gridHtml = ticks.map(tick => `<i class="publication-square-grid-line" style="--publication-tick:${tick}"></i>`).join('');
    const chart = axisYears.length
      ? `<span class="publication-square-axis-title" aria-hidden="true">Number of publications</span><div class="publication-square-scroll"><div class="publication-square-axis-panel" style="--publication-year-count:${axisYears.length};--publication-scale:${limit}"><div class="publication-square-y-axis" aria-hidden="true">${tickHtml}</div><div class="publication-square-graph"><div class="publication-square-grid" aria-hidden="true">${gridHtml}</div><div class="publication-square-columns">${columns}</div></div></div></div>`
      : '<p class="publication-square-empty">No dated publications in this selection.</p>';
    const additional = [['in-press','In press'], ['undated','Year not specified']].map(([key, text]) => {
      const group = groups.get(key);
      if (!group.length) return '';
      const active = String(selectedYear) === key;
      const label = escape(description(text, group, active));
      return `<button type="button" class="publication-square-additional${active ? ' is-selected' : ''}" data-year="${key}" aria-label="${label}" title="${label}" aria-pressed="${active}"><span>${text} <span class="publication-square-additional-count">${group.length}</span></span><span class="publication-square-additional-units" aria-hidden="true">${units(group)}</span></button>`;
    }).join('');
    const additionalHtml = additional ? `<div class="publication-square-additional-groups">${additional}</div>` : '';
    const unknown = records.filter(unknownRole).length;
    const note = unknown ? `<p class="publication-square-note">Authorship not recorded for ${unknown}; shown in gray.</p>` : '';
    return `<div class="publication-square-chart" role="group" aria-label="Publication counts by year. One block represents one publication."><div class="publication-square-main"><div class="publication-square-legend"><span class="publication-square-key"><i class="publication-square-swatch publication-square-lead" aria-hidden="true"></i>First or corresponding</span><span class="publication-square-key"><i class="publication-square-swatch publication-square-other" aria-hidden="true"></i>Coauthor</span></div>${chart}</div><div class="publication-square-footer"><span class="publication-square-unit-note">1 block = 1 publication</span>${additionalHtml}</div>${note}</div>`;
  }

  globalThis.PublicationChart = Object.freeze({render, yearKey});
})();
