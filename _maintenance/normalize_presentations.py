"""One-time source-checked presentation normalization, approved 2026-10-22."""
from __future__ import annotations
import copy, datetime as dt, hashlib, html, json, re
from pathlib import Path
from html.parser import HTMLParser
import yaml

EXPECTED = {
 2018:'deb4aa8b40f9a5a277f632f2a7030b15fa00b372',
 2019:'87a83893aa9cd967781bc288237207e89f17ac93',
 2020:'cdd52180b9aa60f9f5b45e95973ad6f2048d9cb4',
 2021:'52da0169b9425155385f1c4ec546fc05e73befbe',
 2022:'897eaf30164eaa22028d66aefbf7a4f02f3bed4c',
 2023:'7f1acf487156edc08013558a52bf4d9a5b942057',
 2024:'e9f20d868b7405a0e66e587a58a7667d54d4843d',
 2025:'0426bfeb1e526d9eba6b12e18a3bd653422ff077',
}
AUTHOR_COUNTS = dict(zip(range(1,92), [
4,4,5,4,2,4,4,3,4,3,3,2,3,3,3,3,2,3,3,3,4,3,3,3,3,1,3,3,3,3,
3,3,2,8,5,3,3,4,7,5,4,8,9,4,5,7,4,5,6,5,3,6,1,5,7,2,7,5,7,5,
5,7,1,4,5,7,8,2,1,3,1,3,4,3,3,2,1,3,4,5,3,3,4,4,7,8,2,3,8,2,5
]))
AUTHOR_COUNTS[34] = AUTHOR_COUNTS[42] = 7
SEPARATOR = re.compile(r'\s*(?:[,，、]\s*(?:and\s+)?|:\s+|\s+and\s+)\s*')
MONTHS = {m:i for i,m in enumerate(['January','February','March','April','May','June','July','August','September','October','November','December'],1)}

class SafeInline(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True); self.parts=[]
    def handle_starttag(self, tag, attrs):
        if tag in ('sub','sup'): self.parts.append('<'+tag+'>')
        elif tag=='br': self.parts.append(' ')
    def handle_endtag(self, tag):
        if tag in ('sub','sup'): self.parts.append('</'+tag+'>')
    def handle_data(self, data): self.parts.append(data)

def inline(source):
    p=SafeInline(); p.feed(source); return ''.join(p.parts).strip()
def text(source): return re.sub(r'</?(?:sub|sup)>','',source)
def norm_name(s): return re.sub(r'\s+',' ',s).strip()
def hirano(s): return re.sub(r'\s+','',s) in ('平野知之','TomoyukiHirano')
def git_sha(b): return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()

def parse_dates(raw):
    raw=raw.strip().rstrip('.')
    japanese = re.fullmatch(r'(\d{4})年(\d{1,2})月(\d{1,2})(?:日)?(?:\s*[-–－−―]\s*(?:(\d{1,2})月)?(\d{1,2})(?:日)?)?日?',raw)
    slash = re.fullmatch(r'(\d{4})/(\d{1,2})/(\d{1,2})(?:\s*([-–－−―,，])\s*(?:(\d{1,2})/)?(\d{1,2}))?',raw)
    english = re.fullmatch(r'('+'|'.join(MONTHS)+r')\s+(\d{1,2})(?:\s*[-–－−―]\s*(\d{1,2}))?,\s*(\d{4})',raw)
    date_kind='single'; end=None
    if japanese:
        y,m,d,em,ed=japanese.groups(); start=dt.date(int(y),int(m),int(d))
        if ed: end=dt.date(int(y),int(em or m),int(ed)); date_kind='range'
    elif slash:
        y,m,d,sep,em,ed=slash.groups(); start=dt.date(int(y),int(m),int(d))
        if ed: end=dt.date(int(y),int(em or m),int(ed)); date_kind='listed_days' if sep in (',','，') else 'range'
    elif english:
        m,d,ed,y=english.groups(); start=dt.date(int(y),MONTHS[m],int(d))
        if ed: end=dt.date(int(y),MONTHS[m],int(ed)); date_kind='range'
    else: raise ValueError('Unparsed date: '+raw)
    label=f'{start.year}年{start.month}月{start.day}日'
    if end:
        assert end>=start
        label+= ('・' if date_kind=='listed_days' else '－')
        if end.year!=start.year: label+=f'{end.year}年'
        if end.month!=start.month: label+=f'{end.month}月'
        label+=f'{end.day}日'
    return {'text':label,'start':start.isoformat(),'end':(end or start).isoformat(),'kind':date_kind,'source_text':raw,'precision':'conference_dates_as_recorded'}

