#!/usr/bin/env python3
"""Render the existing public Markdown pages for the private design preview.

This module reads the current website sources; it never rewrites them.  The
small renderer supports the mixed Markdown/WordPress HTML used by these five
pages, removes presentation-only wrappers, and preserves their text and links.
Images may be supplied as data URIs through ``assets`` for a portable preview.
"""

from __future__ import annotations

import base64
import html
import mimetypes
import re
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urljoin, urlsplit

import yaml


PUBLIC_BASE = "https://tomoyukihirano.github.io/"
PAGE_SOURCES = {
    "home": ("Home", "index.md"),
    "about": ("About", "about.md"),
    "research": ("Research", "information.md"),
    "grants": ("Grants", "supports-grants.md"),
    "award": ("Award", "award.md"),
}
VOID_TAGS = {"br", "hr", "img", "wbr", "input", "meta", "link"}
ALLOWED_TAGS = {
    "p", "h2", "h3", "h4", "h5", "h6", "ul", "ol", "li", "a", "strong",
    "b", "em", "i", "sub", "sup", "br", "hr", "img", "table", "thead",
    "tbody", "tfoot", "tr", "th", "td", "blockquote", "code", "pre", "wbr",
}
RAW_BLOCK = re.compile(
    r"^</?(?:div|figure|figcaption|p|h[1-6]|ul|ol|li|table|thead|tbody|tfoot|tr|"
    r"th|td|blockquote|pre|hr|img|section|nav)(?:\s|/?>)", re.I
)
LIST_ITEM = re.compile(r"^\s*(?:(?P<bullet>[-*+])|(?P<number>\d+)\.)\s+(?P<body>.+)$")
ATTR_LINE = re.compile(r"^\s*\{:\s*(.*?)\}\s*$")
LIQUID_URL = re.compile(r"\{\{\s*['\"]([^'\"]+)['\"]\s*\|\s*(?:relative_url|absolute_url)\s*\}\}")


@dataclass
class Node:
    tag: str = ""
    attrs: dict[str, str | None] = field(default_factory=dict)
    children: list[Any] = field(default_factory=list)

    @property
    def text(self) -> str:
        return "".join(child if isinstance(child, str) else child.text
                       for child in self.children)


class Fragment(HTMLParser):
    def __init__(self, value: str):
        super().__init__(convert_charrefs=True)
        self.root = Node()
        self.stack = [self.root]
        self.feed(value)
        self.close()

    def handle_starttag(self, tag, attrs):
        node = Node(tag.lower(), dict(attrs))
        self.stack[-1].children.append(node)
        if tag not in VOID_TAGS:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.stack[-1].children.append(Node(tag.lower(), dict(attrs)))

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag.lower():
                del self.stack[index:]
                break

    def handle_data(self, value):
        self.stack[-1].children.append(value)


def _read_page(path: Path) -> tuple[dict, str]:
    text = path.read_text(encoding="utf-8")
    if text.startswith("---\n"):
        _, frontmatter, body = text.split("---", 2)
        return yaml.safe_load(frontmatter) or {}, body.strip()
    return {}, text.strip()


def _inline(value: str) -> str:
    """Keep source inline HTML; the tree is sanitized before rendering."""
    # EDITING.md also permits Markdown's two-space line breaks for new grants.
    value = re.sub(r" {2,}\n", "<br>", value)
    value = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", value)
    value = re.sub(r"(?<!\w)__(.+?)__(?!\w)", r"<strong>\1</strong>", value)
    value = re.sub(
        r"(?<!!)\[([^\]\n]+)\]\(([^\s)]+)\)",
        lambda match: '<a href="' + html.escape(match[2], quote=True) + '">'
        + match[1] + "</a>", value,
    )
    return value.replace(r"\*", "*")


