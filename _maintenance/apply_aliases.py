"""Apply approved aliases on a review branch, preserving archival citations."""
from __future__ import annotations
import copy
import hashlib
import json
from pathlib import Path
import sys
import yaml

TARGETS = {
    "cao le anh kiet": ("kiet-le-anh-cao", "Kiet Le Anh Cao"),
    "ratnasari delyana": ("delyana-ratnasari", "Delyana Ratnasari"),
}
CONFIRMED = "2026-10-22"
REPORT = Path("_audit/alias-report.json")

def norm(value):
    return " ".join(value.split()).casefold()

def child(node, key):
    matches = [v for k, v in node.value if k.value == key]
    if len(matches) != 1:
        raise ValueError(f"Expected exactly one key: {key}")
    return matches[0]

def replace_spans(text, edits):
    end = len(text) + 1
    for start, stop, value in sorted(edits, reverse=True):
        if not 0 <= start <= stop <= len(text) or stop > end:
            raise ValueError("Overlapping or invalid replacement span")
        text = text[:start] + value + text[stop:]
        end = start
    return text

def apply():
    people_path = Path("_data/people.yml")
    original_text = people_path.read_text(encoding="utf-8")
    people = copy.deepcopy(yaml.safe_load(original_text))
    by_id = {p["id"]: p for p in people["records"]}
    if len(by_id) != len(people["records"]):
        raise ValueError("Duplicate person IDs")
    observed = {pid: set() for pid, _ in TARGETS.values()}
    for pid, canonical in TARGETS.values():
        if by_id[pid]["name"] != canonical:
            raise ValueError("Canonical identity differs from approved baseline")
    replacements = {}
    affected = []
    occurrences = 0
    total_presentations = 0
    display_replacements = {}
    for path in sorted(Path("_data/presentations").glob("*.yml")):
        source = path.read_text(encoding="utf-8")
        parsed = yaml.safe_load(source)
        expected = copy.deepcopy(parsed)
        nodes = child(yaml.compose(source), "records").value
        if len(nodes) != len(parsed["records"]):
            raise ValueError("Record/node mismatch")
        edits = []
        for record, expected_record, node in zip(parsed["records"], expected["records"], nodes):
            total_presentations += 1
            authors = record["display"]["authors"]
            author_nodes = child(child(node, "display"), "authors").value
            if len(authors) != len(author_nodes):
                raise ValueError("Author/node mismatch")
            for position, (author, author_node) in enumerate(zip(authors, author_nodes)):
                old = author["name"]
                if norm(old) not in TARGETS:
                    continue
                pid, canonical = TARGETS[norm(old)]
                if author.get("person_id") not in (None, pid):
                    raise ValueError("Existing identity link conflicts with approval")
                name_node = child(author_node, "name")
                if "\n" in source[name_node.start_mark.index:name_node.end_mark.index]:
                    raise ValueError("Unexpected multiline author name")
                value = json.dumps(canonical, ensure_ascii=False)
                if "person_id" not in author:
                    key_node = next(k for k, _ in author_node.value if k.value == "name")
                    value += "\n" + " " * key_node.start_mark.column + "person_id: " + pid
                elif author["person_id"] is None:
                    link_node = child(author_node, "person_id")
                    edits.append((link_node.start_mark.index, link_node.end_mark.index, pid))
                edits.append((name_node.start_mark.index, name_node.end_mark.index, value))
                expected_record["display"]["authors"][position]["name"] = canonical
                expected_record["display"]["authors"][position]["person_id"] = pid
                observed[pid].add(old)
                display_replacements[old] = canonical
                affected.append(record["id"])
                occurrences += 1
        if edits:
            updated = replace_spans(source, edits)
            if yaml.safe_load(updated) != expected:
                raise ValueError("Unexpected presentation data change")
            replacements[path] = updated
    if not all(observed.values()):
        raise ValueError("An approved alias was not found in current display data")
    edits = []
    person_nodes = child(yaml.compose(original_text), "records").value
    for person, node in zip(people["records"], person_nodes):
        pid = person["id"]
        if pid not in observed:
            continue
        aliases = list(person.get("aliases", []))
        for alias in sorted(observed[pid]):
            if alias not in aliases:
                aliases.append(alias)
        person["aliases"] = aliases
        person["identity_confirmed_on"] = CONFIRMED
        edits.append((node.start_mark.index, node.end_mark.index, json.dumps(person, ensure_ascii=False)))
    people_text = replace_spans(original_text, edits)
    if yaml.safe_load(people_text) != people:
        raise ValueError("Unexpected person dictionary change")
    replacements[people_path] = people_text
    guide_path = Path("EDITING.md")
    guide = guide_path.read_text(encoding="utf-8")
    heading = "## コミットメッセージの方針"
    if heading not in guide:
        guide += ("\n\n" + heading + "\n\n"
                  "コミットメッセージの件名・本文には人物名を含めません。\n"
                  "例：`Normalize approved author aliases and presentation labels`。\n"
                  "対象者の氏名や別名はデータ本体で管理し，コミットの説明には記載しません。\n"
                  "既存のコミット履歴は，明示的な指示がない限り書き換えません。\n")
        replacements[guide_path] = guide
    publications = []
    for path in Path("_data/publications").glob("*.yml"):
        publications.extend(yaml.safe_load(path.read_text(encoding="utf-8"))["records"])
    if any(pid not in by_id for r in publications for field in ("authors", "corresponding_authors") for pid in r.get(field, [])):
        raise ValueError("Dangling publication reference")
    report = {"people": len(people["records"]), "publications": len(publications),
              "presentations": total_presentations, "display_occurrences_changed": occurrences,
              "affected_presentation_ids": sorted(set(affected)),
              "changed_files": [str(p) for p in sorted(replacements)],
              "display_replacements": display_replacements, "source_fields_preserved": True}
    for path, content in replacements.items():
        path.write_text(content, encoding="utf-8")
    REPORT.parent.mkdir(exist_ok=True)
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "display_replacements"}, indent=2))

def verify():
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    old_root, new_root = Path("_baseline"), Path("_site")
    old_paths = {p.relative_to(old_root) for p in old_root.rglob("*.html")}
    new_paths = {p.relative_to(new_root) for p in new_root.rglob("*.html")}
    if old_paths != new_paths:
        raise ValueError("Published HTML path set changed")
    changed = []
    for relative in sorted(old_paths):
        original = (old_root / relative).read_bytes()
        rendered = (new_root / relative).read_bytes()
        expected = original
        if relative.as_posix() == "presentations/index.html":
            for before, after in report["display_replacements"].items():
                expected = expected.replace(before.encode(), after.encode())
        if rendered != expected:
            raise ValueError(f"Unexpected HTML difference: {relative}")
        if rendered != original:
            changed.append(relative.as_posix())
    if changed != ["presentations/index.html"]:
        raise ValueError("Expected presentation page was not updated")
    report["html_files_checked"] = len(old_paths)
    report["changed_html"] = changed
    report["html_validation"] = "passed"
    del report["display_replacements"]
    report["blobs"] = {}
    for name in report["changed_files"]:
        data = Path(name).read_bytes()
        report["blobs"][name] = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(REPORT.read_text(encoding="utf-8"))

if __name__ == "__main__":
    {"apply": apply, "verify": verify}[sys.argv[1]]()
