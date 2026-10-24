# Roboto for the Asano-style preview

このプレビューは，Roboto の normal 300・400・500・700 をオフラインで描画するため，Google Fonts の公式ソースから作成した Latin / Latin-ext の WOFF2 を使用します。日本語は既存のシステムフォントへフォールバックします。

## Runtime files

- `../../font-faces.css` が，2 個の WOFF2 を data URI として含む自己完結した実行用 CSS です。ビルドではこの CSS を先頭へ結合してください。外部フォントサービスへのアクセスは不要です。
- `OFL.txt` は Google Fonts から取得した SIL Open Font License 1.1 の全文です。CSS とともにこのライセンスを保持してください。
- このディレクトリの `.woff2` は確認用の個別ファイルです。実行時の CSS はこれらの相対パスを参照しません。`font-faces.css` と `OFL.txt` と本 README があれば，個別のバイナリを Git に含めずに同じ表示を再現できます。
- `build-metadata.json` には，ハッシュ・軸・サブセット範囲・検証結果を記録しています。

## Official sources and provenance

- 参照サイトのフォント指定: https://github.com/yukimasano/yukimasano.github.io/blob/master/_includes/head.html
- 参照サイトの Google Fonts CSS URL: https://fonts.googleapis.com/css?family=Roboto:300,400,500,700%7CRoboto+Slab:100,300,400,500,700%7CMaterial+Icons
- 取得元の公式 Roboto ソース: https://github.com/google/fonts/blob/main/ofl/roboto/Roboto%5Bwdth,wght%5D.ttf
- 公式メタデータ: https://github.com/google/fonts/blob/main/ofl/roboto/METADATA.pb
- 公式ライセンス: https://github.com/google/fonts/blob/main/ofl/roboto/OFL.txt
- フォント名・バージョン: `Roboto` / `Version 3.015; 2026`。
- Copyright: `Copyright 2011 The Roboto Project Authors (https://github.com/googlefonts/roboto-classic)`。
- License: **SIL Open Font License, Version 1.1**。元のフォント内の著作権・ライセンス情報も保持しています。
- 元 TTF の Git blob SHA-1: `5522a368d9072fd88c299916e61fcff369949061`。ダウンロードしたバイト列に Git blob ヘッダーを加えて照合済みです。
- 元 TTF の SHA-256: `d7598e12c5dbef095ff8272cfc55da0250bd07fbdecbac8a530b9b277872a134`。

取得は GitHub connector を通じて公式 `google/fonts` リポジトリから行いました。ここで配布する WOFF2 は，その公式 TTF をローカルで変換したものです。Google Fonts CDN の WOFF2 をそのまま保存したものではなく，CDN のサブセットと同一のバイト列・区切りであるとは主張しません。

## Conversion and CSS configuration

- Source axes: `wght 100–900`，`wdth 75–100`。
- `wdth` は `100`（通常幅）に固定しました。`wght 100–900` の可変軸は保持し，CSS の公開範囲を `font-weight: 300 700` としています。
- CSS は両サブセットとも `font-family: Roboto`，`font-style: normal`，`font-display: swap` です。
- Latin-ext は Latin と重なるコードポイントを除いてからサブセット化しました。2 つの `unicode-range` は非重複です。
- OpenType layout features と名前テーブルの著作権・ライセンス等を保持しました。サブセット化後に幅軸を固定しています。
- 変換には FontTools 4.61.1 と，ローカル Node.js の Brotli エンコーダーを使用しました。追加パッケージのネットワーク取得は行っていません。

## Subsets

### roboto-latin-variable.woff2

- Size: 53,596 bytes。
- SHA-256: `91aecb7059abe9df178cdbc4240429675b349098cd02abdabf370fb5dc5fdc3e`。
- Unicode cmap entries: 272。
- CSS `unicode-range`:

```css
U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-209F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD
```

### roboto-latin-ext-variable.woff2

- Size: 39,928 bytes。
- SHA-256: `07da7f399fef050af44d6f9f0d48ee97d5f75053a8e079fa900910c62995b7ae`。
- Unicode cmap entries: 272。
- CSS `unicode-range`:

```css
U+0100-0130,U+0132-0151,U+0154-02BA,U+02BD-02C5,U+02C7-02D9,U+02DB,U+02DD-0303,U+0305-0307,U+0309-0328,U+032A-036F,U+1D00-1DBF,U+1E00-1EFF,U+20A0-20AB,U+20AD-20C0,U+2113,U+2C60-2C7F,U+A720-A7FF,U+AB30-AB6F
```

## Validation

WOFF2 を再読み込みし，normal の 300・400・500・700 の各ウェイトで，含まれるすべての Unicode グリフの分解済みアウトラインと水平メトリクスが，公式 TTF の通常幅インスタンスと一致することを確認しました。各ウェイトの ascender・descender・line gap も一致しています。Latin の ASCII 印字文字 U+0020–U+007E の網羅，両サブセットのコードポイント範囲の非重複，および日本語/CJK コードポイントを含まないことを確認しました。

この検証は，取得した公式 TTF と生成した WOFF2 の同一性を確認するものです。参照サイトが将来配信するフォントの版や，OS ごとのラスタライズ・日本語フォールバックまで固定するものではありません。
