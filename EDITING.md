# ホームページの更新方法

このリポジトリは GitHub Pages + Jekyll で公開します。

## Homeを更新する

Homeの本文は `index.md` です。

1. GitHubで `index.md` を開く
2. 鉛筆アイコン（Edit this file）を押す
3. YAMLフロントマター（先頭の `---` で囲まれた部分）は通常変更しない
4. その下の本文だけを編集する
5. Commit changes を押す

`main` ブランチへの反映後，GitHub Pagesが自動でHTMLを生成して公開します。

## メニューを変更する

Markdown化したページでは，PC・スマートフォン共通のメニューを `_includes/navigation.html` の1ファイルで管理します。
現時点ではHomeだけがこの共通メニューを使用しています。Aboutなど既存HTMLページは段階的に移行するため，サイト全体のメニューが完全に1ファイル管理になるのは移行完了後です。

## Homeの外枠・デザイン

Homeのヘッダー，フッター，読み込むCSSなどは `_layouts/home.html` です。
通常の文章更新では触る必要はありません。

デザインは既存の `assets/` と `wp-content/` 内のCSS・画像をそのまま利用しています。

## 現在の移行状況

- Home: Markdown化済み
- About: 既存HTML（次段階でMarkdown化）
- Publications: 既存HTML（次段階でMarkdown化）
- Presentations: 既存HTML（次段階でMarkdown化）
- Grants: 既存HTML（次段階でMarkdown化）
- Award: 既存HTML（次段階でMarkdown化）
- Research: 既存HTML（次段階でMarkdown化）

移行は表示を変えないことを優先し，ページ単位で行います。
