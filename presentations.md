---
layout: page
title: "Presentations – 平野 知之 / Tomoyuki Hirano"
heading: "Presentations"
permalink: /presentations/
nav: presentations
page_id: 76
---

〇は発表者を表しています。招待講演・依頼講演には「招待講演」マークを付しています。
{: .wp-block-paragraph }

<div class="achievement-filter" data-achievement-filter data-target="presentation-list" aria-label="発表区分の絞り込み">
  <button type="button" class="achievement-filter__button" data-filter-value="all" aria-pressed="true">全発表 <span data-filter-count="all"></span></button>
  <button type="button" class="achievement-filter__button" data-filter-value="domestic" aria-pressed="false">国内学会 <span data-filter-count="domestic"></span></button>
  <button type="button" class="achievement-filter__button" data-filter-value="international" aria-pressed="false">国際学会 <span data-filter-count="international"></span></button>
</div>
<p class="screen-reader-text" id="presentation-filter-status" aria-live="polite"></p>

{% assign presentation_years = "2026,2025,2024,2023,2022,2021,2020,2019,2018" | split: "," %}
{% assign presentation_total = 0 %}
{% for presentation_year in presentation_years %}
  {% assign presentation_bucket = site.data.presentations[presentation_year] %}
  {% if presentation_bucket and presentation_bucket.records %}
    {% assign presentation_total = presentation_total | plus: presentation_bucket.records.size %}
  {% endif %}
{% endfor %}

<ol id="presentation-list" class="wp-block-list achievement-list" reversed start="{{ presentation_total }}" aria-describedby="presentation-filter-status">
{% for presentation_year in presentation_years %}
  {% assign presentation_bucket = site.data.presentations[presentation_year] %}
  {% if presentation_bucket and presentation_bucket.records %}
    {% for presentation in presentation_bucket.records %}
      <li data-filters="all {{ presentation.scope }}">{{ presentation.display_html }}{% if presentation.classification.invited %} <span class="achievement-badge achievement-badge--invited">招待講演</span>{% endif %}{% if presentation.classification.award %} <span class="achievement-badge achievement-badge--award">受賞</span>{% endif %}</li>
    {% endfor %}
  {% endif %}
{% endfor %}
</ol>

<script src="{{ '/assets/achievement-filters.js' | relative_url }}" defer></script>