def prepare(raw, number):
    s=inline(raw); annotations=[]
    while True:
        hit=re.search(r'\s*(\((?:Award|Invited)\)|【[^】]*(?:受賞|招待|Invited)[^】]*】)\s*$',s)
        if not hit: break
        label=hit[1].strip('【】()')
        annotations.insert(0, {'Award':'受賞','Invited':'招待講演'}.get(label,label))
        s=s[:hit.start()].strip()
    parts=SEPARATOR.split(s,maxsplit=AUTHOR_COUNTS[number])
    assert len(parts)==AUTHOR_COUNTS[number]+1,(number,parts)
    authors=parts[:-1]; rest=parts[-1]
    explicit=[i for i,n in enumerate(authors) if re.match(r'^[〇○◯]',n)]
    assert len(explicit)<=1,(number,explicit)
    presenter=explicit[0] if explicit else None
    evidence='source_circle_marker' if explicit else 'unconfirmed'
    if number in (72,91): presenter=0; evidence='owner_confirmation_2026-10-22'
    authors=[norm_name(re.sub(r'^[〇○◯]\s*','',n)) for n in authors]
    assert all(not any(x in n for x in ('<','>','粒子','合成','Investigation','Spherical')) for n in authors),(number,authors)
    boundary=r'，' if number==77 else r'[,，、]'
    title,detail=re.split(boundary,rest,maxsplit=1)
    title=title.strip();detail=detail.strip()
    recent=re.search(r'[(（]\s*(\d{4}/\d{1,2}/\d{1,2}(?:\s*[-–－−―]\s*(?:\d{1,2}/)?\d{1,2}|\s*[,，]\s*\d{1,2}(?=\s*[,，]))?)\s*[,，]\s*([^()（）]+)[)）]\s*$',detail)
    if recent:
        event=detail[:recent.start()].rstrip(' ,，'); location=recent[2].strip(); dates=parse_dates(recent[1])
    else:
        date=re.search(r'\d{4}年\d{1,2}月\d{1,2}.*$',detail)
        if date is None:
            date=re.search(r'(?:'+'|'.join(MONTHS)+r')\s+\d{1,2}(?:\s*[-–－−―]\s*\d{1,2})?,\s*\d{4}\.?$',detail)
        assert date,(number,detail)
        dates=parse_dates(date[0]); evplace=detail[:date.start()].rstrip(' ,，')
        fields=re.split(r'[,，]',evplace,maxsplit=1);event=fields[0].strip();location=fields[1].strip() if len(fields)>1 else None
    location=re.sub(r'\s*[,，]\s*','，',location) if location else None
    assert event and title,(number,event,location,title)
    return {'authors':authors,'presenter_position':None if presenter is None else presenter+1,
            'presenter_evidence':evidence,'title_html':title,'conference':event,
            'location':location,'dates':dates,'annotations':annotations}

