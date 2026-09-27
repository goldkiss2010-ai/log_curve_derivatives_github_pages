# Public Log Curve Derivatives

メーカー公開の仕様書・データシート・ホワイトペーパーに記載された前向き符号化関数を再実装し、カーブ本体、1階微分、2階微分、stop軸での符号配分、piecewise接続条件を比較する静的サイトです。

> **Scope / disclaimer**  
> 本資料では、各社が公開している仕様書・データシート・ホワイトペーパーの数式を再実装しています。実機の内部処理を直接検証したものではありません。センサー固有処理、EI依存処理、量子化、クリップ、メタデータ処理などは、公開式と異なる可能性があります。公開係数の丸めに由来する可能性がある微小な接続差は、設計意図とは区別して `as printed` として扱います。

現在は ARRI / Sony / Panasonic / FUJIFILM / Nikon / Canon / RED / Apple / DJI の公開式を同じ解析系に置き、CIE L* と Cineon を比較参照として収録しています。

## Repository / Pages

- Repository: https://github.com/goldkiss2010-ai/log_curve_derivatives_github_pages
- GitHub Pages: https://goldkiss2010-ai.github.io/log_curve_derivatives_github_pages/
- Quarto source: `article.qmd`
- Curve registry: `curve_specs/curves.yaml`
- Source registry: `curve_specs/sources.yaml`
- Build entry point: `scripts/build_all.py`
- Adding a curve: `ADDING_A_CURVE.md`

## Single-source build

曲線名、式の種類、係数、接続点、出典は `curve_specs/` を基準にします。既存の数式モデルで表せるLogなら、原則として `curves.yaml` に1項目追加するだけです。

```bash
python scripts/build_all.py
```

これで次をまとめて再生成します。

- `data/*.csv`
- 本文用 overview SVG/PNG
- 接続点SVG
- インタラクティブ `compare.html`
- 個別カーブのコンタクトシートPNG
- `references.bib`
- QMDから読み込む `generated/*.qmd`
- 静的PDF
- GitHub Pages用 `index.html`

新しい数学的な形の関数だけは `scripts/curve_models.py` に `encode / d1 / d2` を追加します。詳しくは [ADDING_A_CURVE.md](ADDING_A_CURVE.md) を参照してください。

## Repository layout

```text
.
├─ index.html                    # GitHub Pagesの公開ページ
├─ compare.html                  # 3列×2行のインタラクティブ比較
├─ article.qmd                   # 人が編集する本文
├─ styles.css
├─ references.bib                # sources.yaml から自動生成
├─ ADDING_A_CURVE.md
├─ requirements.txt
│
├─ curve_specs/
│  ├─ curves.yaml                # 曲線の単一レジストリ
│  └─ sources.yaml               # 出典の単一レジストリ
│
├─ generated/                    # article.qmd がincludeする自動生成断片
│  ├─ camera_curves.qmd
│  ├─ summary_table.qmd
│  ├─ junction_table.qmd
│  └─ primary_sources.qmd
│
├─ scripts/
│  ├─ build_all.py               # 一括生成
│  └─ curve_models.py            # 数式モデルと解析微分
│
├─ assets/figures/
│  ├─ overview/                  # 本文用SVG/PNG
│  ├─ junction/                  # 接続点拡大SVG
│  └─ individual/                # 静的PDF用の個別PNG
│
├─ data/                         # 数値CSV + build manifest
└─ downloads/
   └─ log-gamma-derivatives-contact-sheet.pdf
```

## GitHub Pagesで公開する

このフォルダの**中身**をリポジトリのルートへpushし、GitHubの `Settings → Pages` で `Deploy from a branch / master / (root)` を選択します。公開済みの `index.html` をそのまま配信するため、Pages側でビルドする必要はありません。

## Local preview

相対パスとiframeを含むので、ローカルでは簡易HTTPサーバー経由の確認が確実です。

```bash
python -m http.server 8000
```

その後 `http://localhost:8000/` を開きます。

## Dependencies

Python側は `requirements.txt` を使えます。

```bash
pip install -r requirements.txt
```

`build_all.py` は公開HTML生成に Pandoc を使います。Pandocがない場合は Quarto があれば `quarto render article.qmd` で本文をレンダリングできます。QMDの表や一覧は `generated/` に既に生成されるため、Quartoからも同じレジストリを参照します。

## Sources

一次資料へのリンクは公開ページ本文にも自動生成されます。メーカーPDFそのものはこのリポジトリに再配布しません。
