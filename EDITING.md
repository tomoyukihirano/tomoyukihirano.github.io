# ホームページの更新方法

このサイトはGitHub Pages + Jekyllで公開しています。

- 論文: `_data/publications/YYYY.yml`
- 発表: `_data/presentations/YYYY.yml`
- 研究費: `_data/grants.yml`
- 共通メニュー: `_includes/navigation.html`

`publications.md`，`presentations.md`，`supports-grants.md`は表示テンプレートです。通常の追加はYAMLを編集します。発表では`scope`を`domestic`または`international`，招待講演は`invited: true`，受賞講演は`award_lecture: true`とします。期間・金額が未確認の採択案件は`publish: false`で保持します。
