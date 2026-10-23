# 独立した個人HPデザインプレビュー

Fukushima LabのPublicationsを主な視覚参考にした，個人用Publicationsの初期表示案です。
現在のGitHub Pagesとは独立したプレビューブランチで作成しています。
このフォルダーを追加するだけでは公開先や既存ページは切り替わりません。

## 今回の範囲

- 対象はPublicationsページです。他のナビゲーションは現在の公開HPへ移動します。
- 既存の安定IDを保ち，論文・総説・プレプリントを年別に表示します。
- キーワード，刊行年，種別，本人の筆頭／筆頭または責任著者で絞り込めます。
- 著者表記，化学式，引用原文，DOI・Repository・Preprintのリンクを引き継ぎます。
- 日付の確認状態と，IF・JCR Quartile・Top10%の既存登録値を利用します。
- スマートフォン幅とキーボード操作に対応します。
- 書籍・その他の既存記載もページ下部で表示できます。
- 現在の版には論文の図を追加していません。画像のない論文は誌名タイルを表示します。

## 元データは共通のまま使う

| 内容 | 正本 |
| --- | --- |
| 論文ID，著者ID，役割，分類，日付 | `_data/publications/*.yml` |
| 現在の引用表記，総説，プレプリント，書籍・その他 | `publications.md` |
| DOI・OA・機関リポジトリ・プレプリントURL | `_data/publication_access.yml` |
| 日付の確認状態 | `_data/publication_date_reviews.yml` |
| IF・JCR Quartileと調査年月 | `_data/journals.yml` |
| 表記照合に利用する公開人物情報 | `_data/people.yml`，公開済み発表データ |
| 新デザインだけの画像・説明・テーマ | このフォルダーの `presentation.yml` |

`build_data.py` は公開データを読み取り専用で結合します。
生成されたJSONやHTMLは表示用の成果物であり，編集用データベースにはしません。
非公開の学生・指導関係データは読み込まず，出力にも含めません。

論文の著者・題名・誌名を安全に分割できない場合は，現在の引用全文を表示します。
初版の `pub-0060` と `pub-0009` はこの扱いです。元DBと原文を勝手に修正しません。
Book Chaptersは原文に同一書籍の別章が含まれるため，画面では見出しの件数を省き，
全項目を引き継ぎます。元の見出しも生成データに保存されます。

## 作成する

Python 3.10以降とPyYAMLが必要です。ネットワーク問い合わせは行いません。
リポジトリのルートから実行します。

```bash
python3 -m pip install -r design-preview/requirements.txt
python3 design-preview/build.py --source . --output design-preview/dist/index.html
```

生成された `design-preview/dist/index.html` をブラウザで開くと検索・絞り込みを利用できます。
CSS・JavaScript・表示データを内包しているので，Webサーバーは不要です。
JavaScriptが無効でも業績一覧と外部リンクは表示されます。

Git管理のない読み取り用スナップショットを使う場合は，取得元の正確なコミットを指定します。

```bash
python3 design-preview/build.py --source /path/to/source-snapshot --output /path/to/preview.html --commit c58336e6c7962c8c8d6c455189ad4859fa63fed1
```

上記SHAは初版で読み取った公開データの版です。新しいデータを使う場合は実際のSHAへ変更します。
元データのハッシュは生成時に保存され，入力ファイルが変更されていないことも検証します。

## 見た目だけの情報を追加する

`presentation.yml` の `records` に，既存の安定IDをキーにして設定します。
追加できるのは `thumbnail`，`thumbnail_alt`，`summary`，`topics`，`selected` のみです。
タイトル・著者・日付・DOI・評価値はここで上書きできません。

画像はリポジトリ内のPNG/JPEG/WebP/AVIF/GIFを指定し，内容を説明する代替テキストを付けます。
ビルド時にHTMLへ埋め込まれるため，相対パスの異なるプレビュー先でも表示できます。
`summary` と `topics` は論文行に表示され，テーマ語はキーワード検索にも含まれます。
`selected` は今後の代表業績ページ用として保存する項目で，この初版では表示を切り替えません。
テーマ別ボタン，日本語・英語の切替，Home等への展開は次のデザイン段階で実装できます。

## 評価指標・日付の扱い

- 既存指標の確認年月は2026年10月です。指標対象年やJCR版の年と混同しません。
- Top10%は論文被引用数の区分です。雑誌ランキングのQ1とは別の値です。
- 未登録の日付や確認が必要な日付はN/Aとし，不一致の日付を確定値として出しません。
- リポジトリの公開予定日は表示しません。公開状態は正本側で管理します。
- In pressは刊行年と分けます。年が確認できない項目もIn pressへ混ぜません。

## 継続作業と公開

作業を続ける際は，最新の正本データを読み込んでプレビューを再生成します。
このブランチの古い `_data` を本番の新しいデータに上書きしないでください。
Home，About，Research，Presentations，Grants，Awardへ同じ表示設計を展開し，
内容とレイアウトを確認してから本番の切替を判断します。

GitHub Pagesには1リポジトリにつき1つの公開先という制約があります。
別ブランチの作成だけでは別の公開URLはできません。
独立したGitHub Pagesの公開URLが必要になった段階で，別リポジトリと明示的な公開設定を使います。
この初版にはデプロイ用ワークフローやPages設定変更を含めていません。

## 参照したデザイン

- [Fukushima Lab Publications](https://kenji-fukushima-lab.github.io/publications/)
- [Fukushima Lab source](https://github.com/kenji-fukushima-lab/kenji-fukushima-lab.github.io)
- [Yuki M. Asano Publications](https://yukimasano.github.io/publications/)
- [multi-language-al-folio](https://github.com/george-gca/multi-language-al-folio)

初版は既存データ形式へ合わせた独立した表示実装です。
Fukushima Labの個別研究内容・論文画像・メンバー管理・PDF申請・解析設定は取り込んでいません。
参照元のライセンスと帰属情報は `THIRD_PARTY_NOTICES.md` に記録します。
