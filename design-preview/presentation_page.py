"""Render the private design preview from the canonical presentation records.

This module is read-only with respect to the source database.  In particular,
it does not infer presenter identities, invitation status, event scope, English
names or dates.  All displayed bibliographic values come from ``display``.
"""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
from html import escape
from html.parser import HTMLParser
from pathlib import Path
import re
from typing import Any

import yaml


SCOPES = ("domestic", "international", "other")
SCOPE_LABELS = {
    "domestic": "Domestic",
    "international": "International",
    "other": "Other",
    "unclassified": "",
}


class _TitleParser(HTMLParser):
    """Keep typographic markup while excluding executable HTML/attributes."""

    ALLOWED = frozenset({"sub", "sup", "em", "i", "strong", "b", "u"})

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.html: list[str] = []
        self.plain: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, Any]]) -> None:
        if tag in self.ALLOWED:
            self.html.append(f"<{tag}>")

    def handle_endtag(self, tag: str) -> None:
        if tag in self.ALLOWED:
            self.html.append(f"</{tag}>")

    def handle_data(self, data: str) -> None:
        self.html.append(escape(data, quote=False))
        self.plain.append(data)


def _title_markup(value: str, replacements: list[tuple[str, str]]) -> tuple[str, str]:
    for original, formatted in replacements:
        value = value.replace(original, formatted)
    parser = _TitleParser()
    parser.feed(value)
    parser.close()
    return "".join(parser.html), "".join(parser.plain)


def _formula_replacements(source: Path) -> list[tuple[str, str]]:
    """Read the same literal replacements used by the public Jekyll include."""
    include = source / "_includes" / "chemical-formula.html"
    if not include.is_file():
        return []
    return re.findall(
        r"\|\s*replace:\s*'([^']*)'\s*,\s*'([^']*)'",
        include.read_text(encoding="utf-8"),
    )


def build_presentations(source: str | Path) -> dict[str, Any]:
    """Return public records, exact canonical display data and derived counts.

    ``records`` are ordered by descending year, then ascending display_order.
    ``display`` and ``classification`` are unmodified copies of those source
    fields.  Derived ``scope`` follows the existing site's explicit fallback
    map; an unknown scope remains unclassified and appears only in All.
    """
    source = Path(source)
    directory = source / "_data" / "presentations"
    files = sorted({*directory.glob("*.yml"), *directory.glob("*.yaml")})
    if not files:
        raise FileNotFoundError(f"No presentation database found under {directory}")

    scopes_path = source / "_data" / "presentation_scopes.yml"
    scope_data = (
        yaml.safe_load(scopes_path.read_text(encoding="utf-8")) or {}
        if scopes_path.is_file()
        else {}
    )
    scope_ids = {scope: set(scope_data.get(scope) or []) for scope in SCOPES}
    replacements = _formula_replacements(source)
    records: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    for path in files:
        document = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        for item in document.get("records", []):
            if item.get("public") is False:
                continue
            record_id = str(item["id"])
            if record_id in seen_ids:
                raise ValueError(f"Duplicate public presentation ID: {record_id}")
            seen_ids.add(record_id)
            display = deepcopy(item["display"])
            classification = deepcopy(item.get("classification") or {})
            scope = classification.get("conference_scope")
            if scope not in SCOPES:
                scope = next(
                    (key for key in SCOPES if record_id in scope_ids[key]),
                    "unclassified",
                )
            title_html, title_text = _title_markup(display["title_html"], replacements)
            search_values = [
                record_id,
                title_text,
                *(author["name"] for author in display["authors"]),
                display["conference"],
                display.get("location") or "",
                (display.get("dates") or {}).get("text") or "",
                *(display.get("annotations") or []),
            ]
            records.append(
                {
                    "id": record_id,
                    "year": int(item.get("year", document.get("year"))),
                    "display_order": item.get("display_order", 0),
                    "display": display,
                    "classification": classification,
                    "scope": scope,
                    "event_type": classification.get("event_type"),
                    "invited": classification.get("invited"),
                    "title_html": title_html,
                    "title_text": title_text,
                    "search_text": " ".join(str(value) for value in search_values),
                }
            )

    records.sort(key=lambda record: (-record["year"], record["display_order"]))
    scope_counts = Counter(record["scope"] for record in records)
    year_counts = Counter(record["year"] for record in records)
    years = sorted(year_counts, reverse=True)
    return {
        "records": records,
        "years": years,
        "counts": {
            "all": len(records),
            "invited": sum(record["invited"] is True for record in records),
            **{scope: scope_counts[scope] for scope in (*SCOPES, "unclassified")},
            "by_year": {year: year_counts[year] for year in years},
        },
    }


def _e(value: Any) -> str:
    return escape(str(value), quote=True)


def _authors(display: dict[str, Any], scope: str) -> str:
    names = []
    for author in display["authors"]:
        name = _e(author["name"])
        if author.get("highlight"):
            name = f'<strong class="pr-author-self"><u>{name}</u></strong>'
        names.append(name)
    return (", " if scope == "international" else "，").join(names)