TEMPLATE='''{%- assign presentations = "" | split: "" -%}
{%- for year_data in site.data.presentations -%}
  {%- assign presentations = presentations | concat: year_data[1].records -%}
{%- endfor -%}
{%- assign presentations = presentations | sort: "display_order" -%}
<ol reversed class="wp-block-list">
{%- for item in presentations -%}
  {%- assign d = item.display -%}
<li id="{{ item.id }}">{%- for author in d.authors -%}{%- unless forloop.first -%}，{%- endunless -%}{%- if author.highlight -%}<strong><u>{%- endif -%}{%- if d.presenter_position == forloop.index -%}〇{%- endif -%}{{ author.name | escape }}{%- if author.highlight -%}</u></strong>{%- endif -%}{%- endfor -%}，{{ d.title_html }}，{{ d.conference | escape }}{%- if d.location -%}，{{ d.location | escape }}{%- endif -%}，{{ d.dates.text | escape }}{%- for annotation in d.annotations %} <strong>【{{ annotation | escape }}】</strong>{%- endfor -%}</li>
{%- endfor -%}
</ol>
'''
PAGE='''---
layout: page
title: "Presentations – 平野 知之 / Tomoyuki Hirano"
heading: "Presentations"
permalink: /presentations/
nav: presentations
page_id: 76
---

## Presentations
{: .wp-block-heading }

{% include presentation-list.html %}
'''
DOC='''
## Presentation display format (2026-10-22)

The presentation page is generated from `_data/presentations/YYYY.yml` through
`_includes/presentation-list.html`. Do not maintain a second citation list in `presentations.md`.

The display order is authors, title, conference, location, date, separated by `，`.
Dates use `YYYY年M月D日－D日` (or both months when needed). English titles and author
names are not translated. Chemical subscripts/superscripts from source HTML are preserved.
Tomoyuki Hirano's name is bold and underlined; `〇` identifies an evidenced presenter.
`display.presenter_position` is 1-based or null. Never infer it solely from author order.
The older auto-parsed `presenter_raw` is NOT confirmed evidence.
`display.dates` describes recorded conference dates, not a verified individual talk date.
Original citation fields remain immutable except for the owner-approved split of pres-0072.
That original combined record is preserved in `source_before_split`; the new second record
is pres-0091. Existing IDs are never renumbered. `display_order` controls view ordering.
The `display` fields are the structured citation used by the template. `title_html` permits
only sub/sup markup; all other display text is HTML-escaped by the template.
Unconfirmed name variants, conference editions and presenter identities require review.
'''

