# ホームページの更新方法

このサイトは **GitHub Pages + Jekyll** で公開しています。

普段はHTMLを直接編集せず，以下のMarkdownファイルを編集します。

| 公開ページ | 編集するファイル |
| --- | --- |
| Home | `index.md` |
| About | `about.md` |
| Publications | `publications.md` |
| Presentations | `presentations.md` |
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
1. 著者名, 論文タイトル, ***Journal Name***, 巻, ページ, 年.
```

番号はすべて `1.` のままで構いません。公開時には逆順の番号付きリストとして表示されます。

責任著者を示すアスタリスクはMarkdown記号と区別するため，`\*` と書いてください。

リンクは次の書き方で追加できます。

```markdown
[論文タイトル](https://doi.org/...)
```

## Presentationsを追加する

`presentations.md` のリスト先頭に次のように追記します。

```markdown
1. 著者名，発表題目，学会名，開催地，日付
```

## Grantsを追加する

`supports-grants.md` の該当する区分に次のように追記します。

```markdown
- **助成名**（代表）  
  課題名：○○  
  期間：2026/04–2028/03，金額：○○円
```

現在の表示との完全な互換性のため，既存項目の一部では `<br>` などの短いHTML表記を残しています。

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


## 発表・論文の絞り込み表示

Presentationsは `_data/presentations/YYYY.yml` の `scope`（`domestic` / `international`）と `classification.invited` を使って自動表示します。表示用の統一表記は `display_html`，元データは `citation_text` / `raw_citation_html` に残します。

Publicationsページの「全論文」「筆頭著者」「筆頭著者・責任著者」は `_data/publications/YYYY.yml` の `classification.hirano_first_author` と `classification.hirano_corresponding` に基づいて切り替わります。
