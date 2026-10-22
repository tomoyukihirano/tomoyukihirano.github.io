"""Apply only the owner's 2026-10-22 answers 10-12 on an isolated branch."""
import copy
import hashlib
import html
import json
import re
import sys
from pathlib import Path

import yaml

ROOT = Path('.')
REPORT = ROOT / '_presenter_name_audit.json'
CONFIRMED = '2026-10-22'
NAME_GROUPS = {
    'yusuke-kitou': ('鬼頭 佑輔', ['鬼頭 佑輔', '鬼頭 祐輔']),
    'mai-watanabe': ('渡邊 真衣', ['渡邊 真衣', '渡邉 麻衣']),
}


def read_yaml(path):
    return yaml.safe_load(path.read_text(encoding='utf-8'))


def write_yaml(path, value):
    text = yaml.safe_dump(value, allow_unicode=True, sort_keys=False, width=120)
    assert yaml.safe_load(text) == value
    path.write_text(text, encoding='utf-8')


def replace_required(text, old, new):
    assert text.count(old) == 1, ('Expected one exact replacement', old)
    return text.replace(old, new)


def apply():
    people_path = ROOT / '_data/people.yml'
    people_text = people_path.read_text(encoding='utf-8')
    people = read_yaml(people_path)
    people_before = copy.deepcopy(people)
    by_id = {person['id']: person for person in people['records']}
    lookup = {}
    changes = {}
    for person_id, (canonical, variants) in NAME_GROUPS.items():
        assert person_id in by_id
        person = by_id[person_id]
        person['name_ja'] = canonical
        person['name_ja_confirmed_on'] = CONFIRMED
        person['aliases'] = list(dict.fromkeys(person.get('aliases', []) + variants))
        pattern = re.compile(r'^- .*$', re.M)
        matches = [m for m in pattern.finditer(people_text)
                   if yaml.safe_load(m.group(0))[0].get('id') == person_id]
        assert len(matches) == 1
        match = matches[0]
        replacement = '- ' + json.dumps(person, ensure_ascii=False)
        people_text = people_text[:match.start()] + replacement + people_text[match.end():]
        for variant in variants:
            lookup[re.sub(r'\s+', '', variant)] = (person_id, canonical)
    assert yaml.safe_load(people_text) == people
    people_path.write_text(people_text, encoding='utf-8')
    assert len(people['records']) == len(people_before['records'])
    for original in people_before['records']:
        if original['id'] not in NAME_GROUPS:
            assert by_id[original['id']] == original

    presentation_ids = []
    replacements = {}
    name_updates = []
    previous_presenter_positions = {}
    public_paths = sorted((ROOT / '_data/publications').glob('*.yml'))
    publication_hashes = {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in public_paths}
    for path in sorted((ROOT / '_data/presentations').glob('*.yml')):
        data = read_yaml(path)
        before = copy.deepcopy(data)
        for record in data['records']:
            presentation_ids.append(record['id'])
            display = record['display']
            assert display['authors'], record['id']
            previous_presenter_positions[record['id']] = display.get('presenter_position')
            for author in display['authors']:
                name_before = author['name']
                clean_name = re.sub(r'^[〇○◯]\s*', '', name_before)
                compact_name = re.sub(r'\s+', '', clean_name)
                if compact_name in lookup:
                    person_id, canonical = lookup[compact_name]
                    author['name'] = canonical
                    if name_before != canonical:
                        replacements[name_before] = canonical
                        name_updates.append({'record_id': record['id'], 'from': name_before,
                                             'to': canonical, 'person_id': person_id})
                elif clean_name != name_before:
                    author['name'] = clean_name
                    replacements[name_before] = clean_name
            display['presenter_position'] = 1
            display['presenter_evidence'] = 'owner_confirmed_first_author'
            quality = record.setdefault('quality', {})
            quality['presenter_status'] = 'confirmed_by_owner'
            quality['presenter_confirmed_on'] = CONFIRMED
        # All source citations, dates, titles, ordering, IDs, classifications and
        # the original combined record must remain semantically identical.
        for old, new in zip(before['records'], data['records']):
            assert old['id'] == new['id']
            for key in old:
                if key not in ('display', 'quality'):
                    assert old[key] == new[key], (old['id'], key)
            for key in old['display']:
                if key not in ('authors', 'presenter_position', 'presenter_evidence'):
                    assert old['display'][key] == new['display'][key], (old['id'], key)
            assert len(old['display']['authors']) == len(new['display']['authors'])
            for old_author, new_author in zip(old['display']['authors'], new['display']['authors']):
                assert {k: v for k, v in old_author.items() if k != 'name'} == {k: v for k, v in new_author.items() if k != 'name'}
            for key, value in old.get('quality', {}).items():
                if key not in ('presenter_status', 'presenter_confirmed_on'):
                    assert new['quality'][key] == value
        write_yaml(path, data)
    assert len(presentation_ids) == 91
    assert len(presentation_ids) == len(set(presentation_ids))

    template = ROOT / '_includes/presentation-list.html'
    text = template.read_text(encoding='utf-8')
    marker = '{%- if d.presenter_position == forloop.index -%}〇{%- endif -%}'
    text = replace_required(text, marker, '')
    assert not any(char in text for char in '〇○◯')
    template.write_text(text, encoding='utf-8')

    readme = ROOT / '_data/README.md'
    text = readme.read_text(encoding='utf-8')
    text = replace_required(text,
        "Tomoyuki Hirano's name is bold and underlined; `〇` identifies an evidenced presenter.\n`display.presenter_position` is 1-based or null. Never infer it solely from author order.\nThe older auto-parsed `presenter_raw` is NOT confirmed evidence.",
        "Tomoyuki Hirano's name is bold and underlined. No presenter symbol is displayed.\nThe owner confirmed on 2026-10-22 that all 91 existing presentations were given by\nthe first author. Their `display.presenter_position` is 1 and `presenter_evidence`\nis `owner_confirmed_first_author`. The presenter remains queryable for reports\neven though the website does not print a symbol. This confirmation applies to\nthe existing records; explicitly verify the presenter of each future addition.\nThe older auto-parsed `presenter_raw` is retained only as imported source text;\nuse `display.authors[display.presenter_position - 1]` for the confirmed presenter.")
    text += '\n## Confirmed Japanese names (2026-10-22)\n\nThe owner confirmed 鬼頭 佑輔 / 鬼頭 祐輔 as the same person,\nwith canonical Japanese name 鬼頭 佑輔 (yusuke-kitou).\nThe owner confirmed 渡邊 真衣 / 渡邉 麻衣 as the same person,\nwith canonical Japanese name 渡邊 真衣 (mai-watanabe).\nThese public Japanese names and alternate forms are stored in the people dictionary.\nOnly structured presentation display names are normalized; raw citations are unchanged.\n'
    readme.write_text(text, encoding='utf-8')

    guide = ROOT / 'EDITING.md'
    text = guide.read_text(encoding='utf-8')
    text = replace_required(text,
        '発表者が未確認なら `null` にします。筆頭著者から推測しないでください。',
        '既存91件は，全件で先頭著者が発表者と確認済みのため，`presenter_position: 1` です。\n発表者情報は提出用一覧の抽出に使いますが，ホームページには発表者記号を表示しません。\n新規追加分は発表者を個別に確認し，未確認なら `null` にします。')
    guide.write_text(text, encoding='utf-8')

    for filename, digest in publication_hashes.items():
        assert hashlib.sha256(Path(filename).read_bytes()).hexdigest() == digest
    report = {
        'confirmed_on': CONFIRMED, 'presentation_count': len(presentation_ids),
        'people_count': len(people['records']),
        'presenter_positions_changed': sum(value != 1 for value in previous_presenter_positions.values()),
        'all_presenters_confirmed_first_author': True,
        'name_updates': name_updates, 'rendered_name_replacements': replacements,
        'original_citations_preserved': True, 'publication_data_unchanged': True,
        'private_data_accessed': False,
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2))


