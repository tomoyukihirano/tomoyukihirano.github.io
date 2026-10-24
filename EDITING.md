# ホームページの更新方法

このサイトは **GitHub Pages + Jekyll** で公開しています。

普段はHTMLを直接編集せず，以下のMarkdownファイルを編集します。

| 公開ページ | 編集するファイル |
| --- | --- |
| Home | `index.md` |
| About | `about.md` |
| Publications | `publications.md` |
| Presentations | `_data/presentations/YYYY.yml` |
| Grants | `supports-grants.md` |
| Award | `award.md` |
| Research | `information.md` |

## 基本的な更新方法

1. GitHubで編集したい `.md` ファイルを開く
2. 鉛筆アイコン（Edit this file）を押す
3. 先頭の `---` で囲まれた設定部分は通常変更しない
4. その下の本文だけを編集する
5. Commit changes を押す
6. `main` ブランチへの反映後，GitHub PagesがJekyllでHTMLを自動生成して公開する

## Publicationsを追加する

`publications.md` の該当する見出し直下に，次のように1行追加します。

```markdown
1. <span class="publication-citation" id="pub-0079" data-publication-id="pub-0079">著者名, 論文タイトル, ***Journal Name***, 巻, ページ, 年.</span>{% include publication-links.html id="pub-0079" %}
```

番号はすべて `1.` のままで構いません。査読付き論文は採択日の新しい順に並べ，総件数から1へ降順に番号を付けます。
絞り込み後も表示件数から1へ番号を振り直し，一番下が1番になるようにします。

責任著者を示すアスタリスクはMarkdown記号と区別するため，`\*` と書いてください。

タイトルとDOI文字列はリンクにせず，アクセス先は共通デザインの英語ボタンで表示します。
DOI・公開原稿へのリンクは `_data/publication_access.yml` に追加します。
`pub-0079` は例です。`_data/publications/YYYY.yml` のレコードと同じ，重複しないIDを使ってください。
書誌の原文・著者の強調・責任著者記号・年は citation の span 内に保ちます。

```yaml
records:
  pub-0079:
    doi: 10.xxxx/example
    hir_url: https://hiroshima.repo.nii.ac.jp/records/xxxxxxx
    hir_status: open
    hir_version: accepted_manuscript
```

確認済みDOIから `Publisher` ボタンを生成します。個別論文のOA許諾を確認した場合だけ
`publisher_oa: true` と `publisher_license` を登録すると `Publisher (OA)` と表示します。
HiRはPDF直リンクではなく登録ページを `hir_url` に指定し，本文公開を確認して `open` にします。
公開待ちは `hir_status: embargoed` と `hir_release_date: 'YYYY-MM-DD'` を元データで管理します。
公開予定日はページに表示しません。本文公開を確認して状態を更新してください。HiRのボタンは `Repository` です。
ChemRxivは `chemrxiv_url` と `chemrxiv_doi` を登録すると `Preprint` ボタンを生成します。
独立したPreprints節では `is_preprint: true` と `preprint_url` を使い，Publisherボタンは出しません。
PDF本体はサイトに置きません。表示は `_includes/publication-links.html` が共通生成します。

投稿日・採択日・オンライン公開日は従来どおり `_data/publications/YYYY.yml` と `_data/publication_date_reviews.yml` で管理します。
現在の英語日付表記，N/A表示，CSS/JS/日付データの同一ビルド版指定を維持してください。
並び順にはAccepted欄に実際に表示される日付を使います。N/Aは末尾，同日は元の相対順を保ちます。
静的な本文も同じ採択日順にし，日付データの更新時には表示処理が並び順を再調整します。
絞り込みと日付照合は安定IDを使うため，既存IDを掲載順に合わせて変更しないでください。
`first-author/index.html` と `first-corresponding/index.html` も同じIDと共通includeを使います。
ReviewsのIDは `review-0001` 形式です。独立したPreprints節は査読付き論文の総数に含めません。

論文を追加する際は，本文と元データの両方に同じIDのレコードを登録してください。

## Presentationsを追加する

発表一覧は `_data/presentations/YYYY.yml` のデータから自動生成されます。
`presentations.md` は表示用なので，そこへ別の一覧を追記しないでください。

既存レコードの `display` を編集すると表示に反映されます。
`display.authors` は著者順，`display.presenter_position` は発表者の位置（1から）です。
既存91件は，全件で先頭著者が発表者と確認済みのため，`presenter_position: 1` です。
発表者情報は提出用一覧の抽出に使いますが，ホームページには発表者記号を表示しません。
新規追加分は発表者を個別に確認し，未確認なら `null` にします。
`highlight: true` は平野知之の太字・下線に使います。
`display.title_html` は題目，`conference` は学会名，`location` は開催地，
`dates.text` は表示日付です。日付変更時は `dates.start` と `dates.end` も揃えます。
`annotations` は元データで確認できた招待・受賞の注記です。
招待講演は一覧末尾の注記で示し，先頭のバッジや背景色で強調しません。

新規項目は重複しない `id` を付け，`display_order` で掲載順を指定します。
`raw_citation_html` と `citation_text` は旧記載の保存用です。通常は変更しません。
詳しくは `_data/README.md` の Presentation display format を参照してください。

