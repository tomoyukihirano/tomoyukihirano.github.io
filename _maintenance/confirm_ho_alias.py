"""Apply only the owner-confirmed author alias and verify exact output changes."""
from pathlib import Path
import copy
import hashlib
import json
import re
import subprocess
import sys
import yaml

OLD = 'Ho Thi Thang Nguyen'
NEW = 'Thi Thanh Nguyen Ho'
PID = 'thi-thanh-nguyen-ho'
PEOPLE = Path('_data/people.yml')
PRESENTATIONS = Path('_data/presentations/2025.yml')
REPORT = Path('_maintenance/ho-alias-validation.json')


def blob_sha(data):
    return hashlib.sha1(f'blob {len(data)}\0'.encode() + data).hexdigest()


def apply():
    expected_shas = {PEOPLE: '324d2b88b5e4b19c7d4db0c790e96e9e389d5f2b', PRESENTATIONS: '00d3b685046d65244310d5fffdb49a4367f44a28'}
    for path, expected in expected_shas.items():
        if blob_sha(path.read_bytes()) != expected:
            raise RuntimeError(f'Unexpected source revision: {path}')
    before_people = PEOPLE.read_text(encoding='utf-8')
    people = yaml.safe_load(before_people)
    intended_people = copy.deepcopy(people)
    person = next(p for p in intended_people['records'] if p['id'] == PID)
    assert person['name'] == NEW and OLD not in person.get('aliases', [])
    person.setdefault('aliases', []).append(OLD)
    pattern = r'^- \{[^\n]*"id": "thi-thanh-nguyen-ho"[^\n]*\}$'
    after_people, count = re.subn(pattern, lambda _: '- ' + json.dumps(person, ensure_ascii=False), before_people, flags=re.M)
    assert count == 1
    assert yaml.safe_load(after_people) == intended_people

    before_presentations = PRESENTATIONS.read_text(encoding='utf-8')
    presentations = yaml.safe_load(before_presentations)
    intended_presentations = copy.deepcopy(presentations)
    record = next(r for r in intended_presentations['records'] if r['id'] == 'pres-0081')
    assert record['display']['authors'][1]['name'] == OLD
    assert record['display']['presenter_position'] == 1
    record['display']['authors'][1]['name'] = NEW
    record['display']['authors'][1]['person_id'] = PID
    block_match = re.search(r'^- id: pres-0081\n[\s\S]*?(?=^- id: |\Z)', before_presentations, flags=re.M)
    assert block_match is not None
    block = block_match.group(0)
    updated, count = re.subn(r'^    - name: Ho Thi Thang Nguyen$', '    - name: ' + NEW + '\n      person_id: ' + PID, block, flags=re.M)
    assert count == 1
    after_presentations = before_presentations[:block_match.start()] + updated + before_presentations[block_match.end():]
    assert yaml.safe_load(after_presentations) == intended_presentations
    PEOPLE.write_text(after_people, encoding='utf-8')
    PRESENTATIONS.write_text(after_presentations, encoding='utf-8')

    people_ids = {p['id'] for p in intended_people['records']}
    assert len(people_ids) == len(intended_people['records'])
    publications = [r for p in sorted(Path('_data/publications').glob('*.yml')) for r in yaml.safe_load(p.read_text(encoding='utf-8'))['records']]
    all_presentations = [r for p in sorted(Path('_data/presentations').glob('*.yml')) for r in yaml.safe_load(p.read_text(encoding='utf-8'))['records']]
    for publication in publications:
        for field in ('authors', 'corresponding_authors'):
            assert set(publication.get(field, [])) <= people_ids
    for presentation in all_presentations:
        for author in presentation['display']['authors']:
            if author.get('person_id'):
                assert author['person_id'] in people_ids
    assert len({r['id'] for r in all_presentations}) == len(all_presentations)
    assert all(r['display']['presenter_position'] == 1 for r in all_presentations)
    changes = subprocess.check_output(['git', 'diff', '--name-only'], text=True).splitlines()
    assert set(changes) == {str(PEOPLE), str(PRESENTATIONS)}, changes
    report = {'record': 'pres-0081', 'people': len(people_ids), 'publications': len(publications), 'presentations': len(all_presentations), 'changed_files': changes, 'original_citations_preserved': True, 'author_order_dates_titles_roles_unchanged': True, 'private_data_accessed': False}
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False))


def verify_html():
    baseline = {str(p.relative_to('_baseline')): p.read_bytes() for p in Path('_baseline').rglob('*.html')}
    current = {str(p.relative_to('_site')): p.read_bytes() for p in Path('_site').rglob('*.html')}
    assert baseline.keys() == current.keys()
    target = 'presentations/index.html'
    assert baseline[target].count(OLD.encode()) == 1
    for path, data in baseline.items():
        expected = data.replace(OLD.encode(), NEW.encode()) if path == target else data
        assert current[path] == expected, f'Unexpected HTML change: {path}'
    assert OLD.encode() not in current[target]
    assert '〇'.encode() not in current[target]
    report = json.loads(REPORT.read_text(encoding='utf-8'))
    report.update({'html_pages_checked': len(baseline), 'html_change': 'one approved author-name replacement only', 'validation': 'passed'})
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False))


if __name__ == '__main__':
    if sys.argv[1:] == ['--verify-html']:
        verify_html()
    elif not sys.argv[1:]:
        apply()
    else:
        raise SystemExit('Unknown arguments')
