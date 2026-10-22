"""Apply only the six author-identity decisions confirmed on 2026-10-22."""
from pathlib import Path
from copy import deepcopy
import json
import re
import yaml

DECISIONS = [
    ("yusuke-kito", "yusuke-kitou", "Yusuke Kitou", "Yusuke", "Kitou"),
    ("kouhei-matsumoto", "kohei-matsumoto", "Kohei Matsumoto", "Kohei", "Matsumoto"),
    ("thi-tanh-nguyen-ho", "thi-thanh-nguyen-ho", "Thi Thanh Nguyen Ho", "Thi Thanh Nguyen", "Ho"),
    ("le-hoai-phong", "phong-hoai-le", "Phong Hoai Le", "Phong Hoai", "Le"),
    ("le-thi-nguyet-hang", "hang-thi-nguyet-le", "Hang Thi Nguyet Le", "Hang Thi Nguyet", "Le"),
    ("ferry-inskandar", "ferry-iskandar", "Ferry Iskandar", "Ferry", "Iskandar"),
]
REDIRECTS = {old: new for old, new, *_ in DECISIONS}
DATA = Path('_data')


def load(text):
    return yaml.safe_load(text)


def flow(value):
    return json.dumps(value, ensure_ascii=False)


def replace_once(text, pattern, replacement):
    result, count = re.subn(pattern, lambda _: replacement, text, flags=re.M)
    if count != 1:
        raise ValueError(f'Expected one match, found {count}: {pattern}')
    return result


