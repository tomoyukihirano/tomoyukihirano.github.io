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
1. 著者名, 論文タイトル, ***Journal Name***, 巻, ページ, 年.
```

番号はすべて `1.` のままで構いません。公開時には逆順の番号付きリストとして表示されます。

責任著者を示すアスタリスクはMarkdown記号と区別するため，`\*` と書いてください。

リンクは次の書き方で追加できます。

```markdown
[論文タイトル](https://doi.org/...)
```

## Presentationsを追加する

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
