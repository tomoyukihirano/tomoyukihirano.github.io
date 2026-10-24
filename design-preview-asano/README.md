# Asano / al-folio風の個人HPプレビュー

[Yuki M. Asano氏のサイト](https://yukimasano.github.io/)と[Publications](https://yukimasano.github.io/publications/)の構成・余白・文字組みを参考にした，独立した別案です。
Home / About / Research / Publications / Presentations / Grants / Awardの7画面を，1つのHTMLへまとめています。
**初期画面はHome**です。既存のFukushima案は保持し，本案は `design-preview-asano/` に分けています。

本案の作業ブランチは `preview/asano-personal-20261024` です。
**現時点では未公開**であり，本番の `main`，GitHub Pages設定，公開用ワークフローは変更しません。
今回参照した公開ソースは [tomoyukihirano/tomoyukihirano.github.io](https://github.com/tomoyukihirano/tomoyukihirano.github.io) の `main`，
コミット `b57063b5e6b9b1c980bb83446697deeafbf1aab3` です。

## 見た目と操作

- コンテナーは最大800px，左右15pxの余白を除いた本文幅は最大770pxです。固定ヘッダー，軽い見出し，右寄せの年見出し，コンパクトな文献行を使用します。
- Robotoのnormal 300・400・500・700をHTMLへ内包します。日本語は既存のシステムフォントへフォールバックします。
- 既存の花の配色を保持します。本文はネイビー `#183d58`，リンクはティール `#356d7e`，補助色はラベンダーピンク `#cec0d2`，ブルーグレー `#688c9c`，ディープティール `#1e4b62` です。
- 論文ごとの図・サムネイル・画像列は表示しません。Homeの火炎写真と，Home／Aboutのプロフィール写真は既存ファイルを利用します。
- ヘッダーで7画面を切り替え，`?page=...` とブラウザの戻る・進むに対応します。スマートフォンではメニューボタンを使用します。

| 画面 | パラメーター | 内容 |
| --- | --- | --- |
| Home | `?page=home` | プロフィール，連絡先，写真，研究概要，火炎プロセス |
| About | `?page=about` | プロフィール，連絡先，外部プロフィール，経歴 |
| Research | `?page=research` | 現在と以前の研究テーマ |
| Publications | `?page=publications` | 論文・総説・プレプリント，書籍・その他 |
| Presentations | `?page=presentations` | 公開済み発表の年別一覧と検索 |
| Grants | `?page=grants` | 研究費，共同研究，奨学金 |
| Award | `?page=award` | 受賞一覧 |

Publicationsでは，コレクションのピル型ボタンから全件・論文・総説・プレプリント・筆頭著者・筆頭または責任著者を選べます。
`Search & filters` を開くと，キーワード，年，種別，著者役割，並べ替えを利用できます。
右端の行番号は**表示中のN件から1まで**とし，検索・絞り込み・並べ替えのたびに振り直します。
番号からのリンク先には既存の安定IDを使い，表示番号をIDとして保存しません。

`Publication statistics` は折りたたみ式のワッフルグラフです。1レコードを1つの四角で表し，検索・絞り込みと連動します。
本人が筆頭著者または責任著者ならピンク，その他の共著はグレーです。両方の役割を持つ論文も1件として数えます。
In press・刊行年未登録は年の列と分け，書籍・その他は原文をページ下部へ引き継ぎます。
Presentationsではキーワード・年・招待区分・国内／国際区分を使い，表示中の件数に応じた逆順番号を表示します。

## 元データの扱い

公開データを読み取り専用で利用します。生成HTML・JSONは表示用の成果物であり，編集用の正本にはしません。

- 論文の正本は `_data/publications/*.yml` と `publications.md` です。安定ID，著者順・役割，化学式，引用原文を保持します。
- `_data/publication_access.yml`，`_data/publication_date_reviews.yml`，`_data/journals.yml`，`_data/people.yml` の公開登録値とURLを引き継ぎます。IF・JCR Quartile・Top10%と日付を表示側で補完・推測しません。
- 発表は `_data/presentations/*.yml` と `_data/presentation_scopes.yml` を使用し，原文の `display` を保持します。化学式は `_includes/chemical-formula.html` の規則を利用します。
- 他の画面は `index.md`，`about.md`，`information.md`，`supports-grants.md`，`award.md` と既存画像から生成します。
- `presentation.yml` は，既存の論文IDに対する `summary`，`topics`，`selected` の追加表示設定です。題名・著者・日付・DOI・指標の上書きには使用しません。`selected` は現在の表示切替には使いません。
- 非公開の学生・指導関係データは入力・出力に含めません。既存データセットは変更せず，ビルド前後の入力ハッシュを照合します。

## 再ビルド

Python 3.10以降とPyYAMLが必要です。リポジトリのルートから実行します。
公開データの更新時は，最新の `main` を取得した別チェックアウトを `--source` に指定すると，旧プレビューブランチ内のデータを再利用せずに再生成できます。

```bash
python3 -m pip install -r design-preview-asano/requirements.txt
python3 design-preview-asano/build.py --source /path/to/public-main-checkout --output design-preview-asano/dist/index.html
```

同じチェックアウトを公開ソースとして使う場合は `--source .` とします。Git管理された入力では，実際の `HEAD` を出典コミットとして自動記録します。
Git管理のないスナップショットでは，そのスナップショットに対応する完全なSHAを必ず渡します。

```bash
python3 design-preview-asano/build.py --source /path/to/public-source-snapshot --output design-preview-asano/dist/index.html --commit b57063b5e6b9b1c980bb83446697deeafbf1aab3
```

上記SHAは今回の入力版です。新しいスナップショットには実際の新しいSHAを指定してください。
入力には前節のMarkdown・YAML・化学式includeに加え，以下の画像が必要です。

- `wp-content/uploads/2024/03/240329_Hirano_2.jpg`
- `wp-content/uploads/2025/03/アセット-1@600x-8-1024x629.png`

ビルド自体はネットワークへ問い合わせません。生成した `design-preview-asano/dist/index.html` をブラウザで開くと，Webサーバーなしで7画面と検索を利用できます。
CSS・JavaScript・表示データ・Roboto・既存画像・第三者ライセンスをHTMLへ内包します。JavaScript無効時は全画面の本文と業績一覧を続けて表示します。

## フォントと帰属表示

Gitへ含めるフォント関連ファイルは `font-faces.css`，`assets/fonts/OFL.txt`，`assets/fonts/README.md`，`assets/fonts/build-metadata.json` です。
WOFF2は `font-faces.css` 内のdata URIに含まれるため，個別のバイナリファイルは再ビルドに不要です。
公式出典と変換条件は [フォントREADME](assets/fonts/README.md)，al-folio由来のMITライセンスと既存の帰属表示は [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) を参照してください。
研究内容・元の写真・業績データの権利は元の権利者に残り，参照サイトの研究内容や人物写真は取り込んでいません。