def _markdown_html(body: str) -> str:
    """Render source blocks while retaining embedded HTML and list direction."""
    blocks: list[str] = []
    paragraph: list[str] = []
    items: list[str] = []
    list_tag: str | None = None
    list_reversed = False

    def flush_paragraph():
        if paragraph:
            blocks.append("<p>" + _inline("\n".join(paragraph)) + "</p>")
            paragraph.clear()

    def flush_list():
        nonlocal list_tag, list_reversed
        if items:
            attrs = ' reversed="reversed"' if list_tag == "ol" and list_reversed else ""
            blocks.append(f"<{list_tag}{attrs}>" + "".join(
                "<li>" + _inline(item) + "</li>" for item in items
            ) + f"</{list_tag}>")
            items.clear()
        list_tag, list_reversed = None, False

    for line in body.splitlines():
        stripped = line.strip()
        attr = ATTR_LINE.match(line)
        if attr:
            if "reversed" in attr[1]:
                if items:
                    list_reversed = True
                elif blocks and blocks[-1].startswith("<ol>"):
                    blocks[-1] = blocks[-1].replace("<ol>", '<ol reversed="reversed">', 1)
            continue
        if not stripped:
            flush_paragraph()
            flush_list()
            continue
        item = LIST_ITEM.match(line)
        if item:
            flush_paragraph()
            tag = "ol" if item["number"] else "ul"
            if list_tag and list_tag != tag:
                flush_list()
            list_tag = tag
            items.append(item["body"])
            continue
        heading = re.match(r"^(#{1,6})\s+(.+?)\s*#*\s*$", stripped)
        if heading:
            flush_paragraph()
            flush_list()
            level = max(2, len(heading[1]))
            blocks.append(f"<h{level}>" + _inline(heading[2]) + f"</h{level}>")
            continue
        if RAW_BLOCK.match(stripped) or stripped.startswith("<!--"):
            flush_paragraph()
            flush_list()
            blocks.append(stripped)
            continue
        # Indented continuation lines belong to the preceding list item.
        if items and line.startswith(("  ", "\t")):
            items[-1] += "\n" + line.lstrip()
            continue
        flush_list()
        paragraph.append(line.lstrip())
    flush_paragraph()
    flush_list()
    return "\n".join(blocks)


def _asset_path(value: str) -> str:
    value = LIQUID_URL.sub(lambda match: match[1], value).strip()
    parsed = urlsplit(value)
    path = unquote(parsed.path)
    # The current About Markdown uses ../wp-content; both forms resolve to
    # the same versioned public asset. Never resolve arbitrary parent paths.
    if "wp-content/" in path:
        return path[path.index("wp-content/"):]
    return path.lstrip("/")


def _image_source(value: str, source: Path, assets: dict[str, str]) -> str:
    path = _asset_path(value)
    for key in (path, "/" + path, value):
        if key in assets:
            return assets[key]
    for key, replacement in assets.items():
        if _asset_path(key) == path:
            return replacement
    local = (source / path).resolve()
    try:
        local.relative_to(source.resolve())
    except ValueError:
        local = source / "__missing_asset__"
    if local.is_file():
        media_type = mimetypes.guess_type(local.name)[0] or "application/octet-stream"
        encoded = base64.b64encode(local.read_bytes()).decode("ascii")
        return f"data:{media_type};base64,{encoded}"
    return urljoin(PUBLIC_BASE, path)


def _safe_url(value: str) -> str | None:
    value = html.unescape(value).strip()
    scheme = urlsplit(value).scheme.lower()
    if scheme not in {"", "https", "http", "mailto", "tel"}:
        return None
    return value if scheme or value.startswith("#") else urljoin(PUBLIC_BASE, value)


