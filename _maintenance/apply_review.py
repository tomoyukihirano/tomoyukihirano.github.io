"""Apply the owner-approved review batch without touching private records."""
from pathlib import Path
import copy, hashlib, html, json, os, re, sys, urllib.request, zipfile
import yaml

CONFIG_PATH = Path(__file__).with_name('review_config.json')
C = json.loads(CONFIG_PATH.read_text(encoding='utf-8'))
ROOT = Path(os.environ.get('REVIEW_ROOT', '.')).resolve()
AUDIT = Path(os.environ.get('REVIEW_AUDIT', '_review_audit')).resolve()
DATE = C['date']

def load(path):
    return yaml.safe_load(path.read_text(encoding='utf-8'))

def dump(data):
    return yaml.safe_dump(data, allow_unicode=True, sort_keys=False, width=120)

def compact(text):
    return re.sub(r'\s+', '', text)

def data_files():
    return sorted((ROOT / '_data').rglob('*.yml')) + [ROOT/'_data/README.md', ROOT/'EDITING.md']

def snap():
    return {str(p.relative_to(ROOT)):p.read_text(encoding='utf-8') for p in data_files()}

def by_id(files):
    people = load_from(files, '_data/people.yml')['records']
    presentations = {}
    for path, text in files.items():
        if re.fullmatch(r'_data/presentations/\d{4}\.yml',path):
            d = yaml.safe_load(text)
            for r in d['records']:
                assert r['id'] not in presentations
                assert r['year']==d['year']==int(Path(path).stem)
                presentations[r['id']] = r
    return people, presentations

def load_from(files,path):
    return yaml.safe_load(files[path])

def render_item(r):
    d=r['display']
    escape=lambda x: html.escape(str(x), quote=True).replace('&#x27;','&#39;')
    names=[]
    for a in d['authors']:
        text=escape(a['name'])
        if a.get('highlight'): text='<strong><u>'+text+'</u></strong>'
        names.append(text)
    s='，'.join(names)+'，'+d['title_html']+'，'+escape(d['conference'])
    if d.get('location'): s+='，'+escape(d['location'])
    s+='，'+escape(d['dates']['text'])
    for annotation in d.get('annotations',[]): s+=' <strong>【'+escape(annotation)+'】</strong>'
    return f'<li id="{r["id"]}">{s}</li>'

