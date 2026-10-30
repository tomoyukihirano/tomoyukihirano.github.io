# このリポジトリでの作業

研究者の個人ホームページ（GitHub Pages / Jekyll）です。説明・完了報告は日本語で行います。
最初に本ファイル，`README.md`，`EDITING.md`，`_data/README.md`，`_config.yml`，
`.github/workflows/` を読み，既存の内容・デザイン・運用ルールを引き継いでください。

## ローカル作業と公開の境界

- WindowsのCodexでコードの修正，検証，ビルド，プレビューまで実施します。
- 作業前に `git status --short --branch` を確認し，未コミット変更を保護します。
  新しい作業は `codex/<内容>` のローカルブランチで行います。
- push，`main` への統合，公開・Pages設定の変更は，ユーザーの確認後に実施します。
  ローカル環境の整備や編集の依頼を，公開操作の許可と解釈しないでください。
- Actionsの削除・無効化・新規作成・手動実行は別途依頼がある場合に限ります。
- コミットメッセージの件名・本文に人物名を含めません。
- `_site/`，`_site-preview/`，`.tools/`，`vendor/`，`.bundle/`，ログや認証情報をコミットしません。

## Windowsのコマンド

リポジトリのルートでPowerShell 7（`pwsh`）を使用します。動作確認環境は7.6.5です。

```powershell
.\scripts\site.ps1 Setup      # 初回 / Gemfile.lock変更後（ネット接続が必要）
.\scripts\site.ps1 Validate   # production設定でPages互換ビルド → _site/
.\scripts\site.ps1 Build      # Validateと同じ処理
.\scripts\site.ps1 Preview    # http://127.0.0.1:4000/，Ctrl+Cで停止
# 別ポート: .\scripts\site.ps1 Preview -Port 4001
```

- Ruby 3.3.13，Bundler 2.5.22，github-pages 232（Jekyll 3.10.0）を固定しています。
  `.ruby-version`，`Gemfile`，`Gemfile.lock` を優先し，無断で最新版へ更新しません。
- Setupは公式RubyInstaller+DevkitをSHA256照合後 `.tools/ruby33/` にユーザー用として導入します。
  OS全体のPATHやRubyの関連付けは変更しません。gemは `vendor/bundle/` に置きます。
- スクリプトはRubyのUTF-8設定を適用し，環境変数と作業ディレクトリを終了時に戻します。
  通常の検証でlockfileを更新せず，不整合は失敗として報告します。
- `Validate` はActionsと同じ `bundle exec github-pages build` を使います。
  現在のActionsに独立したデータスキーマ・ID整合性検査はありません。
  ビルド成功だけを，業績内容・氏名・日付の正しさの保証にしないでください。
- Previewは `bundle exec jekyll serve`，ループバック限定，Windows用ポーリング監視です。
  出力先は `_site-preview/`。ソースを `python -m http.server` だけで配信しないでください。
- 主要7ページと変更したページをブラウザーで確認します。Publications / Presentationsの
  絞り込み，論文日付，内部リンク，必要に応じてスマートフォンのメニューも確認します。
  `_config.yml` や依存関係の変更後はプレビューを再起動します。
- 完了時に変更ファイル，検証結果，実際に確認したURL，起動方法，残作業を報告します。

## 引き継ぐ編集ルール

- 現行のページ内容・デザインを維持し，依頼範囲外の整理やデータの推測補完をしません。
  共通ナビゲーションは `_includes/navigation.html`，既存CSS・画像・フォントも維持します。
- 業績・人物のIDは固定です。掲載順に合わせて変更せず，廃止IDも再利用しません。
  著者順，原文・取り込み時の値，確認記録を保持し，未確認の氏名を自動統合しません。
- Publicationsは本文と `_data/publications/` の同じIDを更新し，リンクは共通includeを使います。
  採択日順，N/Aの末尾配置，番号，日付表示とCSS/JS/JSONの同一ビルド版指定を維持します。
- Presentationsは `_data/presentations/` から生成し，二重の本文リストを作りません。
  会期終了後，本人の最終承認を得た発表だけを追加します。会期と個別登壇日は区別します。
  国際学会の表示は確認済み英語表記とし，原文を保持します。
- 公開済み情報だけを保存します。予定の発表，主指導関係，学生番号，メール，評価，
  認証情報などを公開リポジトリへ置きません。`public: false` も非公開保管にはなりません。
- OA・リポジトリ公開状態は確認した値だけを使い，PDF本体は置きません。
  指標値や集計ルールは `_data/reporting_policy.yml` と既存ガイドに従います。

## Actionsの役割

- `.github/workflows/validate-achievement-data.yml` は独自の追加検証です。
  checkout → configure-pages → jekyll-build-pages のみで，デプロイは行いません。
  `main` / `data/**` への対象パスのpushで動作し，`codex/**` やPRはトリガー対象外です。
- `pages build and deployment` はGitHub Pages自身の公開処理です。
  ブランチからの公開でもActions基盤を使うため，ローカル検証への移行を理由に無効化しません。
- ローカル検証は公開処理の代わりにはなりません。公開承認後の反映時にはPagesの成功と
  公開ページを確認し，独自検証の役割変更は別途相談します。
- 今回の準備ではリモートのPages設定やActionsを変更していません。

詳細・導入根拠・トラブル対応は `EDITING.md` を参照してください。
