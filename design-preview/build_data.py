#!/usr/bin/env python3
"""Build a disposable public-site payload without editing the source database.

Usage: python build_data.py --source SITE --output publications.json --commit SHA
Requires PyYAML. No network or private repository is read.
Schema v1: source, counts, records (stable IDs, original citation HTML, optional
split title/authors/bibliography, links, dates, existing metrics, search text),
legacy_sections (original headings/Markdown and rendered list HTML).
Null means unknown. Date.value is displayable; original_value preserves the
master value even when display is N/A. display_fallback requires citation_html.
The output is a generated view, never an additional source of truth.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import unicodedata
from collections import Counter
from dataclasses import dataclass, field
from datetime import date
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

import yaml


OWNER_ID = "tomoyuki-hirano"
OWNER_NAMES = ("Tomoyuki Hirano", "平野 知之")
DATE_FIELDS = ("submitted", "accepted", "published_online")
MONTHS = ("", "January", "February", "March", "April", "May", "June",
          "July", "August", "September", "October", "November", "December")
VOID_TAGS = {"br", "hr", "img", "input", "meta", "link", "wbr"}


@dataclass
class Node:
    tag: str = ""
    opening: str = ""
    children: list[Any] = field(default_factory=list)

    @property
    def text(self) -> str:
        return "".join(child if isinstance(child, str) else child.text
                       for child in self.children)


class Fragment(HTMLParser):
    """Small HTML fragment tree that preserves source start tags."""

    def __init__(self, value: str):
        super().__init__(convert_charrefs=True)
        self.root = Node()
        self.stack = [self.root]
        self.feed(value)
        self.close()

    def handle_starttag(self, tag, attrs):
        node = Node(tag, self.get_starttag_text())
        self.stack[-1].children.append(node)
        if tag not in VOID_TAGS:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.stack[-1].children.append(Node(tag, self.get_starttag_text()))

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                break

    def handle_data(self, data):
        self.stack[-1].children.append(data)


def plain(value: str) -> str:
    return Fragment(value).root.text


def rendered_inline(value: str) -> str:
    # Kramdown consumes escaped literal asterisks in the existing citations.
    return value.replace(r"\*", "*")


def normalized(value: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKC", value).casefold()
                   if c.isalnum())


def normalized_map(value: str):
    chars, positions = [], []
    for index, character in enumerate(value):
        for c in unicodedata.normalize("NFKC", character).casefold():
            if c.isalnum():
                chars.append(c)
                positions.append(index)
    return "".join(chars), positions


def html_slice(root: Node, start: int, end: int) -> str:
    cursor = 0

    def visit(node):
        nonlocal cursor
        if isinstance(node, str):
            left, right = max(start - cursor, 0), min(end - cursor, len(node))
            cursor += len(node)
            return html.escape(node[left:right], quote=False) if right > left else ""
        content = "".join(visit(child) for child in node.children)
        if not node.tag:
            return content
        if not content:
            return ""
        return node.opening + content + "</" + node.tag + ">"

    return visit(root)


def trim_span(text: str, start: int, end: int, separators: str = " \t\r\n,，"):
    while start < end and text[start] in separators:
        start += 1
    while end > start and text[end - 1] in separators:
        end -= 1
    return start, end


def split_at(root: Node, title_start: int, title_end: int):
    text = root.text
    a = trim_span(text, 0, title_start)
    t = trim_span(text, title_start, title_end)
    b = trim_span(text, title_end, len(text))
    if not all(right > left for left, right in (a, t, b)):
        return None
    return {
        "authors_html": html_slice(root, *a),
        "title_html": html_slice(root, *t),
        "bibliography_html": html_slice(root, *b),
        "title": text[t[0]:t[1]],
    }


def split_master(citation: str, title: str, journal: str):
    root = Fragment(citation).root
    text, positions = normalized_map(root.text)
    target = normalized(title)
    if len(target) < 12 or text.count(target) != 1:
        return None
    begin = text.index(target)
    start = positions[begin]
    journal_target = normalized(journal)
    remainder = text[begin + len(target):]
    if not journal_target or remainder.count(journal_target) != 1:
        return None
    journal_begin = begin + len(target) + remainder.index(journal_target)
    end = positions[journal_begin]
    # Use the explicit journal boundary, preserving citation title extensions
    # that are absent from the structured master without changing either source.
    return split_at(root, start, end)


def all_nodes(root: Node):
    for child in root.children:
        if isinstance(child, Node):
            yield child
            yield from all_nodes(child)


def author_pattern(names: set[str]) -> re.Pattern:
    alternatives = [re.escape(name).replace(r"\ ", r"\s+")
                    for name in sorted(names, key=len, reverse=True) if name]
    return re.compile(r"\s*(?:and\s+)?(?:" + "|".join(alternatives)
                      + r")\s*\*?\s*[,，]\s*", re.IGNORECASE)


def split_supplement(citation: str, journals: set[str], names: set[str], author_re):
    """Split only explicit journal names and an unambiguous author-list boundary."""
    root = Fragment(citation).root
    text = root.text
    matches = []
    for journal in journals:
        index = text.rfind(journal)
        if index >= 0 and re.search(r"(?:19|20)\d{2}", text[index + len(journal):]):
            matches.append((index, journal))
    if not matches:
        return None, None
    journal_start, journal = max(matches, key=lambda item: item[0])
    prefix = text[:journal_start]

    # An explicit final 'and <known author>,' is an exact textual boundary,
    # even if an earlier co-author is absent from the person dictionary.
    final_author_ends = []
    for name in names:
        pattern = r"(?:,\s*|\s+)and\s+" + re.escape(name) + r"\s*\*?\s*,\s*"
        final_author_ends.extend(match.end() for match in re.finditer(pattern, prefix, re.I))
    if len(set(final_author_ends)) == 1:
        start = final_author_ends[0]
    else:
        start, consumed = 0, 0
        while match := author_re.match(prefix, start):
            start = match.end()
            consumed += 1
        if not consumed:
            return None, journal
        # Do not mistake an unrecognised Latin author name for an English title.
        remainder = prefix[start:].lstrip()
        first_chunk = re.split(r"[,，]", remainder, maxsplit=1)[0].strip()
        if re.fullmatch(r"[A-Z][\w’'-]+(?:\s+[A-Z][\w’'-]+){1,4}", first_chunk):
            return None, journal
    if len(prefix[start:].strip(" ,，")) < 8:
        return None, journal
    return split_at(root, start, journal_start), journal


def parse_citations(markdown: str):
    result = []
    for match in re.finditer(
        r'^1\.\s+<span(?P<attrs>[^>]*\bclass="publication-citation"[^>]*)>'
        r'(?P<inner>.*)</span>\s*\{%\s*include\s+publication-links\.html\s+'
        r'id="(?P<include>[^"]+)"\s*%\}\s*$', markdown, re.MULTILINE):
        id_match = re.search(r'\bdata-publication-id="([^"]+)"', match.group("attrs"))
        if not id_match or id_match.group(1) != match.group("include"):
            raise ValueError("Citation/include stable ID mismatch")
        result.append((id_match.group(1), match.group("inner")))
    if not result:
        raise ValueError("No existing publication citations found")
    if len({item[0] for item in result}) != len(result):
        raise ValueError("Duplicate citation IDs")
    return result


def parse_legacy(markdown: str):
    result = []
    for match in re.finditer(r'<h2\b[^>]*>(?P<title>.*?)</h2>(?P<body>.*?)(?=<h2\b|\Z)',
                            markdown, re.DOTALL):
        title = plain(match.group("title"))
        if not (title.startswith("Book Chapters") or title == "Others"):
            continue
        body = match.group("body").strip()
        items = re.findall(r'^1\.\s+(.*)$', body, re.MULTILINE)
        if not items:
            raise ValueError("Unrecognised legacy list: " + title)
        result.append({"title": title, "markdown": body,
                       "html": '<ol reversed="reversed">' + "".join(
                           "<li>" + rendered_inline(item) + "</li>" for item in items
                       ) + "</ol>"})
    return result


def valid_date(value):
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return False
    try:
        date.fromisoformat(value)
        return True
    except ValueError:
        return False


def build_dates(master, review):
    source_dates = master.get("dates", {})
    reviews = review.get("fields", {})
    chronology = set()
    for earlier, later in (("submitted", "accepted"), ("accepted", "published_online")):
        a, b = source_dates.get(earlier), source_dates.get(later)
        if valid_date(a) and valid_date(b) and a > b:
            chronology.update((earlier, later))
    result = {}
    for name in DATE_FIELDS:
        original = source_dates.get(name)
        field_review = reviews.get(name, {})
        review_status = field_review.get("status")
        checking = (review_status in {"conflict", "pending"} or name in chronology
                    or bool(original and not valid_date(original))
                    or (review_status == "verified" and field_review.get("checked_value") != original))
        value = original if not checking and valid_date(original) else None
        status = ("conflict" if checking else
                  "verified" if value and review_status == "verified" else
                  "owner_supplied" if value else "unavailable")
        display = "N/A"
        if value:
            parsed = date.fromisoformat(value)
            display = f"{MONTHS[parsed.month]} {parsed.day:02d}, {parsed.year}"
        result[name] = {"value": value, "original_value": original, "display": display,
                        "status": status, "status_label": "確認中" if checking else None,
                        "source_url": review.get("source_url"),
                        "checked_on": review.get("checked_on")}
    return result


def access_links(access):
    links = []
    doi = access.get("doi")
    if access.get("is_preprint"):
        if access.get("preprint_url"):
            links.append({"kind": "preprint", "label": "Preprint", "url": access["preprint_url"],
                          "status": None, "license": None})
    elif doi:
        oa = access.get("publisher_oa") is True
        links.append({"kind": "publisher", "label": "Publisher (OA)" if oa else "Publisher",
                      "url": "https://doi.org/" + doi, "status": "open" if oa else None,
                      "license": access.get("publisher_license") if oa else None,
                      "license_url": access.get("publisher_license_url") if oa else None})
    if access.get("hir_url"):
        links.append({"kind": "repository", "label": "Repository", "url": access["hir_url"],
                      "status": access.get("hir_status"), "license": None})
    if access.get("chemrxiv_url"):
        links.append({"kind": "preprint", "label": "Preprint", "url": access["chemrxiv_url"],
                      "status": None, "license": None})
    for link in links:
        if not re.match(r"^https?://", link["url"]):
            raise ValueError("Unexpected public link scheme: " + link["url"])
    return links


def supplemental_roles(authors_html):
    if not authors_html:
        return None, None
    text = plain(authors_html)
    owner = r"(?:Tomoyuki\s+Hirano|平野\s*知之)"
    if not re.search(owner, text):
        return None, None
    return bool(re.match(r"\s*" + owner, text)), bool(re.search(owner + r"\s*\*", text))


def printed_year(citation, kind):
    text = plain(citation).strip()
    if re.search(r"\bin\s+press\.?\s*$", text, re.I):
        return None, "In press"
    pattern = (r"\b((?:19|20)\d{2})-\d{2}-\d{2}\s*\(v\d+\)\.?$"
               if kind == "preprint" else r"\b((?:19|20)\d{2})\.?(?:\s+Invited)?$")
    match = re.search(pattern, text)
    return (int(match.group(1)), match.group(1)) if match else (None, "Year not specified")


def build_payload(source: Path, commit):
    source = source.resolve()
    loaded = {}

    def read(path):
        full = source / path
        if not full.is_relative_to(source) or not full.is_file():
            raise ValueError("Missing public source: " + str(path))
        data = full.read_bytes()
        loaded[str(path)] = hashlib.sha256(data).hexdigest()
        return data.decode("utf-8")

    def yml(path):
        return yaml.safe_load(read(path))

    master = {}
    for path in sorted((source / "_data/publications").glob("*.yml")):
        for record in yml(path.relative_to(source))["records"]:
            if record["id"] in master:
                raise ValueError("Duplicate master ID: " + record["id"])
            master[record["id"]] = record
    people = yml("_data/people.yml")
    names = set(OWNER_NAMES)
    for person in people["records"]:
        names.update(x for x in [person.get("name"), person.get("name_ja"), *person.get("aliases", [])] if x)
    # Public presentation names help identify exact Japanese author-list tokens.
    for path in sorted((source / "_data/presentations").glob("*.yml")):
        for item in yml(path.relative_to(source)).get("records", []):
            if item.get("public") is not False:
                names.update(author["name"] for author in item.get("display", {}).get("authors", []))
    author_re = author_pattern(names)
    access = yml("_data/publication_access.yml")["records"]
    reviews = yml("_data/publication_date_reviews.yml")["records"]
    journal_data = yml("_data/journals.yml")
    journals_by_name = {record["journal"]: record for record in journal_data["records"]}
    context = journal_data.get("metrics_context", {})
    markdown = read("publications.md")
    citations = parse_citations(markdown)
    if set(master) != {item[0] for item in citations if item[0].startswith("pub-")}:
        raise ValueError("Journal master and existing citation IDs do not agree")
    known_journals = set(journals_by_name)
    for _, raw in citations:
        strongs = [node for node in all_nodes(Fragment(rendered_inline(raw)).root)
                   if node.tag == "strong" and "text-decoration" not in node.opening]
        for node in reversed(strongs):
            value = node.text.strip()
            if value and not any(normalized(value.rstrip("*")) == normalized(name) for name in names):
                known_journals.add(value)
                break

    records = []
    for stable_id, raw in citations:
        citation = rendered_inline(raw)
        record = master.get(stable_id)
        kind = "journal_article" if record else "review" if stable_id.startswith("review-") else "preprint"
        year, year_label = printed_year(citation, kind)
        if record:
            split = split_master(citation, record["title"], record["journal"])
            journal = record["journal"]
            classification = record.get("classification", {})
            first_author = classification.get("hirano_first_author")
            corresponding = classification.get("hirano_corresponding")
        else:
            split, journal = split_supplement(citation, known_journals, names, author_re)
            classification = {}
            first_author, corresponding = supplemental_roles(split["authors_html"] if split else None)
        metric = journals_by_name.get(journal, {}) if record else {}
        quartile = metric.get("jcr_quartile")
        data = {
            "id": stable_id,
            "paper_id": record.get("paper_id") if record else None,
            "hp_no": record.get("hp_no") if record else None,
            "type": kind,
            "year": year,
            "source_year": record.get("year") if record else year,
            "year_label": year_label,
            "status": record.get("status") if record else ("preprint" if kind == "preprint" else "published"),
            "title": split["title"] if split else (record["title"] if record else plain(citation)),
            "title_html": split["title_html"] if split else None,
            "authors_html": split["authors_html"] if split else None,
            "citation_html": citation,
            "citation_source": raw,
            "bibliography_html": split["bibliography_html"] if split else None,
            "journal": journal,
            "first_author": first_author,
            "corresponding": corresponding,
            "display_fallback": split is None,
            "doi": access.get(stable_id, {}).get("doi"),
            "links": access_links(access.get(stable_id, {})),
            "dates": build_dates(record, reviews.get(stable_id, {})) if record else None,
            "metrics": {"impact_factor": metric.get("impact_factor"), "jcr_quartile": quartile,
                        "q1": quartile == "Q1" if quartile else None,
                        "top10_percent": classification.get("top10_percent"),
                        "checked_month": context.get("checked_month"),
                        "metric_year": context.get("metric_year"),
                        "jcr_release_year": context.get("jcr_release_year")},
            "search_text": " ".join(filter(None, [stable_id, record.get("paper_id") if record else None,
                                                  plain(citation), journal, access.get(stable_id, {}).get("doi")]))
        }
        records.append(data)
    type_counts = Counter(record["type"] for record in records)
    payload = {
        "schema_version": 1,
        "source": {"kind": "derived_public_database", "commit": commit,
                   "repository": "tomoyukihirano/tomoyukihirano.github.io",
                   "files_sha256": loaded},
        "counts": {"journal_articles": type_counts["journal_article"], "reviews": type_counts["review"],
                   "preprints": type_counts["preprint"], "total": len(records)},
        "records": records,
        "legacy_sections": parse_legacy(markdown),
    }
    validate_payload(payload, master, citations, access)
    # Prove that reading and generating this view did not alter source files.
    for path, digest in loaded.items():
        if hashlib.sha256((source / path).read_bytes()).hexdigest() != digest:
            raise ValueError("Source changed during generation: " + path)
    return payload


def validate_payload(payload, master, citations, access):
    records = payload["records"]
    assert [record["id"] for record in records] == [item[0] for item in citations]
    assert len({record["id"] for record in records}) == len(records)
    assert payload["counts"]["journal_articles"] == len(master)
    for record, (_, citation) in zip(records, citations):
        assert record["citation_source"] == citation
        assert record["citation_html"] == rendered_inline(citation)
        original_access = access.get(record["id"], {})
        actual_urls = [link["url"] for link in record["links"]]
        expected_urls = []
        if original_access.get("is_preprint"):
            if original_access.get("preprint_url"):
                expected_urls.append(original_access["preprint_url"])
        elif original_access.get("doi"):
            expected_urls.append("https://doi.org/" + original_access["doi"])
        expected_urls.extend(original_access[key] for key in ("hir_url", "chemrxiv_url") if original_access.get(key))
        assert actual_urls == expected_urls, record["id"]
        assert "hir_release_date" not in record and not any("Scheduled" in link["label"] for link in record["links"])
        if record["display_fallback"]:
            assert record["authors_html"] is None
        else:
            for key in ("authors_html", "title_html", "bibliography_html"):
                assert plain(record[key]).strip(), (record["id"], key)
            assert normalized("".join(plain(record[key]) for key in (
                "authors_html", "title_html", "bibliography_html"
            ))) == normalized(plain(record["citation_html"])), record["id"]
            assert normalized(plain(record["bibliography_html"])).startswith(
                normalized(record["journal"])
            ), record["id"]
        if record["dates"]:
            for item in record["dates"].values():
                if item["status"] == "conflict":
                    assert item["value"] is None and item["display"] == "N/A"
    # No full person dictionary, relationships, or internal classifications are emitted.
    assert "people" not in payload and "id_redirects" not in payload


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--commit", required=True, help="Actual source snapshot commit, for provenance")
    args = parser.parse_args()
    output = args.output.resolve()
    source = args.source.resolve()
    if output.is_relative_to(source):
        raise SystemExit("Output must be outside the authoritative source directory")
    payload = build_payload(source, args.commit)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(output), "counts": payload["counts"],
                      "fallback_ids": [r["id"] for r in payload["records"] if r["display_fallback"]],
                      "validated": "stable IDs, original citations, all existing access URLs, source immutability"},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
