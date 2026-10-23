#!/usr/bin/env python3
"""Build a self-contained, read-only publications preview from the existing site.

Run from any directory:
  python3 design-preview/build.py --source . --output design-preview/dist/index.html
Only the output path is written. The source databases are never changed.
"""
from __future__ import annotations

import argparse
import base64
from collections import Counter
from datetime import date
from html import escape
import json
import mimetypes
from pathlib import Path
import re
import subprocess
import sys
import tempfile

import yaml

HERE = Path(__file__).resolve().parent
KINDS = {"journal_article": "Journal article", "review": "Review", "preprint": "Preprint"}


def e(value):
    return escape(str(value if value is not None else ""), quote=True)


def year_key(record):
    if record["year"] is not None:
        return str(record["year"])
    return "in-press" if record["year_label"] == "In press" else "undated"


def year_label(key):
    return {"in-press": "In press", "undated": "Year not specified"}.get(key, key)


def compact_id(record):
    if record.get("paper_id"):
        return record["paper_id"]
    return "R" + record["id"].rsplit("-", 1)[1][-3:] if record["type"] == "review" else "Preprint"


def metric_note(metric, kind):
    checked = metric.get("checked_month")
    if checked and re.fullmatch(r"\d{4}-\d{2}", checked):
        checked_text = "checked " + date.fromisoformat(checked + "-01").strftime("%B %Y")
    else:
        checked_text = "check month not recorded"
    year = metric.get("metric_year" if kind == "IF" else "jcr_release_year")
    label = "Metric year" if kind == "IF" else "JCR edition"
    return f'Registered {"impact factor" if kind == "IF" else "JCR quartile"}; {checked_text}. {label} {year if year is not None else "not confirmed"}.'


def apply_presentation(payload, source, path):
    config = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    settings = config.get("records", {})
    if not isinstance(settings, dict):
        raise ValueError("presentation.yml records must be an ID-keyed mapping")
    ids = {record["id"] for record in payload["records"]}
    unknown = set(settings) - ids
    if unknown:
        raise ValueError(f"Unknown publication IDs in presentation.yml: {sorted(unknown)}")
    for record in payload["records"]:
        item = settings.get(record["id"]) or {}
        if not item:
            continue
        forbidden = set(item) - {"thumbnail", "thumbnail_alt", "summary", "topics", "selected"}
        if forbidden:
            raise ValueError(f"Only presentation fields are allowed in {record['id']}: {sorted(forbidden)}")
        display = {key: item[key] for key in ("summary", "topics", "selected") if key in item}
        if "topics" in display and (not isinstance(display["topics"], list) or not all(isinstance(x, str) for x in display["topics"])):
            raise ValueError("topics must be a list of strings")
        if item.get("thumbnail"):
            image = (source / item["thumbnail"]).resolve()
            if not image.is_relative_to(source):
                raise ValueError("Thumbnail must be inside the source checkout")
            mime = mimetypes.guess_type(image.name)[0]
            if mime not in {"image/png", "image/jpeg", "image/webp", "image/avif", "image/gif"}:
                raise ValueError("Use PNG, JPEG, WebP, AVIF or GIF thumbnails")
            if not item.get("thumbnail_alt"):
                raise ValueError("A meaningful thumbnail_alt is required for every thumbnail")
            display["thumbnail_data"] = "data:" + mime + ";base64," + base64.b64encode(image.read_bytes()).decode("ascii")
            display["thumbnail_alt"] = str(item["thumbnail_alt"])
        record["presentation"] = display


