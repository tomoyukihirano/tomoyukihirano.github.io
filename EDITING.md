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

1. WindowsのCodexでこの作業フォルダを開き，`AGENTS.md` と本ガイドを読む
2. `git status --short --branch` で変更を確認し，`git switch -c codex/<作業名>` でローカル作業ブランチを作る
3. 対象のMarkdownやデータを編集する。先頭の `---` で囲まれた設定部分は通常変更しない
4. `.\scripts\site.ps1 Validate` でビルドし，`.\scripts\site.ps1 Preview` で表示・リンク・絞り込みを確認する
5. 差分と検証結果を確認する。コミットメッセージには人物名を含めない
6. push・`main` への統合・公開は本人の確認後に実施する。リモートの `main` への反映後，GitHub PagesがHTMLを生成・公開する

## Windowsでのローカル運用

作業フォルダ：`C:\Users\hirano\Documents\GitHub\tomoyukihirano.github.io`

PowerShell 7（`pwsh`）を使います（動作確認：Windows / PowerShell 7.6.5）。
Windows標準のWindows PowerShell 5.1ではなく，CodexのPowerShell 7ターミナルで実行してください。
初回はインターネット接続が必要です。

```powershell
Set-Location 'C:\Users\hirano\Documents\GitHub\tomoyukihirano.github.io'
.\scripts\site.ps1 Setup
.\scripts\site.ps1 Validate
.\scripts\site.ps1 Preview
```

| コマンド | 処理 |
| --- | --- |
| `Setup` | 公式Ruby+Devkitの取得・SHA256照合・ユーザー用導入と，lockfileに従うgemのインストール |
| `Validate` | `JEKYLL_ENV=production` で `bundle exec github-pages build` を実行。出力先 `_site/` |
| `Build` | `Validate` と同じビルド（別の追加検査はない） |
| `Preview` | `bundle exec jekyll serve` で監視・配信。出力先 `_site-preview/` |

通常の編集では `Validate` → `Preview` で確認します。プレビュー中の本文変更は自動ビルドされるため，ブラウザーを再読み込みします。
`_config.yml` やGemfileの変更後はサーバーを再起動してください。依存関係を取得し直すときは `Setup` を実行します。

プレビューは **http://127.0.0.1:4000/** です。ループバックにだけバインドし，外部へ公開しません。
停止は起動したターミナルの `Ctrl+C`。ポートが使用中なら次のように変更します。

```powershell
.\scripts\site.ps1 Preview -Port 4001
```

表示確認先：`/`，`/about/`，`/publications/`，`/presentations/`，`/supports-grants/`，`/award/`，`/information/`。
Publications / Presentationsの絞り込みとリセット，論文日付・内部リンクも確認します。
カレンダー等の外部サービスは別途ネット接続が必要です。既存ページの外部リンクやAnalyticsもそのままなので，ローカル表示でも外部への通信が発生する場合があります。

### バージョンと保存場所

- Ruby **3.3.13**（RubyInstaller+Devkit 3.3.13-1 x64）：`.ruby-version` とスクリプトで固定。
  GemfileはPagesコンテナのパッチ差を許容するためRuby 3.3系を指定。
- Bundler **2.5.22**：スクリプトと `Gemfile.lock` で固定。
- github-pages **232** / Jekyll **3.10.0**：既存の `actions/jekyll-build-pages@v1` に合わせる。
  Actionが追加する `jekyll-include-cache` と `jekyll-octicons` も含める。
- 推移的な依存関係は `Gemfile.lock` を保存し，通常のSetupでも変更しない。
  Actionの可変タグが将来更新された場合は差異を確認してから更新する。
- RubyとDevkitは `.tools/ruby33/`，gemは `vendor/bundle/`，Bundler設定・キャッシュは `.bundle/`。
  ダウンロードしたインストーラーは `.tools/downloads/`。いずれもGit管理対象外。
- Setupはユーザー用インストールとしてWindowsに登録されるが，PATHと `.rb` の関連付けは変更しない。
  初回に同梱MSYS2の鍵を初期化する。RubyInstaller自身もRubyGemsの設定ファイルを作成する。
- スクリプトは自分のプロセス内でUTF-8と実行環境を設定し，終了時に元へ戻す。
  `_config.yml` の公開URL・baseurlはローカル用に書き換えない。
- Windowsの監視は `--force_polling` を使い，追加の `wdm` は不要。
  `_site/` も除外し，別ターミナルでValidateした際にプレビューの再生成が連続しないようにする。