def _clean_tree(root: Node, page_id: str, source: Path, assets: dict[str, str]) -> list[Any]:
    heading_counts: dict[str, int] = {}

    def clean(node):
        if isinstance(node, str):
            return [node]
        if node.tag in {"script", "style", "iframe", "object", "noscript"}:
            return []
        children = [part for child in node.children for part in clean(child)]
        if node.tag == "div" and "wp-block-buttons" in (node.attrs.get("class") or "").split():
            return [Node("nav", {"class": "profile-links", "aria-label": "Research profiles"}, children)]
        if node.tag not in ALLOWED_TAGS:
            return children
        if node.tag in {"strong", "b"} and "Tomoyuki" in node.text:
            return children
        if node.tag == "p" and not node.text.strip() and not any(
            isinstance(child, Node) and child.tag == "img" for child in children
        ):
            return []
        attrs: dict[str, str | None] = {}
        if node.tag == "a":
            href = _safe_url(node.attrs.get("href") or "")
            if not href:
                return children
            attrs = {"href": href}
            if urlsplit(href).scheme in {"https", "http"}:
                attrs.update({"target": "_blank", "rel": "noopener noreferrer"})
            if node.attrs.get("title"):
                attrs["title"] = node.attrs["title"]
        elif node.tag == "img":
            attrs = {
                "src": _image_source(node.attrs.get("src") or "", source, assets),
                "alt": node.attrs.get("alt") or "",
                "decoding": "async",
                "loading": "eager" if page_id == "home" else "lazy",
            }
            for size in ("width", "height"):
                if (node.attrs.get(size) or "").isdigit():
                    attrs[size] = node.attrs[size]
        elif node.tag == "ol" and "reversed" in node.attrs:
            attrs["reversed"] = "reversed"
        elif node.tag in {"th", "td"}:
            for key in ("scope", "colspan", "rowspan"):
                value = node.attrs.get(key)
                if value and (key == "scope" and value in {"row", "col", "rowgroup", "colgroup"}
                              or key != "scope" and value.isdigit()):
                    attrs[key] = value
        elif node.tag == "table":
            attrs["class"] = "profile-table"
        elif re.fullmatch("h[2-6]", node.tag):
            slug = re.sub(r"[^\w-]+", "-", node.text.strip().lower()).strip("-") or "section"
            heading_counts[slug] = heading_counts.get(slug, 0) + 1
            suffix = "" if heading_counts[slug] == 1 else "-" + str(heading_counts[slug])
            attrs["id"] = f"{page_id}-{slug}{suffix}"
        return [Node(node.tag, attrs, children)]

    return [part for child in root.children for part in clean(child)]


def _render(node: Any) -> str:
    if isinstance(node, str):
        return html.escape(node, quote=False)
    attrs = "".join(" " + key if value is None else
                    " " + key + '="' + html.escape(value, quote=True) + '"'
                    for key, value in node.attrs.items())
    start = f"<{node.tag}{attrs}>"
    if node.tag in VOID_TAGS:
        return start
    return start + "".join(_render(child) for child in node.children) + f"</{node.tag}>"


def _elements(nodes: list[Any]) -> list[Node]:
    return [node for node in nodes if isinstance(node, Node)]


def _with_class(node: Node, name: str) -> Node:
    node.attrs["class"] = " ".join(filter(None, (node.attrs.get("class"), name)))
    return node


def _home_profile(source: Path, assets: dict[str, str]) -> Node:
    """Reuse the approved About profile without inventing homepage content."""
    _, body = _read_page(source / "about.md")
    nodes = _clean_tree(Fragment(_markdown_html(body)).root, "home", source, assets)
    elements = _elements(nodes)
    if len(elements) < 5 or [node.tag for node in elements[:3]] != ["img", "p", "p"]:
        raise ValueError("The homepage profile needs the existing About image and biography")
    image, _, bio = elements[:3]
    information = next((index for index, node in enumerate(elements)
                        if node.tag == "h2" and node.text.strip() == "Information"), None)
    if information is None or information + 1 >= len(elements) or elements[information + 1].tag != "p":
        raise ValueError("The homepage profile needs the existing About contact paragraph")
    contact = elements[information + 1]
    lines: list[list[Any]] = [[]]
    for child in contact.children:
        if isinstance(child, Node) and child.tag == "br":
            lines.append([])
        else:
            lines[-1].append(child)

    # The source's postal address is the second line. Keep its exact text under
    # the photograph; retain the other contact lines beside the biography.
    sidebar: list[Any] = [Node("figure", {"class": "home-profile-photo"}, [image])]
    copy: list[Any] = [bio]
    if len(lines) == 4:
        sidebar.append(Node("p", {"class": "home-profile-address"}, lines[1]))
        details: list[Any] = []
        for index, line in enumerate((lines[0], lines[2], lines[3])):
            if index:
                details.append(Node("br"))
            details.extend(line)
        copy.append(Node("p", {"class": "home-contact-details"}, details))
    else:
        # A later source edit must not silently drop or mislabel contact data.
        copy.append(contact)
    links = next((node for node in elements if node.tag == "nav"
                  and node.attrs.get("class") == "profile-links"), None)
    if links:
        copy.append(links)
    return Node("section", {"class": "home-profile", "aria-label": "Profile"}, [
        Node("div", {"class": "home-profile-copy"}, copy),
        Node("aside", {"class": "home-profile-sidebar", "aria-label": "Portrait and address"}, sidebar),
    ])