def verify():
    report = json.loads(REPORT.read_text(encoding='utf-8'))
    baseline = ROOT / '_baseline'
    site = ROOT / '_site'
    old_pages = {p.relative_to(baseline).as_posix(): p for p in baseline.rglob('*.html')}
    new_pages = {p.relative_to(site).as_posix(): p for p in site.rglob('*.html')}
    assert old_pages.keys() == new_pages.keys()
    other_pages = 0
    for relative, old_path in old_pages.items():
        old = old_path.read_text(encoding='utf-8')
        new = new_pages[relative].read_text(encoding='utf-8')
        if relative == 'presentations/index.html':
            expected = old.replace('〇', '').replace('○', '').replace('◯', '')
            for source, target in sorted(report['rendered_name_replacements'].items(), key=lambda p: -len(p[0])):
                expected = expected.replace(html.escape(source, quote=False), html.escape(target, quote=False))
            assert expected == new, 'Presentation HTML changed outside approved symbols/names'
            assert not any(char in new for char in '〇○◯')
            assert len(re.findall(r'<li id="pres-[^"]+">', new)) == report['presentation_count']
            report['presenter_markers_removed'] = sum(old.count(char) for char in '〇○◯')
        else:
            assert old_path.read_bytes() == new_pages[relative].read_bytes(), relative
            other_pages += 1
    report['other_html_pages_byte_identical'] = other_pages
    report['presentation_html_only_approved_changes'] = True
    for path in sorted((ROOT / '_data/presentations').glob('*.yml')):
        for record in read_yaml(path)['records']:
            assert record['display']['presenter_position'] == 1
            assert record['quality']['presenter_status'] == 'confirmed_by_owner'
            assert record['display']['presenter_evidence'] == 'owner_confirmed_first_author'
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    if sys.argv[1:] == ['--verify']:
        verify()
    else:
        assert not sys.argv[1:]
        apply()