def render_record(record):
    role = "First & corresponding" if record["first_author"] and record["corresponding"] else "First author" if record["first_author"] else "Corresponding author" if record["corresponding"] else ""
    presentation = record.get("presentation", {})
    tile = (f'<img src="{e(presentation["thumbnail_data"])}" alt="{e(presentation.get("thumbnail_alt"))}" loading="lazy">' if presentation.get("thumbnail_data") else
            f'<div class="paper-tile" aria-hidden="true"><span class="tile-id">{e(compact_id(record))}</span><span class="tile-journal">{e(record["journal"] or KINDS[record["type"]])}</span><span class="tile-kind">{e(KINDS[record["type"]])}</span></div>')
    if record["display_fallback"]:
        body = f'<h3 class="sr-only">{e(compact_id(record))}</h3><p class="fallback-citation">{record["citation_html"]}</p>'
    else:
        body = f'<h3>{record["title_html"] or e(record["title"])}</h3><p class="authors">{record["authors_html"] or ""}</p><p class="bibliography">{record["bibliography_html"] or ""}</p>'
    links = []
    for link in record["links"]:
        cls = " preprint" if link["kind"] == "preprint" else " oa" if link["kind"] == "publisher" and link.get("status") == "open" else ""
        title = f' title="{e(link["license"])}"' if link.get("license") else ""
        links.append(f'<a class="paper-link{cls}" href="{e(link["url"])}" target="_blank" rel="noopener"{title}>{e(link["label"])} <span aria-hidden="true">↗</span></a>')
    metric = record["metrics"]
    badges = []
    if metric.get("impact_factor") is not None:
        badges.append(f'<span class="metric" title="{e(metric_note(metric, "IF"))}">IF {e(metric["impact_factor"])}</span>')
    if metric.get("jcr_quartile"):
        badges.append(f'<span class="metric" title="{e(metric_note(metric, "JCR"))}">{e(metric["jcr_quartile"])}</span>')
    if metric.get("top10_percent") is True:
        badges.append('<span class="metric top10" title="Existing article citation-ranking classification. A qualifying subject category is sufficient.">Top 10%</span>')
    metrics = '<span class="metrics" aria-label="Existing evaluation data">' + "".join(badges) + '</span>' if badges else ""
    dates = ""
    if record["dates"]:
        parts = []
        for key, label in (("submitted", "Submitted"), ("accepted", "Accepted"), ("published_online", "Published online")):
            date = record["dates"][key]
            note = '<span class="date-note">Under review</span>' if date["status"] == "conflict" else ""
            parts.append(f'<div><dt>{label}</dt><dd>{e(date["display"])}{note}</dd></div>')
        dates = '<dl class="date-grid">' + ''.join(parts) + '</dl>'
    role_html = f'<span class="role-dot" aria-hidden="true">·</span><span class="author-role">{e(role)}</span>' if role else ""
    summary = f'<p class="paper-summary">{e(presentation["summary"])}</p>' if presentation.get("summary") else ""
    topics = '<div class="topics">' + ''.join(f'<span class="topic">{e(topic)}</span>' for topic in presentation["topics"]) + '</div>' if presentation.get("topics") else ""
    doi = f'<p class="doi-line">DOI: {e(record["doi"])}</p>' if record.get("doi") else ""
    return (f'<article class="publication" id="{e(record["id"])}" data-publication-id="{e(record["id"])}">'
            f'<div class="publication-art">{tile}</div><div class="publication-body">'
            f'<div class="paper-topline"><span class="type-badge type-{e(record["type"])}">{e(KINDS[record["type"]])}</span>{role_html}<a class="paper-id" href="#{e(record["id"])}" title="Permanent publication identifier">{e(compact_id(record))}</a></div>'
            f'{body}{summary}{topics}<div class="paper-actions">{"".join(links)}{metrics}</div>'
            f'<details class="publication-details"><summary>{"Dates & citation" if dates else "Full citation"}</summary><div class="detail-panel">{dates}<h4>Original citation</h4><p class="citation">{record["citation_html"]}</p>{doi}</div></details>'
            '</div></article>')