### 掲載時期と確認済み氏名（2026-10-23）

掲載対象は，会期を終えた発表に限ります。個別登壇日が過ぎても会期中は掲載せず，
会期終了後に本人の最終承認を得た項目だけを公開データへ追加します。
開催前の候補は私用の確認待ち一覧で保持し，公開リポジトリには登録しません。
`public: false` でもリポジトリ内の情報は公開されるため，予定情報の保管には使いません。
会期は `display.dates`，個別登壇日は `participation.presentation_date` に分けます。

片岡氏の日本語表示名は「片岡 幹裕」，人物IDは `mikihiro-kataoka` に統一します。
資料にある「片岡 幹弘」は本人承認済みの別表記として `people.yml` の `aliases` に記録します。
取り込んだ原文は保持し，構造化された表示名と人物IDで正規化してください。

### 国際学会の英語表記（2026-10-23）

国際学会に分類された発表は，著者名・題目・学会名・開催地・日付・注記をすべて英語で表示します。
著者名は `people.yml` または確認済みの原資料にある英名を使用し，著者順を保ちます。
片岡氏の英語表示名は `Mikihiro Kataoka` です。
日付は `September 9, 2026`，同月内の会期は `May 11–15, 2026` の形式にします。
月をまたぐ場合は `August 30–September 2, 2026`，年をまたぐ場合は両端に年を記します。
日付の言語変更では，確認済みの `dates.start`・`dates.end` と個別登壇日を変更しません。
招待講演の英語注記は `Invited talk` とします。区切りのコンマと注記の括弧は
`_includes/presentation-list.html` が学会区分に応じて切り替えます。
取り込んだ原文・`dates.source_text`・日本語の人物名辞書は保持します。

## Grantsを追加する

`supports-grants.md` の該当する区分に次のように追記します。

```markdown
- **助成名**（代表）  
  課題名：○○  
  期間：2026/04–2028/03，金額：○○円
```

現在の表示との完全な互換性のため，既存項目の一部では `<br>` などの短いHTML表記を残しています。
見出しは背景色なしの濃紺とし，大見出しの下線と助成機関などの小見出しの左線に青緑を使います。
フォント・文字サイズ・太さ・行間などの基本スタイルは維持します。
見出しとリンクの表示は `assets/grants-palette.css`，リンクの色は `assets/academic-palette.css` で管理します。

## Awardを追加する

`award.md` の番号付きリスト先頭に次のように追加します。

```markdown
1. 平野 知之，受賞名，授与機関，2026/10
```

## Researchを更新する

`information.md` は通常のMarkdownです。

```markdown
## 見出し

- 研究テーマ1
- 研究テーマ2
```

## Aboutを更新する

`about.md` を編集します。

Aboutは写真，外部サービスのボタン，2列の経歴表の見た目を以前と完全に合わせるため，一部にHTMLを残しています。
通常の氏名・所属・経歴の文章更新は `about.md` 内だけで完結します。

## 共通メニューを変更する

Home / About / Publications / Presentations / Grants / Award / Research のPC・スマートフォン共通メニューは，

```text
_includes/navigation.html
```

の1ファイルで管理します。

## ページの外枠

- Home: `_layouts/home.html`
- その他の主要ページ: `_layouts/page.html`

通常の文章更新では触る必要はありません。

## CSS・画像

既存デザインを維持するため，WordPress時代から引き継いだCSSと画像をそのまま利用しています。

- `assets/`
- `wp-content/`

通常の文章・業績更新では触る必要はありません。

## Jekyllとは

JekyllはMarkdown原稿とレイアウトを組み合わせて，公開用HTMLを自動生成する静的サイトジェネレーターです。
このリポジトリでは，GitHub Pages上でJekyllが自動実行されます。


## コミットメッセージの方針

コミットメッセージの件名・本文には人物名を含めません。
例：`Normalize approved author aliases and presentation labels`。
対象者の氏名や別名はデータ本体で管理し，コミットの説明には記載しません。
既存のコミット履歴は，明示的な指示がない限り書き換えません。


## データ修正のまとめ方

関連する確認事項をまとめて提示し，確定した修正を検証して一括反映します。
回答1件ごとに公開ブランチへコミットしません。
人物名をコミットメッセージに含めない方針は継続します。

## 業績の集計設定

`_data/reporting_policy.yml`に分類・集計ルールを保存しています。
研究機関セミナー・展示会講演は学会区分と分け，ホームページの日付は原則として会期を使います。
個別発表日は`participation.presentation_date`です。誌上発表も通常の発表一覧に残します。
受賞情報を無視する指定は`award_reporting: excluded_by_owner`で管理し，受賞していないと断定しません。
IF・JCR Quartileの調査年月は2026年10月です。指標の対象年やJCR版の年は未確認です。
Top10%は論文被引用数による区分であり，評価分野の一つでも該当すれば採用します。
Q1も評価分野の一つでも該当すれば採用します。既存の指標値自体は変更していません。
主指導学生の業績の範囲は出力時に選択し，選択値を出力記録に残します。自動出力機能は別途実装します。
