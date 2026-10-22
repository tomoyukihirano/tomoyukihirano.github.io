"""Apply only the two author-identity merges confirmed on 2026-10-22."""
from pathlib import Path
import copy
import json
import re
import yaml

ROOT = Path('_data')
REDIRECTS = {
    'annie-m-rahmatika': 'annie-mufyda-rahmatika',
    'asep-nandiyanto': 'asep-bayu-dani-nandiyanto',
}

def flow(value):
    return json.dumps(value, ensure_ascii=False)

def replace_one(text, pattern, replacement):
    updated, count = re.subn(pattern, lambda _: replacement, text, flags=re.M)
    if count != 1:
        raise ValueError(f'Expected exactly one match: {pattern}; got {count}')
    return updated

def main():
    files = sorted(ROOT.rglob('*.yml'))
    original_text = {p: p.read_text(encoding='utf-8') for p in files}
    before = {p: yaml.safe_load(text) for p, text in original_text.items()}
    people_path = ROOT / 'people.yml'
    people = before[people_path]
    names = {r['id']: r['name'] for r in people['records']}
    records = {r['id']: r for r in people['records']}
    assert len(records) == len(people['records']) == 113
    changes = {}
    text = original_text[people_path]
    for old, new in REDIRECTS.items():
        assert old in records and new in records
        assert old not in people.get('id_redirects', {})
        canonical = copy.deepcopy(records[new])
        canonical['aliases'] = list(dict.fromkeys(canonical.get('aliases', []) + [names[old]]))
        canonical['legacy_ids'] = list(dict.fromkeys(canonical.get('legacy_ids', []) + [old]))
        canonical['identity_confirmed_on'] = '2026-10-22'
        text = replace_one(text, r'^- \{id: ' + re.escape(old) + r', [^\n]*\}\n', '')
        text = replace_one(text, r'^- \{id: ' + re.escape(new) + r', [^\n]*\}$', '- ' + flow(canonical))
    assert 'id_redirects:\n' in text
    text = text.rstrip() + '\n' + ''.join(f'  {old}: {new}\n' for old, new in REDIRECTS.items())
    changes[people_path] = text
    affected = []
    for path in files:
        if path.parent.name != 'publications':
            continue
        text = original_text[path]
        for record in before[path]['records']:
            for key, original_key in [('authors', 'author_names_as_imported'), ('corresponding_authors', 'corresponding_author_names_as_imported')]:
                ids = record.get(key, [])
                if not any(i in REDIRECTS for i in ids):
                    continue
                pattern = r'^- id: ' + re.escape(record['id']) + r'\n[\s\S]*?(?=^- id: |\Z)'
                match = re.search(pattern, text, flags=re.M)
                assert match is not None
                old_block = match.group()
                replacement = f'  {key}: {flow([REDIRECTS.get(i, i) for i in ids])}'
                if original_key not in record:
                    replacement += f'\n  {original_key}: {flow([names[i] for i in ids])}'
                list_pattern = r'^  ' + re.escape(key) + r':(?: +\[[^\n]*\]|\n(?:  - [^\n]+\n?)+)'
                found = re.search(list_pattern, old_block, flags=re.M)
                assert found is not None
                if found.group().endswith('\n'):
                    replacement += '\n'
                new_block = replace_one(old_block, list_pattern, replacement)
                text = text[:match.start()] + new_block + text[match.end():]
                affected.append({'record': record['id'], 'field': key})
        if text != original_text[path]:
            changes[path] = text
    after = {p: yaml.safe_load(changes.get(p, original_text[p])) for p in files}
    expected_people = copy.deepcopy(people)
    expected_people['records'] = [r for r in expected_people['records'] if r['id'] not in REDIRECTS]
    for old, new in REDIRECTS.items():
        r = next(r for r in expected_people['records'] if r['id'] == new)
        r['aliases'] = list(dict.fromkeys(r.get('aliases', []) + [names[old]]))
        r['legacy_ids'] = list(dict.fromkeys(r.get('legacy_ids', []) + [old]))
        r['identity_confirmed_on'] = '2026-10-22'
        expected_people['id_redirects'][old] = new
    assert after[people_path] == expected_people
    valid_ids = {r['id'] for r in expected_people['records']}
    assert len(valid_ids) == len(expected_people['records']) == 111
    counts = {'publications': 0, 'presentations': 0}
    for path in files:
        if path == people_path:
            continue
        expected = copy.deepcopy(before[path])
        if path.parent.name == 'publications':
            for r in expected['records']:
                for key, original_key in [('authors', 'author_names_as_imported'), ('corresponding_authors', 'corresponding_author_names_as_imported')]:
                    ids = r.get(key, [])
                    if any(i in REDIRECTS for i in ids):
                        r.setdefault(original_key, [names[i] for i in ids])
                        r[key] = [REDIRECTS.get(i, i) for i in ids]
                assert all(i in valid_ids for i in r.get('authors', []) + r.get('corresponding_authors', []))
                assert len(r['authors']) == len(set(r['authors']))
        assert after[path] == expected, str(path)
        if path.parent.name in counts:
            counts[path.parent.name] += len(after[path]['records'])
    assert counts == {'publications': 78, 'presentations': 90}
    assert {v['record'] for v in affected} == {'pub-0008', 'pub-0017', 'pub-0023'}
    readme_path = ROOT / 'README.md'
    readme = readme_path.read_text(encoding='utf-8')
    assert readme.count('Six identity merges were confirmed') == 1
    changes[readme_path] = readme.replace('Six identity merges were confirmed', 'Eight identity merges were confirmed')
    for p, text in changes.items():
        p.write_text(text, encoding='utf-8')
    report = {'confirmed_on': '2026-10-22', 'people_before': 113, 'people_after': 111,
              'record_counts': counts, 'redirects': REDIRECTS, 'affected_publications': affected,
              'changed_files': [str(p) for p in changes], 'original_fields_preserved': True,
              'dangling_references': 0}
    Path('/tmp/identity-round2-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