def _render_record(record: dict[str, Any], number: int) -> str:
    display = record["display"]
    record_id = _e(record["id"])
    scope = record["scope"]
    invited = record["invited"] is True
    invitation_value = "true" if invited else "false" if record["invited"] is False else "unknown"
    metadata = []
    if SCOPE_LABELS.get(scope):
        metadata.append(f'<span class="pr-scope">{SCOPE_LABELS[scope]}</span>')
    if invited:
        invited_label = "Invited talk" if scope == "international" else "招待講演"
        metadata.append(f'<span class="pr-invited">{invited_label}</span>')
    for annotation in display.get("annotations") or []:
        if invited and annotation in {"招待講演", "Invited talk"}:
            continue
        annotation_open, annotation_close = ("[", "]") if scope == "international" else ("【", "】")
        metadata.append(f'<span class="pr-annotation">{annotation_open}{_e(annotation)}{annotation_close}</span>')
    metadata.append(
        f'<a class="pr-record-link" href="#{record_id}" '
        f'aria-label="Link to presentation {number}">{number}</a>'
    )
    details = []
    if display.get("location"):
        details.append(f'<span class="pr-location">{_e(display["location"])}</span>')
    dates_text = (display.get("dates") or {}).get("text")
    if dates_text:
        details.append(f'<span class="pr-date">{_e(dates_text)}</span>')
    details_html = '<span class="pr-separator" aria-hidden="true"> · </span>'.join(details)
    event_type_attr = (
        f' data-event-type="{_e(record["event_type"])}"'
        if record["event_type"] is not None
        else ""
    )
    language_attr = ' lang="en"' if scope == "international" else ""
    return (
        f'<li class="pr-record" id="{record_id}" data-year="{record["year"]}" '
        f'data-conference-scope="{scope}" data-invited="{invitation_value}" '
        f'data-search="{_e(record["search_text"])}"{event_type_attr}{language_attr}>'
        f'<div class="pr-topline">{"".join(metadata)}</div>'
        f'<h3 class="pr-title">{record["title_html"]}</h3>'
        f'<p class="pr-authors">{_authors(display, scope)}</p>'
        f'<p class="pr-venue">{_e(display["conference"])}</p>'
        f'<p class="pr-details">{details_html}</p>'
        '</li>'
    )


def render_presentations(data: dict[str, Any]) -> str:
    """Return a standalone page section for the parent's shared site shell."""
    records = data["records"]
    counts = data["counts"]
    years = data["years"]
    year_options = "".join(f'<option value="{year}">{year}</option>' for year in years)
    year_links = "".join(
        f'<a href="#pr-year-{year}" data-pr-year-link="{year}">{year}</a>' for year in years
    )
    groups = []
    number = len(records)
    for year in years:
        year_records = [record for record in records if record["year"] == year]
        articles = []
        for record in year_records:
            articles.append(_render_record(record, number))
            number -= 1
        groups.append(
            f'<section class="pr-year-group" id="pr-year-{year}" data-pr-year="{year}" '
            f'aria-labelledby="pr-heading-{year}">'
            f'<h2 id="pr-heading-{year}">{year}<span data-pr-year-count>{len(year_records)}</span></h2>'
            f'<ol class="pr-records" aria-label="{year} presentations">{"".join(articles)}</ol>'
            '</section>'
        )
    return f'''<section class="pr-page" id="presentations-page" aria-labelledby="pr-page-title" data-pr-total="{counts['all']}">
  <header class="pr-intro">
    <h1 id="pr-page-title">Presentations</h1>
    <div class="pr-totals" aria-label="Presentation totals">
      <span><strong>{counts['all']}</strong> presentations</span>
      <span><strong>{counts['invited']}</strong> invited talks</span>
    </div>
  </header>
  <div class="pr-controls" hidden>
    <div class="pr-search-row">
      <label class="pr-search-field" for="pr-search">
        <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="10.5" cy="10.5" r="6.5"></circle><path d="m16 16 4.5 4.5"></path></svg>
        <span class="sr-only">Search presentations</span>
        <input id="pr-search" type="search" placeholder="Search title, author, conference…" autocomplete="off" aria-controls="pr-results">
      </label>
      <button type="button" class="pr-reset" disabled>Reset filters <span aria-hidden="true">↺</span></button>
    </div>
    <div class="pr-filter-row">
      <div class="pr-select-field">
        <label for="pr-scope-filter">Conference scope</label>
        <select id="pr-scope-filter" aria-controls="pr-results"><option value="all">All presentations</option><option value="domestic">Domestic</option><option value="international">International</option></select>
      </div>
      <div class="pr-select-field">
        <label for="pr-year-filter">Year</label>
        <select id="pr-year-filter" aria-controls="pr-results"><option value="all">All years</option>{year_options}</select>
      </div>
      <div class="pr-select-field">
        <label for="pr-invited-filter">Invitation</label>
        <select id="pr-invited-filter" aria-controls="pr-results"><option value="all">All presentations</option><option value="invited">Invited talks</option></select>
      </div>
    </div>
  </div>
  <div class="pr-results-heading">
    <p class="pr-status" role="status" aria-live="polite" aria-atomic="true"><strong>{counts['all']}</strong> presentations</p>
    <p class="pr-scope-note">セミナー・勉強会・展示会講演などは All presentations に含みます。</p>
  </div>
  <div class="pr-layout">
    <aside class="pr-year-sidebar" aria-label="Presentation years">
      <span>YEAR</span><nav aria-label="Jump to presentation year">{year_links}</nav>
    </aside>
    <div id="pr-results" class="pr-results">{''.join(groups)}
      <div class="pr-empty" hidden>
        <h2>No presentations found</h2>
        <p>検索語や絞り込み条件を変更してください。</p>
        <button type="button" class="pr-empty-reset">Reset filters</button>
      </div>
    </div>
  </div>
</section>'''