バージョンの根拠：
[GitHub Pages依存関係](https://pages.github.com/versions/)，
[ActionのGemfile](https://github.com/actions/jekyll-build-pages/blob/v1/Gemfile)，
[Actionの実行処理](https://github.com/actions/jekyll-build-pages/blob/v1/entrypoint.sh)，
[RubyInstallerの導入オプション](https://github.com/oneclick/rubyinstaller2/wiki/FAQ#q-how-do-i-perform-a-silentunattended-install-with-the-rubyinstaller)。

### 困ったとき

- Ruby / gemがない，依存関係不足：まず `Setup` を実行する。
- lockfile不整合：`Gemfile` と `Gemfile.lock` の差分を確認する。検証を通すためだけに `bundle update` や凍結解除をしない。
- SHA256不一致：該当の `.tools/downloads/` 内のインストーラーだけを削除して再取得する。
  ハッシュ検証やTLS検証を無効にしない。
- 日本語の文字化け：ファイルはUTF-8（BOMなし）で保存する。スクリプトがRubyのUTF-8設定を適用する。
- 実行ポリシーで `.ps1` が拒否された場合：組織のルールを確認し，マシン全体のポリシーを変更しない。
  ダウンロード扱いのファイルは内容確認後に必要なファイルだけ `Unblock-File` で解除する。
- Codexの制限で `.git` の書き込みや外部ダウンロードが拒否された場合は，必要な操作だけ権限を要求する。
  プレビューのログが起動成功でもブラウザー接続がタイムアウトする場合は，サーバーを停止し，
  ネットワーク制限外で同じPreviewコマンドを起動する（待受先は `127.0.0.1` を維持）。
  通常のビルド・プレビューにGitHubへの書き込み権限やトークンは不要。
- `bigdecimal` のRuby 3.4以降に関する警告と，Faradayの任意の再試行gemの案内は現在の依存関係で表示される。
  固定したRuby 3.3.13ではビルド・プレビュー成功を確認済み。警告を消すためだけに依存関係を更新しない。

### GitHub Pagesと独自検証Actionsの違い

`.github/workflows/validate-achievement-data.yml` は，checkout → `actions/configure-pages@v5` →
`actions/jekyll-build-pages@v1` で `_site/` を生成する **追加のビルド検証** です。
名前にdataを含みますが，独立した業績データのスキーマ検証・ID照合は実装されていません。
ローカルの `Validate` は同じgithub-pagesのビルド入口を使ってYAML・Liquid・Markdownの処理を確認します。
GitHub上の設定・権限を読む `configure-pages`，Linuxコンテナ，公開処理そのものは再現しません。

この検証Actionは `main` と `data/**` へのpushのうち，`_data/**`・`_layouts/**`・`_includes/**`・`*.md` が対象です。
`codex/**`・PR・手動実行は現在のトリガーに含まれません。Actionsを実行するためのpushは行いません。

`pages build and deployment` は **GitHub Pages固有のビルド・公開** です。
ブランチ公開でもGitHub側ではActionsの公開処理が走ります。
ローカルで検証できても，現在の公開方式を続けるためにこの処理は必要です。
独自検証Actionは公開自体には必須ではありませんが，サーバー側の追加確認として今回は維持します。
どちらも削除・無効化・新規作成・手動実行せず，公開設定も変更しません。
今後，公開承認後の反映時に成功と公開ページを確認します。
仕様の根拠：[GitHub Pagesの公開元](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site)。

### 導入時の確認結果（2026-10-29）

- 開始時：`main` / `84e2adf`，未コミット変更なし。ローカルブランチ `codex/windows-local-jekyll` を作成。
- Ruby 3.3.13 / Bundler 2.5.22 / github-pages 232 / Jekyll 3.10.0，100 gemsの導入に成功。
  Windows用のlockにLinux用の解決情報も記録（Linux上での実行は未実施）。
- PowerShell 7.6.5でSetupの再実行，Validateのproductionビルド，Previewの起動に成功。
  lockfile不変，実行後の環境変数・作業フォルダ復元，PowerShell構文検査，`git diff --check` を確認。
- **http://127.0.0.1:4000/** で主要7ページをブラウザー表示確認。
  筆頭著者一覧・筆頭/責任著者一覧・予定2ページもHTTP 200。
- 主要ページのCSS・JS・画像・フォント・日付JSONを含む49個のローカルリソースがHTTP 200。
- Publications：全79件 → 筆頭著者12件 → 2026年の筆頭著者1件 → 全79件に復帰。
  英語日付・N/A表示も確認。Presentations：全112件 / 国内86件 / 国際21件の切替と復帰を確認。
- ローカルツール・ガイド・gem・プレビュー出力がproductionの `_site/` に混入しないことを確認。
- ページ本文・業績データ・レイアウト・CSS・画像・既存workflowは変更していない。
  push，main統合，リモート公開設定変更，Actionsの作成・削除・無効化・手動実行は未実施。
- GitHub側の公開・公開後の表示確認，カレンダー内の外部データの内容確認はこの作業の対象外。

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
