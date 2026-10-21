# 平野 知之 / Tomoyuki Hirano

個人ホームページの静的HTML一式です。

## 公開設定

GitHub Pagesの個人サイトとして，実際のGitHubユーザー名に対応する
`<username>.github.io` リポジトリへこの一式を配置します。
公開元は `main` ブランチの `/(root)` を使用します。
`index.html` と空の `.nojekyll` はリポジトリ直下に置きます。
HTMLの生成や更新のためにWordPress本体を実行する必要はありません。

## 編集

- 文章は各ページの `index.html` を編集します。
- 共通の表示調整は `assets/site.css` にあります。
- 共通メニューの動作は `assets/site.js` にあります。
- `assets/css/exported/` は元のページから抽出したスタイルです。
- 画像の既存パスを保持しています。

ローカルで確認する場合は，このディレクトリーで次を実行します。

```sh
python3 -m http.server 8000
```

ブラウザーで `http://localhost:8000/` を開きます。

## 検索エンジン向け設定

主な公開先は https://tomoyukihirano.github.io/ です。
各HTMLのcanonicalは，この公開先にある対応ページの絶対URLを指定しています。
公開先を変更するときはcanonicalとサイトマップのURLも更新してください。

- sitemap.xml は内容ページとブログ一覧を掲載します。著者別・カテゴリー別の一覧は省いていますが，クロールを禁止しているわけではありません。
- ページを追加・移動・削除したときはsitemap.xmlも更新してください。
- robots.txt はクロールを許可し，サイトマップの場所を案内します。
- トップとAboutのdescriptionには，既存本文の紹介文をそのまま使用しています。
- Search Consoleへ登録するプロパティは https://tomoyukihirano.github.io/ （URLプレフィックス）です。所有権確認用のタグやファイルを追加した場合は，確認後も保持してください。

## 保存について

この一式には公開ページの表示に必要なローカルファイルを含めています。
HTMLをそのまま配信できる別のWebサーバーへも移せるように，相対パスを使用しています。
数式記事のMathJax，アクセス解析，外部サイトへのリンクは元の設定を保持しています。

`SHA256SUMS.txt` は2026年10月21日時点の公開用スナップショットの照合用です。
ファイルを編集した後は必要に応じて照合値を更新してください。

## 著作権・第三者コンポーネント

本文・写真・資料の著作権を放棄したり，新しい利用許諾を付与したりするものではありません。
BusinessPress，Font Awesome，normalize.cssの既存の著作権・ライセンス表記は，
対応するCSSファイルの中に保持しています。

## GitHub公式資料

- [Creating a GitHub Pages site](https://docs.github.com/en/pages/getting-started-with-github-pages/creating-a-github-pages-site)
- [Configuring a publishing source](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site)