def apply():
    AUDIT.mkdir(parents=True,exist_ok=True)
    before=snap()
    (AUDIT/'before.json').write_text(json.dumps(before,ensure_ascii=False))
    ppath=ROOT/'_data/people.yml'
    pdata=load(ppath)
    people={p['id']:p for p in pdata['records']}
    lookup={}
    newids=[]
    for conf in C['identities']:
        pid=conf['person_id']
        if conf.get('new'):
            assert pid not in people
            given,family=conf['name_en'].rsplit(' ',1)
            people[pid]={'id':pid,'name':conf['name_en'],'first_name':given,'last_name':family}
            newids.append(pid)
        person=people[pid]
        assert person['name']==conf['name_en']
        person.update(name_ja=conf['name_ja'],name_ja_confirmed_on=DATE,identity_confirmed_on=DATE)
        aliases=person.setdefault('aliases',[])
        for name in (conf['name_ja'],compact(conf['name_ja'])):
            if name not in aliases: aliases.append(name)
        for name in [person['name'],person['name_ja']]+aliases:
            key=compact(name)
            assert key not in lookup or lookup[key]==pid
            lookup[key]=pid
    # Preserve untouched people lines and their formatting.
    people_text=ppath.read_text(encoding='utf-8')
    for conf in C['identities']:
        if conf.get('new'): continue
        pid=conf['person_id']; found=[]
        for line in people_text.splitlines():
            if line.startswith('- {'):
                obj=yaml.safe_load(line)[0]
                if obj['id']==pid: found.append(line)
        assert len(found)==1,pid
        people_text=people_text.replace(found[0],'- '+json.dumps(people[pid],ensure_ascii=False),1)
    insert=''.join('- '+json.dumps(people[pid],ensure_ascii=False)+'\n' for pid in newids)
    assert '\nid_redirects:' in people_text
    people_text=people_text.replace('\nid_redirects:', '\n'+insert+'\nid_redirects:',1)
    ppath.write_text(people_text,encoding='utf-8')
    links=0
    for path in sorted((ROOT/'_data/presentations').glob('*.yml')):
        data=load(path); out=[]
        for r in data['records']:
            if r['id'] in C['removed']: continue
            d=r['display']; rid=r['id']
            for a in d['authors']:
                pid=lookup.get(compact(a['name']))
                if pid:
                    assert a.get('person_id',pid)==pid
                    if not a.get('person_id'): links+=1
                    a['person_id']=pid
                    if compact(a['name'])==compact(people[pid]['name_ja']): a['name']=people[pid]['name_ja']
            cl=r.setdefault('classification',{})
            # Retain prior explicit invitations; owner confirmed other existing records general.
            cl['invited']=bool(cl.get('invited',False))
            q=r.setdefault('quality',{})
            q['invitation_status']='confirmed_by_owner'
            q['invitation_confirmed_on']=DATE
            if rid in C['ignored_awards']:
                cl['award']=None
                cl['award_reporting']='excluded_by_owner'
                d['annotations']=[a for a in d.get('annotations',[]) if not re.search(r'受賞|賞|award',a,re.I)]
                q['award_review_status']='excluded_by_owner'
                q['award_reviewed_on']=DATE
            if rid in C['online_date_records']:
                r['participation']={'presentation_date':'2022-08-10','mode':'online','confirmed_on':DATE,'source':'owner_confirmation'}
            if rid in C['proceedings_only_records']:
                r['participation']={'mode':'proceedings_only','confirmed_on':DATE,'source':'owner_confirmation','show_mode_annotation':False}
                cl['reporting_type']='presentation'
            assert d['presenter_position']==1
            out.append(r)
        data['records']=out
        path.write_text(dump(data),encoding='utf-8')
    journals_path=ROOT/'_data/journals.yml'
    journals=load(journals_path)
    journals['metrics_context']={
        'checked_month':'2026-10',
        'checked_month_source':'owner_confirmation',
        'confirmed_on':DATE,
        'metric_year':None,
        'jcr_release_year':None,
        'quartile_aggregation':'best_quartile_among_assessed_subject_categories',
        'q1_rule':'at_least_one_assessed_subject_category_is_Q1',
        'subject_categories':None,
        'values_reverified_in_this_update':False,
        'note':'調査年月と指標の対象年・JCR版の年は別です。既存値は保持し，対象年と分野名は未確認です。'}
    journals_path.write_text(dump(journals),encoding='utf-8')
    policy={
        'schema_version':1,'confirmed_on':DATE,
        'review_batch':{'questions_from':25,'questions_through':72},
        'presentation':{
            'classification_basis':'nature_of_event_not_host_country',
            'conference_scope_options':['domestic','international'],
            'separate_event_types':['seminar','exhibition_lecture'],
            'separate_event_types_filter':'all_presentations_only',
            'website_date_basis':'conference_period',
            'individual_presentation_date_field':'participation.presentation_date',
            'presenter_marker':False,
            'proceedings_only_reporting':'include_as_presentation_without_special_label',
            'invitation_confirmation_applies_to':'existing_records_at_review_date_only',
            'new_record_invitation_default':None,
            'reserved_retired_ids':C['removed'],
            'ignored_award_record_ids':C['ignored_awards'],
            'ignored_award_means':'excluded_from_reporting_not_confirmed_absence_of_award',
            'excluded_import_candidates':[{'source':'lab_website','source_record_number':359,'status':'deferred_by_owner'}]},
        'publication_metrics':{
            'top10_percent':{
                'stored_field':'classification.top10_percent','level':'article','basis':'citation_percentile',
                'threshold_percent':10,'aggregation':'any_assessed_field',
                'assessment_date':None,'assessment_year':None,'assessment_fields':None,
                'note':'論文被引用数に基づくTop10%です。雑誌順位ではありません。既存判定値は変更しません。'},
            'journal_metrics_context':'journals.metrics_context'},
        'internal_report':{
            'scope_selection':'select_at_export','default_scope':None,
            'presentation_scopes':['student_is_presenter','student_is_any_author'],
            'publication_scopes':['student_is_first_author','student_is_any_author'],
            'private_relationship_data_required':True,
            'private_records_in_public_build':False,
            'note':'出力時に条件を選択します。この設定は自動出力プログラムの実装完了を意味しません。'}}
    (ROOT/'_data/reporting_policy.yml').write_text(dump(policy),encoding='utf-8')
    p=ROOT/'_data/README.md'; text=p.read_text(encoding='utf-8')
    text=text.replace('`top10_percent`: Top-10% journal flag from the source workbook.','`top10_percent`: Article citation Top-10% flag from the source workbook; any assessed field qualifies. This is not a journal-rank flag.')
    text+='\n## Consolidated review and reporting policy\n\nConfirmed review items 25–72 are applied as one data batch.\n`reporting_policy.yml` records conference classification, website date conventions,\nretired record IDs, ignored award metadata, citation-metric definitions and output-time scope selection.\nA null award value with `award_reporting: excluded_by_owner` means excluded metadata, not proof of no award.\nThe retired record is removed from the active list; its ID must not be reused.\n`journals.metrics_context.checked_month` is an investigation month, not a JCR edition or metric year.\nThe actual metric year and subject categories remain unknown. No indicator values were refreshed.\nPrivate relationship records are never loaded by the public site build.\nThe output rules do not constitute an implemented Excel/Word export tool.\n'
    p.write_text(text,encoding='utf-8')
    p=ROOT/'EDITING.md'; text=p.read_text(encoding='utf-8')
    text+='\n## 業績の集計設定\n\n`_data/reporting_policy.yml`に分類・集計ルールを保存しています。\n研究機関セミナー・展示会講演は学会区分と分け，ホームページの日付は原則として会期を使います。\n個別発表日は`participation.presentation_date`です。誌上発表も通常の発表一覧に残します。\n受賞情報を無視する指定は`award_reporting: excluded_by_owner`で管理し，受賞していないと断定しません。\nIF・JCR Quartileの調査年月は2026年10月です。指標の対象年やJCR版の年は未確認です。\nTop10%は論文被引用数による区分であり，評価分野の一つでも該当すれば採用します。\nQ1も評価分野の一つでも該当すれば採用します。既存の指標値自体は変更していません。\n主指導学生の業績の範囲は出力時に選択し，選択値を出力記録に残します。自動出力機能は別途実装します。\n'
    p.write_text(text,encoding='utf-8')
    after=snap(); report=validate(before,after)
    report['new_author_links']=links
    report['changed_files']=[n for n in after if before.get(n)!=after[n]]
    (AUDIT/'after.json').write_text(json.dumps(after,ensure_ascii=False))
    (AUDIT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    for label,files in [('before',before),('after',after)]:
        with zipfile.ZipFile(AUDIT/(label+'.zip'),'w',zipfile.ZIP_DEFLATED) as z:
            for n,t in files.items(): z.writestr(n,t)
    print(json.dumps(report,ensure_ascii=False))

def validate(before,after):
    bp,br=by_id(before); ap,ar=by_id(after)
    assert len(bp)==111 and len(ap)==115
    assert len(br)==91 and len(ar)==90
    assert set(br)-set(ar)==set(C['removed']) and not(set(ar)-set(br))
    pids={p['id'] for p in ap}; assert len(pids)==len(ap)
    assert sum(len(load_from(after,n)['records']) for n in after if n.startswith('_data/publications/') and n.endswith('.yml'))==78
    for n in before:
        if n.startswith('_data/publications/'): assert after[n]==before[n]
    assert load_from(after,'_data/journals.yml')['records']==load_from(before,'_data/journals.yml')['records']
    changed_names=[]; invited=[]; visible_changes=[]
    allowedkeys={'display','quality','classification','participation'}
    for rid,r in ar.items():
        b=br[rid]
        for k in set(b)|set(r):
            if k not in allowedkeys: assert r.get(k)==b.get(k),(rid,k)
        d=r['display'];bd=b['display']
        assert len(d['authors'])==len(bd['authors'])
        for k in set(d)|set(bd):
            if k not in {'authors','annotations'}: assert d.get(k)==bd.get(k),(rid,k)
        for a,ba in zip(d['authors'],bd['authors']):
            assert a.get('highlight')==ba.get('highlight')
            assert compact(a['name'])==compact(ba['name'])
            if a['name']!=ba['name']: changed_names.append({'record_id':rid,'old':ba['name'],'new':a['name']})
            if a.get('person_id'): assert a['person_id'] in pids
            if ba.get('person_id'): assert a.get('person_id')==ba['person_id']
        bc=b.get('classification',{}); rc=r['classification']
        assert rc['invited']==bool(bc.get('invited',False))
        if rc['invited']: invited.append(rid)
        for k,v in bc.items():
            if k!='award' or rid not in C['ignored_awards']: assert rc.get(k)==v
        if rid in C['ignored_awards']:
            assert rc['award'] is None and rc['award_reporting']=='excluded_by_owner'
            assert d['annotations']==[a for a in bd.get('annotations',[]) if not re.search(r'受賞|賞|award',a,re.I)]
        else: assert d.get('annotations')==bd.get('annotations')
        if rid in C['online_date_records']:
            assert r['participation']['presentation_date']=='2022-08-10'
        if render_item(r)!=render_item(b): visible_changes.append(rid)
    assert len(invited)==4
    return {'base_commit':C['base_commit'],'confirmed_questions':list(range(25,73)),
        'people':len(ap),'publications':78,'presentations':len(ar),'removed_ids':C['removed'],
        'invited_presentations':len(invited),'general_presentations':len(ar)-len(invited),
        'award_reporting_excluded':C['ignored_awards'],'original_fields_preserved_for_remaining_records':True,
        'publication_data_byte_identical':True,'journal_indicator_values_preserved':True,
        'renormalized_spacing':changed_names,'visible_changed_record_ids':visible_changes,
        'private_repository_accessed':False,'export_tool_implemented':False,'full_jekyll_build_verified':False}

def verify():
    before=json.loads((AUDIT/'before.json').read_text());after=json.loads((AUDIT/'after.json').read_text())
    validate(before,after)
    br=by_id(before)[1];ar=by_id(after)[1]
    bd=ROOT/'_baseline';ad=ROOT/'_site'
    old={str(p.relative_to(bd)):p.read_bytes() for p in bd.rglob('*') if p.is_file()}
    new={str(p.relative_to(ad)):p.read_bytes() for p in ad.rglob('*') if p.is_file()}
    assert set(old)==set(new)
    changes=[n for n in old if old[n]!=new[n]]
    assert changes==['presentations/index.html'] or set(changes)=={'presentations/index.html'},changes
    expected=old['presentations/index.html'].decode()
    for rid,b in br.items():
        pattern=rf'<li id="{re.escape(rid)}">.*?</li>'
        matches=re.findall(pattern,expected,flags=re.S);assert len(matches)==1,rid
        original=matches[0]
        if rid in C['removed']:
            replacement=''
        else:
            assert original==render_item(b),(rid,'baseline rendering differs')
            replacement=render_item(ar[rid])
        expected=expected.replace(original,replacement,1)
    assert expected==new['presentations/index.html'].decode(),'unexpected generated HTML difference'
    text=expected
    assert len(re.findall(r'<li id="pres-',text))==90
    assert not re.search(r'[〇◯○]',re.search(r'<ol reversed class="wp-block-list">(.*?)</ol>',text,re.S).group(1))
    report=json.loads((AUDIT/'report.json').read_text());report.update(full_jekyll_build_verified=True,generated_html_pages=len([n for n in new if n.endswith('.html')]),changed_generated_files=changes,exact_allowed_html_changes=True)
    (AUDIT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    with zipfile.ZipFile(AUDIT/'preview.zip','w',zipfile.ZIP_DEFLATED) as z:
        for n,v in new.items():z.writestr(n,v)
    print(json.dumps(report,ensure_ascii=False))

def upload():
    # Store only verified production file blobs in a tree based on the untouched main snapshot.
    report=json.loads((AUDIT/'report.json').read_text());assert report['full_jekyll_build_verified']
    files=json.loads((AUDIT/'after.json').read_text())
    elems=[{'path':n,'mode':'100644','type':'blob','content':files[n]} for n in report['changed_files']]
    payload=json.dumps({'base_tree':C['base_tree'],'tree':elems}).encode()
    req=urllib.request.Request('https://api.github.com/repos/tomoyukihirano/tomoyukihirano.github.io/git/trees',data=payload,headers={'Authorization':'Bearer '+os.environ['GH_TOKEN'],'Accept':'application/vnd.github+json','Content-Type':'application/json'},method='POST')
    with urllib.request.urlopen(req,timeout=60) as r: out=json.load(r)
    (AUDIT/'tree.json').write_text(json.dumps({'tree_sha':out['sha'],'parent_commit':C['base_commit'],'changed_files':report['changed_files']},indent=2)+'\n')
    print('Validated production tree stored; no branch or commit updated.')

if __name__=='__main__':
    {'apply':apply,'verify':verify,'upload':upload}[sys.argv[1]]()
