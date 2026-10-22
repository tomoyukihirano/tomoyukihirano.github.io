"""Apply and validate one owner-confirmed public-data review batch."""
from __future__ import annotations
import copy, html, json, os, re, sys, urllib.request, zipfile
from pathlib import Path
import yaml

BASE = '6694b299a760af316bf6b98b99e7e26a1350a7d2'
DATE = '2026-10-22'
ROOT = Path('.')
OUT = Path('_batch_audit')
DATA = ROOT / '_data'
YEAR_IDS = {'pres-0026', 'pres-0027', 'pres-0028', 'pres-0029'}
INVITED = {'pres-0068': True, 'pres-0069': True, 'pres-0071': False}
RULES = {
 'shota-imaoka': {'name_ja': '今岡 生太', 'aliases': ['今岡 生太', '今岡生太']},
 'eka-lutfi-septiani': {'aliases': ['Septiani Eka Lutfi']},
 'febrigia-ghana-rinaldi': {'aliases': ['Rinaldi Febrigia Ghana']},
 'eishi-tanabe': {'name_ja': '田辺 栄司', 'aliases': ['田辺 栄司', '田辺栄司']},
 'kohei-matsumoto': {'name_ja': '松本 恒平', 'aliases': ['松本 恒平', '松本恒平']},
}

class UniqueLoader(yaml.SafeLoader):
    pass

def construct_mapping(loader, node, deep=False):
    result = {}
    for kn, vn in node.value:
        key = loader.construct_object(kn, deep=deep)
        if key in result:
            raise ValueError('Duplicate YAML key')
        result[key] = loader.construct_object(vn, deep=deep)
    return result

UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, construct_mapping)

def load(text):
    return yaml.load(text, Loader=UniqueLoader)

def compact(s):
    return re.sub(r'\s+', '', s)

def dump_record(rec):
    return yaml.safe_dump([rec], allow_unicode=True, sort_keys=False, width=120)

def split_blocks(text):
    matches = list(re.finditer(r'^- id: (pres-\d+)\s*$', text, re.M))
    if not matches:
        raise ValueError('No presentation records')
    header = text[:matches[0].start()]
    blocks = {}
    for i, match in enumerate(matches):
        end = matches[i+1].start() if i+1 < len(matches) else len(text)
        blocks[match.group(1)] = text[match.start():end]
    return header, blocks

def load_presentations(texts):
    recs = {}
    paths = {}
    for path, text in texts.items():
        if not re.fullmatch(r'_data/presentations/\d{4}\.yml', path):
            continue
        doc = load(text)
        for rec in doc['records']:
            if rec['id'] in recs:
                raise ValueError('Duplicate presentation ID')
            assert rec['year'] == doc['year']
            recs[rec['id']] = rec
            paths[rec['id']] = path
    return recs, paths

