"""Render the publication chart without changing the source records.

The browser renderer in publication-chart.js intentionally uses the same HTML.
Each rectangular unit represents one record. Known calendar years are shown in
ascending order; in-press and undated records stay in separate, clickable groups.
Pass the full ``years`` list when rendering a filtered subset to keep the axis
stable. First OR corresponding author is one category, never counted twice.
"""

from __future__ import annotations

from html import escape
from math import ceil, floor, log10


def _year(value):
    if isinstance(value, bool):
        return None
    text = str(value)
    return int(text) if text.isascii() and text.isdigit() and 0 < int(text) < 10000 else None


def year_key(record):
    year = _year(record.get("year"))
    if year is not None:
        return str(year)
    return "in-press" if record.get("year_label") == "In press" else "undated"


def _lead(record):
    return record.get("first_author") is True or record.get("corresponding") is True


def _unknown(record):
    return not _lead(record) and not (
        record.get("first_author") is False and record.get("corresponding") is False
    )


def _units(records):
    ordered = [record for record in records if _lead(record)] + [record for record in records if not _lead(record)]
    return "".join(
        '<span class="publication-square-unit publication-square-'
        + ("lead" if _lead(record) else "other")
        + '" data-publication-id="' + escape(str(record.get("id", "")), quote=True) + '"></span>'
        for record in ordered
    )


def _description(label, records, active):
    lead = sum(_lead(record) for record in records)
    unknown = sum(_unknown(record) for record in records)
    other = len(records) - lead - unknown
    parts = [f"{label}: {len(records)} publications", f"{lead} first or corresponding author", f"{other} coauthor"]
    if unknown:
        parts.append(f"{unknown} authorship not recorded")
    return "; ".join(parts) + (". Clear year filter." if active else ". Filter to this group.")


def _scale(maximum):
    raw_step = max(1, ceil(maximum / 4))
    magnitude = 10 ** floor(log10(raw_step))
    step = next(value * magnitude for value in (1, 2, 5, 10) if value * magnitude >= raw_step)
    limit = max(1, ceil(maximum / step)) * step
    return limit, list(range(0, limit + 1, step))


def render_publication_chart(records, *, years=None, selected_year="all"):
    """Return accessible chart HTML; the surrounding app handles button clicks.

    Year/group buttons expose ``data-year`` and ``aria-pressed``. No title,
    library, event handler, global ID, source modification, or network request
    is introduced here. Include publication-chart.css alongside the result.
    """
    records = list(records)
    candidates = years if years is not None else [record.get("year") for record in records]
    numeric_years = sorted({year for value in candidates if (year := _year(value)) is not None})
    # Include a newly supplied record even if the caller's year list is stale.
    numeric_years = sorted(set(numeric_years) | {int(year_key(record)) for record in records if year_key(record).isdigit()})
    if numeric_years:
        numeric_years = list(range(numeric_years[0], numeric_years[-1] + 1))
    groups = {str(year): [] for year in numeric_years}
    groups.update({"in-press": [], "undated": []})
    for record in records:
        groups[year_key(record)].append(record)
    maximum = max((len(groups[str(year)]) for year in numeric_years), default=0)
    limit, ticks = _scale(maximum)
    columns = []
    for year in numeric_years:
        key = str(year)
        group = groups[key]
        active = str(selected_year) == key
        description = escape(_description(key, group, active), quote=True)
        columns.append(
            f'<button type="button" class="publication-square-column{" is-selected" if active else ""}" '
            f'data-year="{key}" aria-label="{description}" title="{description}" aria-pressed="{str(active).lower()}">'
            '<span class="publication-square-plot" aria-hidden="true">'
            f'<span class="publication-square-stack">{_units(group)}</span></span>'
            f'<span class="publication-square-year">{key}</span></button>'
        )
    tick_html = ''.join(f'<span class="publication-square-y-tick" style="--publication-tick:{tick}">{tick}</span>' for tick in ticks)
    grid_html = ''.join(f'<i class="publication-square-grid-line" style="--publication-tick:{tick}"></i>' for tick in ticks)
    chart = (
        '<span class="publication-square-axis-title" aria-hidden="true">Number of publications</span>'
        '<div class="publication-square-scroll">'
        f'<div class="publication-square-axis-panel" style="--publication-year-count:{len(numeric_years)};--publication-scale:{limit}">'
        f'<div class="publication-square-y-axis" aria-hidden="true">{tick_html}</div>'
        f'<div class="publication-square-graph"><div class="publication-square-grid" aria-hidden="true">{grid_html}</div>'
        '<div class="publication-square-columns">' + "".join(columns) + '</div></div></div></div>'
    ) if numeric_years else '<p class="publication-square-empty">No dated publications in this selection.</p>'
    additional = []
    for key, label in (("in-press", "In press"), ("undated", "Year not specified")):
        group = groups[key]
        if not group:
            continue
        active = str(selected_year) == key
        description = escape(_description(label, group, active), quote=True)
        additional.append(
            f'<button type="button" class="publication-square-additional{" is-selected" if active else ""}" '
            f'data-year="{key}" aria-label="{description}" title="{description}" aria-pressed="{str(active).lower()}">'
            f'<span>{label} <span class="publication-square-additional-count">{len(group)}</span></span>'
            f'<span class="publication-square-additional-units" aria-hidden="true">{_units(group)}</span></button>'
        )
    additional_html = '<div class="publication-square-additional-groups">' + "".join(additional) + '</div>' if additional else ""
    unknown = sum(_unknown(record) for record in records)
    note = f'<p class="publication-square-note">Authorship not recorded for {unknown}; shown in gray.</p>' if unknown else ""
    return (
        '<div class="publication-square-chart" role="group" aria-label="Publication counts by year. One block represents one publication.">'
        + '<div class="publication-square-main">'
        + '<div class="publication-square-legend"><span class="publication-square-key"><i class="publication-square-swatch publication-square-lead" aria-hidden="true"></i>First or corresponding</span>'
        + '<span class="publication-square-key"><i class="publication-square-swatch publication-square-other" aria-hidden="true"></i>Coauthor</span></div>'
        + chart + '</div><div class="publication-square-footer"><span class="publication-square-unit-note">1 block = 1 publication</span>'
        + additional_html + '</div>'
        + note + '</div>'
    )