def main(root=Path('.')):
    data=root/'_data/presentations';packs={}
    for year,digest in EXPECTED.items():
        p=data/f'{year}.yml';b=p.read_bytes();assert git_sha(b)==digest,f'Source changed: {p}'
        packs[year]=yaml.safe_load(b)
    records=[r for p in packs.values() for r in p['records']]
    assert len(records)==90
    byid={r['id']:r for r in records};assert len(byid)==90
    original=copy.deepcopy(byid['pres-0072']);a=byid['pres-0072']
    marker='<strong><span style="text-decoration: underline;">平野 知之</span></strong>, 房谷 航大'
    first,sep,last=original['raw_citation_html'].partition(marker);assert sep
    second=sep+last;assert first+second==original['raw_citation_html']
    a['raw_citation_html']=first;a['citation_text']=text(inline(first))
    a['source_before_split']=original;a['source_part']=1;a['split_confirmed_on']='2026-10-22'
    a['details_raw']='第41回エアロゾル科学・技術研究討論会（2024/8/20-22, 東京都八王子市）'
    a['quality']={'parsing_status':'owner_confirmed_split','needs_review':False}
    b={'id':'pres-0091','type':'presentation','year':2024,'source_order':19,'source_part':2,
       'derived_from':'pres-0072','split_confirmed_on':'2026-10-22',
       'raw_citation_html':second,'citation_text':text(inline(second)),
       'quality':{'parsing_status':'owner_confirmed_split','needs_review':False}}
    packs[2024]['records'].insert(packs[2024]['records'].index(a)+1,b);records.append(b)
    records.sort(key=lambda r:(r['source_order'],r.get('source_part',1)))
    parsed={r['id']:prepare(r['raw_citation_html'],int(r['id'][5:])) for r in records}
    spaced={}
    for d in parsed.values():
        for name in d['authors']:
            if re.fullmatch(r'[一-龯々]+ [一-龯々]+',name):
                key=name.replace(' ','')
                if key in spaced: assert spaced[key]==name
                spaced[key]=name
    for order,r in enumerate(records,1):
        d=parsed[r['id']];d['authors']=[{'name':spaced.get(n.replace(' ',''),n),'highlight':hirano(n)} for n in d['authors']]
        d['title_html']=re.sub(r'&lt;(/?(?:sub|sup))&gt;',r'<\1>',html.escape(d['title_html'],quote=False))
        r['display_order']=order;r['display']=d
        r.setdefault('quality',{})['display_parsing_status']='checked_against_original_citation'
        r['quality']['presenter_status']='confirmed' if d['presenter_position'] else 'needs_confirmation'
        r['quality']['display_names_not_identity_verified']=True
    assert len(records)==91
    assert all(r['display']['dates']['start'][:4]==str(r['year']) for r in records)
    assert all(sum(x['highlight'] for x in r['display']['authors'])==1 for r in records)
    expected='〇平野 知之，吉川 潤，荻 崇，管状火炎燃焼を利用した微粒子合成技術の開発，第36回 エアロゾル科学・技術研究討論会，広島，2019年9月4日－6日'
    d=byid['pres-0013']['display'];example='，'.join(['〇'+d['authors'][0]['name']]+[n['name'] for n in d['authors'][1:]]+[d['title_html'],d['conference'],d['location'],d['dates']['text']])
    assert example==expected
    for year,p in packs.items():
        p['schema_version']=2;p['source']='Legacy presentations.md import; original citations preserved'
        (data/f'{year}.yml').write_text(yaml.safe_dump(p,allow_unicode=True,sort_keys=False,width=110),encoding='utf-8')
    inc=root/'_includes';inc.mkdir(exist_ok=True)
    (inc/'presentation-list.html').write_text(TEMPLATE,encoding='utf-8')
    (root/'presentations.md').write_text(PAGE,encoding='utf-8')
    readme=root/'_data/README.md'
    if readme.exists():
        s=readme.read_text();s=s.replace('One 2024 source line appears to contain two concatenated presentations; it is intentionally preserved as one record with `quality.needs_review: true` until manually confirmed.','The owner-confirmed 2024 combined record has been split into pres-0072 and pres-0091; the original is retained in source_before_split.')
        readme.write_text(s.rstrip()+'\n'+DOC,encoding='utf-8')
    guide=root/'EDITING.md'
    if guide.exists():
        s=guide.read_text().replace('| Presentations | `presentations.md` |','| Presentations | `_data/presentations/YYYY.yml` |')
        start=s.index('## Presentationsを追加する');end=s.index('## Grantsを追加する',start)
        s=s[:start]+'''## Presentationsを追加する

発表一覧は `_data/presentations/YYYY.yml` のデータから自動生成されます。
`presentations.md` は表示用なので，そこへ別の一覧を追記しないでください。

既存レコードの `display` を編集すると表示に反映されます。
`display.authors` は著者順，`display.presenter_position` は発表者の位置（1から）です。
発表者が未確認なら `null` にします。筆頭著者から推測しないでください。
`highlight: true` は平野知之の太字・下線に使います。
`display.title_html` は題目，`conference` は学会名，`location` は開催地，
`dates.text` は表示日付です。日付変更時は `dates.start` と `dates.end` も揃えます。
`annotations` は元データで確認できた招待・受賞の注記です。

新規項目は重複しない `id` を付け，`display_order` で掲載順を指定します。
`raw_citation_html` と `citation_text` は旧記載の保存用です。通常は変更しません。
詳しくは `_data/README.md` の Presentation display format を参照してください。

'''+s[end:]
        guide.write_text(s,encoding='utf-8')
    report={'records_before':90,'records_after':len(records),'approved_split':['pres-0072','pres-0091'],
      'presenter_confirmed':sum(r['display']['presenter_position'] is not None for r in records),
      'presenter_unconfirmed':[r['id'] for r in records if r['display']['presenter_position'] is None],
      'source_digests_verified':True,'example_exact_match':True,
      'missing_locations':[r['id'] for r in records if not r['display']['location']]}
    (root/'_presentation_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    print(json.dumps(report,ensure_ascii=False))
    return records

if __name__=='__main__':main()