def _layout_home(nodes: list[Any], source: Path, assets: dict[str, str]) -> list[Any]:
    elements = _elements(nodes)
    content = nodes
    if len(elements) >= 2 and elements[0].tag == "p" and elements[1].tag == "img":
        intro, image = elements[:2]
        rest = [node for node in nodes if node is not intro and node is not image]
        for node in _elements(rest):
            if node.tag == "ul":
                _with_class(node, "method-list")
            elif node.tag == "p":
                _with_class(node, "section-lead")
        content = [
            Node("div", {"class": "home-overview"}, [
                Node("div", {"class": "home-introduction"}, [intro]),
                Node("figure", {"class": "home-research-visual"}, [image]),
            ]),
            Node("div", {"class": "home-processes"}, rest),
        ]
    return [
        _home_profile(source, assets),
        Node("section", {"class": "home-research-overview", "aria-labelledby": "home-research-overview-title"}, [
            Node("h2", {"id": "home-research-overview-title"}, ["Research overview"]),
            *content,
        ]),
    ]


def _layout_about(nodes: list[Any]) -> list[Any]:
    elements = _elements(nodes)
    if len(elements) < 3 or [node.tag for node in elements[:3]] != ["img", "p", "p"]:
        return nodes
    image, name, bio = elements[:3]
    _with_class(name, "profile-name")
    # Keep the Japanese name together when the profile column becomes narrow.
    name_parts = re.fullmatch(r"(.*?)(\s+)([\u3040-\u30ff\u3400-\u9fff].*)", name.text)
    if name_parts:
        name.children = [Node("span", {"class": "profile-name-en"}, [name_parts[1]]),
                         name_parts[2],
                         Node("span", {"class": "profile-name-ja"}, [name_parts[3]])]
    rest = [node for node in nodes if all(node is not item for item in (image, name, bio))]
    return [
        Node("div", {"class": "profile-overview"}, [
            Node("figure", {"class": "profile-photo"}, [image]),
            Node("div", {"class": "profile-bio"}, [name, bio]),
        ]),
        Node("div", {"class": "profile-details"}, rest),
    ]


def _layout_grants(nodes: list[Any]) -> list[Any]:
    for node in _elements(nodes):
        if node.tag == "ul":
            _with_class(node, "grant-list")
            for item in _elements(node.children):
                if item.tag != "li":
                    continue
                lines: list[list[Any]] = [[]]
                for child in item.children:
                    if isinstance(child, Node) and child.tag == "br":
                        lines.append([])
                    else:
                        lines[-1].append(child)
                if len(lines) == 3:
                    item.children = [Node("div", {"class": name}, line)
                                     for name, line in zip(
                                         ("grant-program", "grant-project", "grant-meta"), lines)]
        elif node.tag == "ol":
            _with_class(node, "support-list")
    return nodes


def build_pages(source: Path, assets: dict[str, str] | None = None) -> dict[str, dict[str, Any]]:
    """Return safe body HTML and metadata for Home, About, Research, Grants, Award.

    The caller owns each page's h1, navigation and routing.  Asset keys may be
    decoded repository paths, percent-encoded paths, or the original src value.
    When an asset exists in the supplied snapshot it is embedded automatically;
    otherwise the original public website URL is retained.
    """
    source = Path(source)
    assets = assets or {}
    result: dict[str, dict[str, Any]] = {}
    for page_id, (title, filename) in PAGE_SOURCES.items():
        metadata, body = _read_page(source / filename)
        root = Fragment(_markdown_html(body)).root
        nodes = _clean_tree(root, page_id, source, assets)
        if page_id == "home":
            nodes = _layout_home(nodes, source, assets)
        elif page_id == "about":
            nodes = _layout_about(nodes)
        elif page_id == "grants":
            nodes = _layout_grants(nodes)
        elif page_id == "award":
            for node in _elements(nodes):
                if node.tag == "ol":
                    _with_class(node, "award-list")
        wrapper = Node("div", {"class": f"static-page-content static-page-{page_id}"}, nodes)
        result[page_id] = {
            "title": title,
            "html": _render(wrapper),
            "source": filename,
            "description": metadata.get("description", ""),
            "permalink": metadata.get("permalink", "/"),
        }
        if page_id == "home":
            result[page_id]["subtitle"] = "Assistant Professor · Chemical Engineering · Hiroshima University"
            result[page_id]["additional_sources"] = ["about.md"]
    return result
