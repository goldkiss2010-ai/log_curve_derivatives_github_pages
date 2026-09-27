# Public Log Curve Derivatives

メーカー公開の仕様書・データシート・ホワイトペーパーに記載された前向き符号化関数を再実装し、カーブ本体、1階微分、2階微分、stop軸での符号配分、piecewise接続条件を比較する静的サイトです。

> **Scope / disclaimer**  
> これは実機測定によるOETF推定ではありません。各メーカーが公開した数式を、その公表係数の精度で再実装した比較です。内部画像処理、センサー固有処理、EI依存処理、量子化、クリップ、メタデータ処理などを再現するものではありません。公開係数の丸めに由来する可能性がある微小な接続差は、設計意図とは区別して `as printed` として扱います。


## Repository / Pages

- Repository: https://github.com/goldkiss2010-ai/log_curve_derivatives_github_pages
- GitHub Pages: https://goldkiss2010-ai.github.io/log_curve_derivatives_github_pages/
- Quarto source: https://github.com/goldkiss2010-ai/log_curve_derivatives_github_pages/blob/main/article.qmd
- Scripts: https://github.com/goldkiss2010-ai/log_curve_derivatives_github_pages/tree/main/scripts
- Data: https://github.com/goldkiss2010-ai/log_curve_derivatives_github_pages/tree/main/data
- References: https://github.com/goldkiss2010-ai/log_curve_derivatives_github_pages/blob/main/references.bib

## Repository layout

- `index.html` — GitHub Pages のメインページ
- `compare.html` — チェックボックス式のインタラクティブ比較。デスクトップでは6図を3列×2行で表示
- `article.qmd` — 編集用Quartoソース
- `references.bib` — 公式仕様書・ホワイトペーパー等の参考文献
- `assets/figures/overview/` — 本文で使うSVG
- `assets/figures/individual/` — 各カーブ個別SVG
- `assets/figures/junction/` — 接続点拡大SVG
- `data/` — 比較表・サンプル値CSV
- `scripts/` — 図・比較ページ・PDFの再生成用Python
- `downloads/log-gamma-derivatives-contact-sheet.pdf` — 静的PDF版
- `.nojekyll` — GitHub Pagesでそのまま静的配信するための設定

## GitHub Pagesで公開する

1. このフォルダの**中身**をGitHubリポジトリのルートへ置きます。
2. GitHubで `Settings` → `Pages` を開きます。
3. `Build and deployment` を `Deploy from a branch` にします。
4. Branchを `main`、Folderを `/(root)` にして保存します。
5. 数分後、PagesのURLで `index.html` が公開されます。

ビルド工程は不要です。公開済みHTMLとSVGをそのまま配信します。

## Local preview

相対パスとiframeの確認には、リポジトリのルートで簡易HTTPサーバーを起動するのが確実です。

```bash
python -m http.server 8000
```

その後 `http://localhost:8000/` をブラウザで開きます。

## Sources

数式の出典は `references.bib` と本文末尾の参考文献にまとめています。メーカーPDFそのものはこのリポジトリに再配布していません。

## 図幅と再レンダリング

本文の静的図は約760 px（比較ウィンドウの約半分）に設定しています。比較ウィンドウだけは最大1500 pxを使います。
この設定は `styles.css` にまとめてあります。`article.qmd` をQuartoで再レンダリングしても維持されます。

```bash
quarto render article.qmd
```

`article.qmd` は `index.html` を出力する設定です。