def main():
    before_text = {p: p.read_text(encoding='utf-8') for p in DATA.rglob('*.yml')}
    before = {p: load(s) for p, s in before_text.items()}
    changes = {}
    people_path = DATA / 'people.yml'
    people = deepcopy(before[people_path])
    originals = {p['id']: deepcopy(p) for p in people['records']}
    assert len(originals) == len(people['records']), 'Duplicate pre-existing person IDs'
    assert not people.get('id_redirects'), 'Redirects already exist; review before applying'
    text = before_text[people_path]
    canonical_ids = set(REDIRECTS.values())
    name_matches = {}
    decisions = []
    for old, new, name, first, last in DECISIONS:
        assert old in originals and new in originals, f'Missing identity: {old}, {new}'
        record = deepcopy(originals[new])
        record.update(name=name, first_name=first, last_name=last)
        record['aliases'] = sorted(set(record.get('aliases', []) + [originals[old]['name']]) - {name})
        record['legacy_ids'] = sorted(set(record.get('legacy_ids', []) + [old]))
        record['identity_confirmed_on'] = '2026-10-22'
        text = replace_once(text, r'^- \{id: ' + re.escape(old) + r',[^\n]*\}\n?', '')
        text = replace_once(text, r'^- \{id: ' + re.escape(new) + r',[^\n]*\}$', '- ' + flow(record))
        for n in [record['name'], originals[old]['name'], originals[new]['name']]:
            key = ' '.join(n.split())
            assert key not in name_matches or name_matches[key] == new
            name_matches[key] = new
        decisions.append({'retired_id': old, 'canonical_id': new, 'canonical_name': name,
                          'alias': originals[old]['name'], 'family_name': last})
    text = text.rstrip() + '\n\nid_redirects:\n'
    text += ''.join(f'  {old}: {new}\n' for old, new in REDIRECTS.items())
    changes[people_path] = text
    people_after = load(text)
    current_people = {p['id']: p for p in people_after['records']}
    assert len(current_people) == len(originals) - len(DECISIONS)
    assert not set(REDIRECTS).intersection(current_people)
    for pid, record in originals.items():
        if pid not in REDIRECTS and pid not in canonical_ids:
            assert current_people[pid] == record, f'Unapproved person change: {pid}'

    affected_publications = []
    affected_presentations = []
    publication_refs = 0
    for path in sorted(DATA.joinpath('publications').glob('*.yml')):
        doc = before[path]
        output = before_text[path]
        for record in doc['records']:
            replacements = []
            for key in ('authors', 'corresponding_authors'):
                old_ids = record.get(key, [])
                if not any(pid in REDIRECTS for pid in old_ids):
                    continue
                new_ids = [REDIRECTS.get(pid, pid) for pid in old_ids]
                assert len(new_ids) == len(set(new_ids)), f'Duplicate after merge: {record["id"]}'
                preservation_key = 'author_names_as_imported' if key == 'authors' else 'corresponding_author_names_as_imported'
                assert preservation_key not in record
                names = [originals[pid]['name'] for pid in old_ids]
                replacements.append((key, new_ids, preservation_key, names))
                publication_refs += sum(pid in REDIRECTS for pid in old_ids)
            if not replacements:
                continue
            pat = r'^- id: ' + re.escape(record['id']) + r'\n[\s\S]*?(?=^- id: |\Z)'
            block = re.search(pat, output, flags=re.M)
            assert block, record['id']
            updated = block.group(0)
            for key, ids, preservation_key, names in replacements:
                pattern = r'^  ' + key + r':[^\n]*\n(?:  - [^\n]*(?:\n|$))*'
                updated = replace_once(updated, pattern,
                    f'  {key}: {flow(ids)}\n  {preservation_key}: {flow(names)}\n')
            output = output[:block.start()] + updated + output[block.end():]
            affected_publications.append(record['id'])
        if output != before_text[path]:
            changes[path] = output

    for path in sorted(DATA.joinpath('presentations').glob('*.yml')):
        output = before_text[path]
        for record in before[path]['records']:
            # Never infer identity from Japanese names or free-form citation text.
            links = []
            for index, name in enumerate(record.get('authors_raw', []), start=1):
                canonical = name_matches.get(' '.join(name.split()))
                if canonical:
                    links.append({'author_index': index, 'name_as_recorded': name, 'person_id': canonical})
            presenter = name_matches.get(' '.join((record.get('presenter_raw') or '').split()))
            if not links and not presenter:
                continue
            assert 'author_id_links' not in record and 'presenter_id' not in record
            extra = ''
            if links:
                extra += '  author_id_links: ' + flow(links) + '\n'
            if presenter:
                extra += '  presenter_id: ' + presenter + '\n'
            output = replace_once(output, r'^- id: ' + re.escape(record['id']) + r'$',
                                  '- id: ' + record['id'] + '\n' + extra.rstrip())
            affected_presentations.append(record['id'])
        if output != before_text[path]:
            changes[path] = output

    counts = {'publications': 0, 'presentations': 0}
    for kind in counts:
        all_ids = []
        for path in sorted(DATA.joinpath(kind).glob('*.yml')):
            new = load(changes.get(path, before_text[path]))
            old = before[path]
            assert len(new['records']) == len(old['records'])
            for a, b in zip(old['records'], new['records']):
                all_ids.append(b['id'])
                for key, value in a.items():
                    expected = [REDIRECTS.get(v, v) for v in value] if key in ('authors', 'corresponding_authors') else value
                    assert b[key] == expected, f'Unapproved change: {path}: {a["id"]}.{key}'
                for key in ('authors', 'corresponding_authors'):
                    for pid in b.get(key, []):
                        assert pid in current_people, f'Unresolved ID: {pid}'
                for link in b.get('author_id_links', []):
                    assert link['person_id'] in current_people
                    assert b['authors_raw'][link['author_index'] - 1] == link['name_as_recorded']
                if b.get('presenter_id'):
                    assert b['presenter_id'] in current_people
        assert len(all_ids) == len(set(all_ids)), f'Duplicate {kind} IDs'
        counts[kind] = len(all_ids)

    readme_path = DATA / 'README.md'
    readme = readme_path.read_text(encoding='utf-8')
    assert '## Confirmed author identity corrections' not in readme
    readme += '''\n## Confirmed author identity corrections\n\nSix identity merges were confirmed by the repository owner on 2026-10-22.\nCanonical person records keep alternate spellings/order in `aliases` and retired IDs in `legacy_ids`.\n`people.yml` also contains `id_redirects` so old exported IDs can be resolved.\nPublication author and corresponding-author IDs were redirected without changing their order.\n`author_names_as_imported` and `corresponding_author_names_as_imported` preserve the names\nresolved from the pre-correction master; these are NOT independently verified publisher spellings.\nOriginal website citations and all presentation `*_raw` / `citation_text` fields are unchanged.\nPresentation `author_id_links` use 1-based positions and only exact, confirmed name matches.\nMissing links mean unresolved, not absence of the person from the work.\nUnconfirmed spelling variants must not be merged automatically.\n'''
    changes[readme_path] = readme
    for path, output in changes.items():
        path.write_text(output, encoding='utf-8')
    for path in DATA.rglob('*.yml'):
        load(path.read_text(encoding='utf-8'))
    report = {'confirmed_on': '2026-10-22', 'people_before': len(originals),
              'people_after': len(current_people), 'decisions': decisions,
              'record_counts': counts, 'affected_publications': affected_publications,
              'updated_publication_references': publication_refs,
              'linked_presentations': affected_presentations,
              'modified_files': [str(p) for p in changes],
              'original_fields_preserved': True, 'dangling_references': 0}
    Path('/tmp/identity-normalization-report.json').write_text(flow(report), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
