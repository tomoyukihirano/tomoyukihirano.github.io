# 個人ホームページ（GitHub Pages / Jekyll）

公開URL：https://tomoyukihirano.github.io/

研究者個人ホームページのソースコードです。GitHub Pages が `main` ブランチの内容を Jekyll でビルドして公開します。旧WordPressの運用環境は不要です。

## 編集するファイル

| 内容 | 主なファイル |
| --- | --- |
| トップ | `index.md` |
| 経歴 | `about.md` |
| 論文一覧 | `publications.md` と `_data/publications/`，`_data/publication_access.yml` |
| 学会発表 | `_data/presentations/`（表示テンプレート：`_includes/presentation-list.html`） |
| 研究費 | `supports-grants.md` |
| 受賞 | `award.md` |
| 研究 | `information.md` |
| 共通メニュー | `_includes/navigation.html` |

編集方法・運用ルールは **[EDITING.md](EDITING.md)** を参照してください。研究業績のデータ構造は **[_data/README.md](_data/README.md)** に説明があります。

## 構成

- `_layouts/`：共通ページ構造
- `_includes/`：共通表示部品
- `_data/`：業績などの管理データ
- `assets/`：ページ固有のCSS・JavaScript，WordPressから移行したスタイル
- `wp-content/`：現在も使用する画像・テーマCSS・フォント
- `schedule-hirano/`，`schedule-lab/`：独立したカレンダーページ
- `author/`，`category/`：過去のURLとの互換性を保つために残しているページ

生成済みサイト（`_site/`）や個人環境の一時ファイルはリポジトリへコミットしません。

## 更新と公開の確認

`main` へのコミット後，GitHub Pages がサイトを生成します。GitHub Actions の `Validate achievement data` と `pages build and deployment` が成功したことを確認してください。公開ページのレイアウト，リンク，絞り込み動作も確認します。

ローカルで Jekyll を使用する場合は別途 Jekyll 環境が必要です。単に `python -m http.server` でソースファイルを配信しても，LiquidテンプレートやMarkdownはビルドされません。

## 公開上の注意

このリポジトリは公開されています。未公開の業績，学内専用情報，認証情報を置かないでください。カレンダー情報の公開範囲は，Google Calendar側の共有設定で管理してください。

旧サイト由来のCSS・画像・フォントは，表示互換性を維持するためのものです。未参照に見えても，古い個別ページや外部リンクから使われる場合があるため，削除前に参照先を確認します。公開ページに直接関係しない過去の作業履歴はGitのコミット履歴に残ります。

BusinessPressやFont Awesomeなどの第三者コンポーネントは，それぞれのライセンス・権利表示に従います。
