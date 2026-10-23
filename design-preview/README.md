# 独立した個人HPデザインプレビュー

Fukushima Labの実画面にできるだけ揃えた，論文図なしの個人HPデザインプレビューです。
本文幅950px（左右余白を含む），固定ヘッダー，40pxの軽い見出し，検索・3つの絞り込み，
その下の横長グラフ，右寄せの年見出し，種別ラベルをタイトルの横に置く論文行を採用しています。
Home / About / Research / Publications / Presentations / Grants / Awardの7画面を，
1つのHTMLファイルにまとめています。現在のGitHub Pagesとは別に確認・調整するための版です。
本番ページ，GitHub Pages設定，公開用ワークフローは変更していません。

## ページと操作

初期表示はPublicationsです。ヘッダーのメニューは同じプレビュー内の画面を切り替えます。
画面は `?page=...` で指定でき，ブラウザの戻る・進むにも対応します。

| ページ | パラメーター | 内容 |
| --- | --- | --- |
| Home | `?page=home` | 現在の紹介文，火炎写真，3種類の火炎プロセス |
| About | `?page=about` | プロフィール，写真，連絡先，外部プロフィール，経歴表 |
| Research | `?page=research` | 現在と以前の研究テーマ |
| Publications | `?page=publications` | 論文・総説・プレプリント，書籍・その他の業績 |
| Presentations | `?page=presentations` | 公開済み発表の年別一覧，検索・絞り込み |
| Grants | `?page=grants` | 進行中・終了した研究費，共同研究，奨学金 |
| Award | `?page=award` | 現在の受賞一覧と逆順の番号 |

外部プロフィール，論文のアクセス先，フッターの現在のHPへのリンクは，元の外部URLを開きます。
本文，経歴，研究課題名，期間，金額，受賞記載は現在の公開ソースから引き継ぎます。
Homeの火炎写真とAboutのプロフィール写真も既存ファイルをHTMLへ埋め込みます。

### Publications

- 安定ID，著者順，化学式，引用原文，DOI・Repository・Preprintのリンクを引き継ぎます。
- キーワード，刊行年，種別，筆頭著者／筆頭または責任著者で絞り込めます。刊行年の新しい順／古い順も切り替えられます。
- 論文ごとの図，サムネイル，誌名タイルは表示しません。
- Number of publicationsは，**1レコードを1つの四角いブロック**として年ごとに積み上げます。
  参考と同じ横長グラフとし，上部の凡例，縦軸の目盛り，年ラベルを付けています。
- All authorshipsでは，本人が**筆頭著者または責任著者ならピンク**，それ以外の共著は**グレー**です。
  両方の役割を持つ論文も1つの四角として数えます。
- グラフは検索・絞り込みと連動します。年の列を選ぶとその年で絞り込めます。
  In pressと刊行年未登録の項目は年の列と分けて表示します。
- グラフの対象は論文・総説・プレプリントです。書籍・その他はページ下部に原文を表示します。
- 日付の確認状態と，IF・JCR Quartile・Top10%の既存登録値を利用します。
- ヘッダーのTomoyukiは通常の太さとし，Publications見出しの末尾にピリオドは付けません。

### Presentations

- `_data/presentations/*.yml` の公開済みレコードから，年別の発表一覧を生成します。
- キーワード，年，招待講演，国内／国際学会で絞り込めます。
- All presentationsには，セミナー・勉強会・展示会講演なども含めます。
- 著者名と順序，題目，学会名，開催地，会期，注記は既存の `display` を使用します。
  発表者，招待区分，日付，英語表記を表示側で推定しません。
- 国内／国際の区分には既存の分類と `_data/presentation_scopes.yml` を使用します。
  発表データは論文の追加表示設定 `presentation.yml` とは別です。

## 元データは共通のまま使う

| 内容 | 正本 |
| --- | --- |
| 論文ID，著者ID，役割，分類，日付 | `_data/publications/*.yml` |
| 現在の引用表記，総説，プレプリント，書籍・その他 | `publications.md` |
| DOI・OA・機関リポジトリ・プレプリントURL | `_data/publication_access.yml` |
| 日付の確認状態 | `_data/publication_date_reviews.yml` |
| IF・JCR Quartileと調査年月 | `_data/journals.yml` |
| 表記照合に利用する公開人物情報 | `_data/people.yml`，公開済み発表データ |
| 発表ID，表示内容，分類，招待区分 | `_data/presentations/*.yml` |
| 発表の国内／国際等の区分 | `_data/presentation_scopes.yml` |
| 発表題目の化学式の表示規則 | `_includes/chemical-formula.html` |
| Home / About / Researchの本文 | `index.md`，`about.md`，`information.md` |
| 研究費・奨学金と受賞情報 | `supports-grants.md`，`award.md` |
| Home / Aboutの写真 | 現在の `wp-content/uploads/` 内の該当画像 |
| 論文の追加説明・テーマ・代表業績フラグ | このフォルダーの `presentation.yml` |