def build(source, output, commit):
    if commit is None:
        if not (source / ".git").exists():
            raise ValueError("For a source snapshot without .git, pass the actual source commit with --commit")
        commit = subprocess.check_output(["git", "-C", str(source), "rev-parse", "HEAD"], text=True).strip()
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("--commit must be the complete source commit SHA")
    protected = (source / "_data").resolve()
    if output.is_relative_to(protected) or output in {source / name for name in ("publications.md", "presentations.md", "index.md", "about.md", "information.md", "supports-grants.md", "award.md")}:
        raise ValueError("The output must not overwrite authoritative data or pages")
    with tempfile.TemporaryDirectory(prefix="publication-preview-") as temp:
        json_path = Path(temp) / "publications.json"
        subprocess.run([sys.executable, str(HERE / "build_data.py"), "--source", str(source), "--output", str(json_path), "--commit", commit], check=True)
        payload = json.loads(json_path.read_text(encoding="utf-8"))
    apply_presentation(payload, source, HERE / "presentation.yml")
    records = payload["records"]
    keys = sorted({year_key(record) for record in records}, key=lambda key: (0, 0) if key == "in-press" else (2, 0) if key == "undated" else (1, -int(key)))
    counts = Counter(year_key(record) for record in records)
    initial_list = ''.join(f'<section class="year-group" id="year-{e(key)}" aria-labelledby="heading-{e(key)}"><h2 id="heading-{e(key)}">{e(year_label(key))}<span>{counts[key]}</span></h2>' + ''.join(render_record(record) for record in records if year_key(record) == key) + '</section>' for key in keys)
    years = sorted(int(key) for key in keys if key not in {"in-press", "undated"})
    maximum = max((counts[str(year)] for year in years), default=1)
    chart = ''.join(f'<button type="button" class="chart-column" data-year="{year}" aria-label="Filter to {year}: {counts[str(year)]} publications" aria-pressed="false"><span class="chart-count">{counts[str(year)]}</span><span class="chart-bar" style="height:{counts[str(year)]/maximum*76:.2f}%"></span><span class="chart-year">{year}</span></button>' for year in years)
    legacy = ''.join(f'<details class="legacy-section" id="{e("book-chapters-3-in-total" if section["title"].startswith("Book Chapters") else "others")}"><summary>{e("Book Chapters" if section["title"].startswith("Book Chapters") else section["title"])}</summary><div class="legacy-content">{section["html"]}</div></details>' for section in payload["legacy_sections"])
    checked_months = sorted({record["metrics"].get("checked_month") for record in records if record["metrics"].get("checked_month")})
    metrics_guide = "Existing registered values. "
    if checked_months:
        metrics_guide += "Checked: " + ", ".join(date.fromisoformat(month + "-01").strftime("%B %Y") for month in checked_months) + ". "
    metrics_guide += "See each label for the recorded metric year and JCR edition."
    totals = payload["counts"]
    replacements = {
        "__STYLES__": (HERE / "styles.css").read_text(encoding="utf-8"),
        "__SCRIPT__": (HERE / "app.js").read_text(encoding="utf-8"),
        "__DATA__": json.dumps(payload, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026"),
        "__TOTALS__": ''.join(f'<span><strong>{totals[key]}</strong> {label}</span>' for key, label in (("journal_articles", "journal articles"), ("reviews", "reviews"), ("preprints", "preprint"))),
        "__CHART__": chart,
        "__IN_PRESS_NOTE__": f'+ {counts["in-press"]} in press' if counts["in-press"] else "",
        "__YEAR_OPTIONS__": ''.join(f'<option value="{e(key)}">{e(year_label(key))}</option>' for key in keys),
        "__YEAR_NAV__": ''.join(f'<a href="#year-{e(key)}">{e(year_label(key))}</a>' for key in keys),
        "__RESULT_COUNT__": f'<strong>{totals["total"]}</strong> of {totals["total"]} publications',
        "__INITIAL_LIST__": initial_list,
        "__LEGACY_SECTIONS__": legacy,
        "__BUILD_DATE__": date.today().strftime("%d %B %Y"),
        "__METRICS_GUIDE__": e(metrics_guide),
    }
    html = (HERE / "template.html").read_text(encoding="utf-8")
    for marker, value in replacements.items():
        html = html.replace(marker, value)
    if re.search(r"__[A-Z_]+__", html):
        raise ValueError("Unresolved template markers")
    if "Scheduled: January 27, 2027" in html:
        raise ValueError("Unexpected repository scheduled date")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(html, encoding="utf-8")
    print(json.dumps({"output": str(output), "bytes": output.stat().st_size, "counts": totals, "year_counts": dict(counts), "first_author": sum(record["first_author"] is True for record in records), "first_or_corresponding": sum(record["first_author"] is True or record["corresponding"] is True for record in records)}, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=HERE.parent)
    parser.add_argument("--output", type=Path, default=HERE / "dist" / "index.html")
    parser.add_argument("--commit", help="Actual source commit; otherwise use the supplied checkout's HEAD")
    args = parser.parse_args()
    build(args.source.resolve(), args.output.resolve(), args.commit)
