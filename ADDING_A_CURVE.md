# Adding a Log Curve

このリポジトリは、曲線を後から追加しても図・表・HTML・CSV・PDFを個別に書き換えなくてよい構造にしています。

## 1. まず `curve_specs/curves.yaml` に追加する

既存モデルに当てはまる場合は、新しいエントリを1件追加します。たとえば線形枝からLog枝へ接続するタイプなら、必要な係数、接続点、出典キーを記述します。

```yaml
- id: example-log
  name: Example Log
  family: camera
  model: commonlog
  params:
    cut: 0.01
    a: 1.0
    b: 0.01
    c: 0.25
    d: 0.6
    e: 5.0
    f: 0.1
  branches:
    low: linear
    high: log10
  junctions:
    - id: toe
      value: 0.01
      domain: r
      label: linear / log10
      primary: true
  sources: [example-source]
```

`id` はファイル名・HTML要素IDにも使うため、英小文字・数字・ハイフンを推奨します。

## 2. `curve_specs/sources.yaml` に一次資料を追加する

```yaml
example-source:
  type: techreport
  author: Example Corporation
  organization: Example Corporation
  title: Example Log White Paper
  year: 2026
  url: https://example.com/example-log.pdf
  note: Forward encoding formula.
```

この情報から `references.bib` と本文の一次資料リンク表が生成されます。

## 3. 新しい数式型だけ `scripts/curve_models.py` を編集する

既存の `model:` で表せない場合だけ、同じモデル名について次の3関数へ式を追加します。

- `encode(c, r)` — 前向き符号化 `f(r)`
- `d1(c, r)` — 解析的な1階微分 `f'(r)`
- `d2(c, r)` — 解析的な2階微分 `f''(r)`

stop軸の微分は共通式

```text
g'(s)  = ln(2) r f'(r)
g''(s) = ln(2)^2 [r f'(r) + r^2 f''(r)]
```

から自動生成されます。

## 4. 複数の接続点も列挙できる

`junctions:` は配列です。Apple Logのように複数のpiecewise接続がある場合は、すべて記述できます。インタラクティブ画面では、そのカーブをチェックすると各接続点の拡大図が表示されます。

`primary: true` を付けた接続点は、静的PDFの個別コンタクトシートで代表接続点として使われます。

## 5. 一括再生成する

```bash
python scripts/build_all.py
```

追加した曲線は自動的に、overview 6図、チェックボックス、接続点拡大、18%グレー表、連続性表、CSV、個別図、PDF、一次資料リンク、参考文献へ反映されます。

## 6. 確認する

```bash
python -m http.server 8000
```

`http://localhost:8000/` で `index.html` と `compare.html` を確認します。特に新しい曲線では、18%グレー値と接続点の `C0 / C1 / C2` が原資料の記述や既知のコード値と整合するかを確認してください。

## 実装上の原則

このプロジェクトは実機の挙動を推定するのではなく、公開文書に記載された式を比較するものです。メーカーごとのEI処理、クリッピング、量子化、内部ISP処理などを別途推定して曲線へ混ぜないでください。公開係数の丸めによる微小差は `as printed` として保持します。

### 複数の接続点

`junctions:` に複数の接続点を登録すると、インタラクティブ版だけでなく静的コンタクトシートにも全接続点が自動的に出力されます。`primary: true` は代表点を必要とする処理のために残せますが、静的図から他の接続点を省略する意味には使いません。