`build_data.py`，`presentation_page.py`，`site_pages.py` は公開ソースを読み取り専用で利用します。
生成されたJSONやHTMLは表示用の成果物であり，編集用データベースにはしません。
非公開の学生・指導関係データは読み込まず，出力にも含めません。

論文の著者・題名・誌名を安全に分割できない場合は，現在の引用全文を表示します。
元DBと原文は表示に合わせて書き換えません。
Book Chaptersは原文に同一書籍の別章が含まれるため，画面では見出しの件数を省き，
全項目を引き継ぎます。元の見出しも生成データに保存されます。

## 作成する

Python 3.10以降とPyYAMLが必要です。ネットワーク問い合わせは行いません。
リポジトリのルートから実行します。

```bash
python3 -m pip install -r design-preview/requirements.txt
python3 design-preview/build.py --source . --output design-preview/dist/index.html
```

生成された `design-preview/dist/index.html` をブラウザで開くと，7画面の移動と検索・絞り込みを利用できます。
CSS・JavaScript・表示データ・既存のHome/About画像を内包しているので，Webサーバーは不要です。
JavaScriptが無効な場合は，全ページの本文と業績一覧を続けて表示します。
スマートフォン幅とキーボード操作に対応しています。狭い画面ではヘッダーのメニューボタンから各ページを開きます。

Git管理のない読み取り用スナップショットを使う場合は，取得元の正確なコミットを指定します。

```bash
python3 design-preview/build.py --source /path/to/source-snapshot --output /path/to/preview.html --commit a8bdb8f7f270e73704301171ddcd0eee596ae9e1
```

上記SHAは今回読み取った公開ソースの版です。新しいデータを使う場合は実際のSHAへ変更します。
スナップショットには上記のMarkdown・YAML・化学式include・既存の2枚の写真を含めます。
元データ，ページ本文，写真などのハッシュは生成時に保存し，ビルド中に入力ファイルが変更されていないことも検証します。

## 見た目だけの情報を追加する

`presentation.yml` の `records` に，既存の安定IDをキーにして設定します。
追加できるのは `summary`，`topics`，`selected` のみです。
タイトル・著者・日付・DOI・評価値はここで上書きできません。

`summary` と `topics` は論文行に表示され，テーマ語はキーワード検索にも含まれます。
`selected` は今後の代表業績表示用として保存する項目で，現在は表示を切り替えません。
既存IDに対する追加情報のみを設定し，確認済みの内容を記入します。

## 評価指標・日付の扱い

- 既存指標の確認年月は2026年10月です。指標対象年やJCR版の年と混同しません。
- Top10%は論文被引用数の区分です。雑誌ランキングのQ1とは別の値です。
- 未登録の日付や確認が必要な日付はN/Aとし，不一致の日付を確定値として出しません。
- リポジトリの公開予定日は表示しません。公開状態は正本側で管理します。
- In pressは刊行年と分けます。年が確認できない項目もIn pressへ混ぜません。

## 継続作業と公開

作業を続ける際は，最新の正本データを読み込んでプレビューを再生成します。
このブランチの古い `_data` を本番の新しいデータに上書きしないでください。
7画面はプレビュー内で確認できます。内容とレイアウトを調整し，公開を明示的に指示された後に
本番への切替方法を決めます。現在の版を生成しただけでは公開サイトは切り替わりません。

このフォルダーには自動公開用のワークフローを追加していません。
本番の `main`，既存ページ，GitHub Pages設定，公開用ワークフローへの変更は今回の対象外です。

## 参照したデザイン

- [Fukushima Lab Publications](https://kenji-fukushima-lab.github.io/publications/)
- [Fukushima Lab source](https://github.com/kenji-fukushima-lab/kenji-fukushima-lab.github.io)
- [Yuki M. Asano Publications](https://yukimasano.github.io/publications/)
- [multi-language-al-folio](https://github.com/george-gca/multi-language-al-folio)

Fukushima Labとそのベースであるmulti-language-al-folioの見た目を参考にし，
既存データ形式へ合わせて独立した表示実装を作成しています。
Fukushima Labの個別研究内容・論文画像・メンバー管理・PDF申請・解析設定は取り込んでいません。
参照元のライセンスと帰属情報は `THIRD_PARTY_NOTICES.md` に記録します。