def apply():
    OUT.mkdir(exist_ok=True)
    files = sorted(DATA.rglob('*.yml')) + [DATA/'README.md', ROOT/'EDITING.md']
    before = {p.as_posix(): p.read_text(encoding='utf-8') for p in files}
    (OUT/'before.json').write_text(json.dumps(before, ensure_ascii=False), encoding='utf-8')
    people_doc = load(before['_data/people.yml'])
    people = {p['id']: p for p in people_doc['records']}
    assert len(people) == len(people_doc['records']) == 111
    pres, original_paths = load_presentations(before)
    assert len(pres) == 91
    original_pres = copy.deepcopy(pres)
    original_people = copy.deepcopy(people_doc)
    name_map = {}
    for pid, rule in RULES.items():
        person = people[pid]
        if 'name_ja' in rule:
            assert person.get('name_ja') in (None, rule['name_ja'])
            person['name_ja'] = rule['name_ja']
            person['name_ja_confirmed_on'] = DATE
        aliases = person.setdefault('aliases', [])
        for alias in rule['aliases']:
            if alias not in aliases:
                aliases.append(alias)
        person['identity_confirmed_on'] = DATE
        for name in [person['name']] + aliases + ([person['name_ja']] if 'name_ja' in person else []):
            target = person['name_ja'] if re.search(r'[\u3400-\u9fff]', name) else person['name']
            key = compact(name)
            assert key not in name_map or name_map[key] == (pid, target)
            name_map[key] = (pid, target)
    people_text = before['_data/people.yml']
    for old, new in zip(original_people['records'], people_doc['records']):
        if old == new:
            continue
        candidates = [line for line in people_text.splitlines() if line.startswith('- {') and load(line)[0]['id'] == new['id']]
        assert len(candidates) == 1
        replacement = '- ' + json.dumps(new, ensure_ascii=False)
        people_text = people_text.replace(candidates[0], replacement, 1)
    assert load(people_text) == people_doc
    (DATA/'people.yml').write_text(people_text, encoding='utf-8')
    author_changes = []
    for rid, rec in pres.items():
        for pos, author in enumerate(rec['display']['authors'], start=1):
            match = name_map.get(compact(author['name']))
            if not match:
                continue
            pid, canonical = match
            assert author.get('person_id') in (None, pid)
            old = copy.deepcopy(author)
            author['name'] = canonical
            author['person_id'] = pid
            if author != old:
                author_changes.append({'id': rid, 'position': pos, 'display_changed': old['name'] != canonical})
        if rid in YEAR_IDS:
            assert rec['year'] == 2020
            dates = rec['display']['dates']
            assert dates['start'] == '2020-08-26' and dates['end'] == '2020-08-27'
            rec['quality']['date_correction'] = {
                'confirmed_on': DATE, 'evidence': 'owner_confirmation',
                'previous_year': 2020, 'previous_start': dates['start'], 'previous_end': dates['end']}
            rec['year'] = 2021
            dates['start'], dates['end'] = '2021-08-26', '2021-08-27'
            dates['text'] = '2021年8月26日－27日'
        if rid in INVITED:
            rec['classification']['invited'] = INVITED[rid]
            rec['quality']['invited_status'] = 'confirmed_by_owner'
            rec['quality']['invited_confirmed_on'] = DATE
            if INVITED[rid]:
                annotations = rec['display']['annotations']
                assert not any('招待' in a or 'Invited' in a for a in annotations)
                annotations.append('招待講演')
    assert YEAR_IDS <= pres.keys() and INVITED.keys() <= pres.keys()
    old_blocks = {}
    headers = {}
    for path, text in before.items():
        if re.fullmatch(r'_data/presentations/\d{4}\.yml', path):
            header, blocks = split_blocks(text)
            headers[path] = header
            old_blocks.update(blocks)
    assert set(old_blocks) == set(pres)
    for path, header in headers.items():
        year = int(Path(path).stem)
        records = sorted((r for r in pres.values() if r['year'] == year), key=lambda r: r['display_order'])
        parts = [header]
        for rec in records:
            if rec == original_pres[rec['id']]:
                parts.append(old_blocks[rec['id']])
            else:
                parts.append(dump_record(rec))
        text = ''.join(parts)
        doc = load(text)
        assert doc['records'] == records
        Path(path).write_text(text, encoding='utf-8')
    guide_path = ROOT/'EDITING.md'
    guide = before['EDITING.md']
    guide += ('\n\n## データ修正のまとめ方\n\n'
              '関連する確認事項をまとめて提示し，確定した修正を検証して一括反映します。\n'
              '回答1件ごとに公開ブランチへコミットしません。\n'
              '人物名をコミットメッセージに含めない方針は継続します。\n')
    guide_path.write_text(guide, encoding='utf-8')
    readme_path = DATA/'README.md'
    readme = before['_data/README.md']
    readme += ('\n## Batched review corrections (2026-10-22)\n\n'
               'Owner-confirmed aliases and Japanese names are linked by stable person IDs.\n'
               'Questions 16-24 were applied as one coherent production batch.\n'
               'Four records moved from the 2020 data file to 2021 without changing record IDs or display order.\n'
               'The recorded conference dates are corrected; original citation text and date source text remain unchanged.\n'
               '`quality.date_correction` preserves the previous structured dates and confirmation.\n'
               '`quality.invited_status` and `invited_confirmed_on` distinguish confirmed invitation classifications\n'
               'from legacy boolean values with no explicit confirmation.\n')
    readme_path.write_text(readme, encoding='utf-8')
    after = {p: Path(p).read_text(encoding='utf-8') for p in before}
    after_pres, after_paths = load_presentations(after)
    assert len(after_pres) == 91 and set(after_pres) == set(original_pres)
    assert len(load(after['_data/people.yml'])['records']) == 111
    raw_keys = ['raw_citation_html', 'citation_text', 'authors_raw', 'presenter_raw', 'title_raw', 'details_raw', 'source_before_split', 'source_order']
    for rid, old in original_pres.items():
        new = after_pres[rid]
        for key in raw_keys:
            assert old.get(key) == new.get(key), (rid, key)
        assert new['display_order'] == old['display_order']
        assert new['display']['presenter_position'] == old['display']['presenter_position'] == 1
        assert new['display']['title_html'] == old['display']['title_html']
        assert new['display']['conference'] == old['display']['conference']
        assert len(new['display']['authors']) == len(old['display']['authors'])
        for a in new['display']['authors']:
            assert not a.get('person_id') or a['person_id'] in people
        if rid not in YEAR_IDS:
            assert new['year'] == old['year']
            assert new['display']['dates'] == old['display']['dates']
        if rid not in INVITED:
            assert new['classification'] == old['classification']
        else:
            assert new['classification']['invited'] is INVITED[rid]
    pub_count = 0
    for path, text in before.items():
        if path.startswith('_data/publications/'):
            assert after[path] == text
            pub_count += len(load(text)['records'])
    assert pub_count == 78
    changed = [p for p in before if before[p] != after[p]]
    allowed = {'_data/people.yml', '_data/README.md', 'EDITING.md'} | set(headers)
    assert set(changed) <= allowed
    report = {'base_commit': BASE, 'confirmed_questions': list(range(16,25)),
              'people': 111, 'publications': pub_count, 'presentations': len(pres),
              'author_updates': author_changes, 'year_corrected_records': sorted(YEAR_IDS),
              'invitation_confirmations': INVITED, 'changed_files': changed,
              'original_fields_preserved': True, 'publication_data_unchanged': True,
              'all_presenters_first_author': True, 'production_commit_created': False}
    (OUT/'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    for label, texts in [('before',before),('after',after)]:
        with zipfile.ZipFile(OUT/f'{label}.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
            for path, text in texts.items():
                archive.writestr(path,text)
    print(json.dumps({'changed_files': changed, 'presentations': len(pres)}, ensure_ascii=False))

def verify():
    from bs4 import BeautifulSoup
    before = json.loads((OUT/'before.json').read_text(encoding='utf-8'))
    old, _ = load_presentations(before)
    texts = {p.as_posix():p.read_text(encoding='utf-8') for p in DATA.rglob('*.yml')}
    new, _ = load_presentations(texts)
    baseline, final = Path('_baseline'), Path('_site')
    old_files = {p.relative_to(baseline).as_posix():p for p in baseline.rglob('*') if p.is_file()}
    new_files = {p.relative_to(final).as_posix():p for p in final.rglob('*') if p.is_file()}
    assert set(old_files) == set(new_files)
    changed_html = []
    for path in old_files:
        if old_files[path].read_bytes() != new_files[path].read_bytes():
            assert path == 'presentations/index.html', path
            changed_html.append(path)
    a = BeautifulSoup(old_files['presentations/index.html'].read_text(), 'html.parser')
    b = BeautifulSoup(new_files['presentations/index.html'].read_text(), 'html.parser')
    old_items = a.select('li[id^="pres-"]')
    new_items = b.select('li[id^="pres-"]')
    assert [n['id'] for n in old_items] == [n['id'] for n in new_items]
    assert len(new_items) == 91
    for left, right in zip(old_items,new_items):
        rid = left['id']
        expected = left.decode_contents()
        for oa, na in zip(old[rid]['display']['authors'], new[rid]['display']['authors']):
            if oa['name'] != na['name']:
                expected = expected.replace(html.escape(oa['name'], quote=False), html.escape(na['name'], quote=False))
        if rid in YEAR_IDS:
            expected = expected.replace(old[rid]['display']['dates']['text'], new[rid]['display']['dates']['text'])
        if INVITED.get(rid):
            expected += ' <strong>【招待講演】</strong>'
        assert right.decode_contents() == expected, rid
        assert '〇' not in right.get_text() and '◯' not in right.get_text()
    report = json.loads((OUT/'report.json').read_text())
    report.update({'html_pages':len([p for p in old_files if p.endswith('.html')]),
                   'changed_html':changed_html, 'exact_presentation_html_validated':True,
                   'other_site_files_byte_identical':True})
    (OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    with zipfile.ZipFile(OUT/'preview.zip','w',zipfile.ZIP_DEFLATED) as z:
        for path in new_files:
            z.write(new_files[path],path)
    print('Exact HTML comparison passed.')

def upload_tree():
    report = json.loads((OUT/'report.json').read_text())
    assert report.get('exact_presentation_html_validated') is True
    repo = os.environ['GITHUB_REPOSITORY']
    assert repo == 'tomoyukihirano/tomoyukihirano.github.io'
    def api(path, body=None):
        data = None if body is None else json.dumps(body).encode()
        req = urllib.request.Request('https://api.github.com/repos/'+repo+path, data=data,
            headers={'Authorization':'Bearer '+os.environ['GH_TOKEN'],
                     'Accept':'application/vnd.github+json','Content-Type':'application/json',
                     'X-GitHub-Api-Version':'2022-11-28'})
        with urllib.request.urlopen(req,timeout=30) as response:
            return json.load(response)
    assert api('/git/ref/heads/main')['object']['sha'] == BASE
    base_tree = api('/git/commits/'+BASE)['tree']['sha']
    entries = []
    for path in report['changed_files']:
        blob = api('/git/blobs', {'content':Path(path).read_text(encoding='utf-8'),'encoding':'utf-8'})
        entries.append({'path':path,'mode':'100644','type':'blob','sha':blob['sha']})
    result = api('/git/trees',{'base_tree':base_tree,'tree':entries})
    (OUT/'tree.json').write_text(json.dumps({'base_commit':BASE,'tree_sha':result['sha'],'entries':entries}, indent=2),encoding='utf-8')
    print('Validated tree object uploaded; no branch or commit updated.')

if __name__ == '__main__':
    {'apply':apply, 'verify':verify, 'upload':upload_tree}[sys.argv[1]]()
