import importlib.util
import math
import re
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

OUT = Path(__file__).resolve().parent

# Load the existing formula implementation so the interactive/static views use exactly the same functions.
spec = importlib.util.spec_from_file_location('logcurves', OUT / 'generate_log_gamma_artifacts.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

camera_names = [n for n, c in mod.curves.items() if c['family'] == 'camera']


def slugify(name):
    s = re.sub(r'[^a-zA-Z0-9]+', '-', name).strip('-').lower()
    return s

# Stable Matplotlib default cycle colours, sampled without manually fixing specific colours.
cycle = plt.rcParams['axes.prop_cycle'].by_key()['color']
curve_colors = {n: cycle[i % len(cycle)] for i, n in enumerate(camera_names)}


def save_svg_with_gids(filename, domain='scene', metric='y'):
    if domain == 'scene':
        x = np.unique(np.r_[np.geomspace(1e-5, 0.02, 320), np.geomspace(0.02, 16.0, 460)])
        xlabel = 'scene-linear r (18% gray = 0.18)'
        xscale = 'log'
        if metric == 'y':
            fun = mod.encode; ylabel = 'encoded output'; title = 'Scene-linear: curve'; yscale = 'linear'
        elif metric == 'd1':
            fun = mod.d1; ylabel = "f'(r)"; title = 'Scene-linear: first derivative'; yscale = 'log'
        else:
            fun = mod.d2; ylabel = "f''(r)"; title = 'Scene-linear: second derivative'; yscale = 'symlog'
    else:
        x = np.linspace(-12.0, 10.0, 640)
        rr = 0.18 * (2.0 ** x)
        xlabel = 'stops from 18% gray'
        xscale = 'linear'
        if metric == 'y':
            fun = lambda n, z: mod.encode(n, rr); ylabel = 'encoded output'; title = 'Stop domain: curve'; yscale = 'linear'
        elif metric == 'd1':
            fun = lambda n, z: mod.g1_stop(n, rr); ylabel = "g'(s) / stop"; title = 'Stop domain: allocation per stop'; yscale = 'linear'
        else:
            fun = lambda n, z: mod.g2_stop(n, rr); ylabel = "g''(s) / stop²"; title = 'Stop domain: second derivative'; yscale = 'linear'

    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    for n in camera_names:
        y = fun(n, x)
        line, = ax.plot(x, y, label=n, color=curve_colors[n], linewidth=1.25)
        line.set_gid('curve-' + slugify(n))
    ax.set_xscale(xscale)
    if yscale == 'log':
        ax.set_yscale('log')
    elif yscale == 'symlog':
        ax.set_yscale('symlog', linthresh=1e-2)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.grid(True, which='both', alpha=0.22)
    # Keep legends out; checkboxes are the legend in the interactive view.
    fig.tight_layout()
    path = OUT / filename
    plt.rcParams['svg.fonttype'] = 'none'
    fig.savefig(path)
    plt.close(fig)
    return path


# Create six interactive SVGs with line group IDs.
interactive_svgs = [
    ('interactive_scene_curve.svg', 'scene', 'y'),
    ('interactive_scene_d1.svg', 'scene', 'd1'),
    ('interactive_scene_d2.svg', 'scene', 'd2'),
    ('interactive_stop_curve.svg', 'stop', 'y'),
    ('interactive_stop_d1.svg', 'stop', 'd1'),
    ('interactive_stop_d2.svg', 'stop', 'd2'),
]
for fn, dom, met in interactive_svgs:
    save_svg_with_gids(fn, dom, met)


def svg_inner(path):
    txt = Path(path).read_text(encoding='utf-8')
    # Strip XML/doctype and keep the complete SVG element.
    m = re.search(r'(<svg[\s\S]*</svg>)', txt)
    return m.group(1) if m else txt


def junction_range(name):
    j = mod.curves[name].get('join', np.nan)
    if not np.isfinite(j):
        return None
    if abs(j) < 1e-12:
        span = 0.035
    elif abs(j) < 0.002:
        span = max(abs(j) * 0.85, 0.0007)
    elif abs(j) < 0.05:
        span = max(abs(j) * 0.7, 0.008)
    else:
        span = abs(j) * 0.55
    lo, hi = j - span, j + span
    # Keep within the safe formula domain where needed; negative values are meaningful for some curves.
    if name.startswith('FUJIFILM') or name in ('ARRI LogC3 EI800', 'Sony S-Log3', 'Panasonic V-Log', 'Nikon N-Log'):
        lo = max(lo, -0.007 if name == 'Nikon N-Log' else -0.001)
    return lo, hi


def make_junction_triptych(name, out_svg=None, out_png=None, compact=False):
    xr = junction_range(name)
    if xr is None:
        return None
    lo, hi = xr
    x = np.linspace(lo, hi, 700)
    j = float(mod.curves[name]['join'])
    figsize = (9.3, 2.8) if compact else (10.5, 3.2)
    fig, axes = plt.subplots(1, 3, figsize=figsize)
    funcs = [mod.encode, mod.d1, mod.d2]
    titles = ['value', 'first derivative', 'second derivative']
    ylabs = ['f(r)', "f'(r)", "f''(r)"]
    for ax, fun, t, yl in zip(axes, funcs, titles, ylabs):
        y = fun(name, x)
        ax.plot(x, y, color=curve_colors[name], linewidth=1.5)
        ax.axvline(j, linestyle='--', linewidth=0.9)
        ax.set_title(t, fontsize=9)
        ax.set_xlabel('r', fontsize=8)
        ax.set_ylabel(yl, fontsize=8)
        ax.tick_params(labelsize=7)
        ax.grid(True, alpha=0.22)
    fig.suptitle(f'{name} — junction at r = {j:.6g}', fontsize=11, y=1.01)
    fig.tight_layout()
    if out_svg:
        fig.savefig(out_svg, bbox_inches='tight')
    if out_png:
        fig.savefig(out_png, dpi=170, bbox_inches='tight')
    plt.close(fig)
    return out_svg or out_png


# Junction zoom assets and HTML cards.
junction_assets = {}
for n in camera_names:
    s = slugify(n)
    svg = OUT / f'junction_{s}.svg'
    png = OUT / f'junction_{s}.png'
    make_junction_triptych(n, svg, png)
    junction_assets[n] = (svg, png)


# Build standalone interactive HTML.
checkboxes = []
for i, n in enumerate(camera_names):
    s = slugify(n)
    checkboxes.append(
        f'<label class="curve-option" data-slug="{s}"><input type="checkbox" value="{s}">'
        f'<span class="swatch" style="background:{curve_colors[n]}"></span>{n}</label>'
    )

plot_blocks = []
for fn, dom, met in interactive_svgs:
    plot_blocks.append(f'<div class="plot-card">{svg_inner(OUT/fn)}</div>')

junction_cards = []
for n in camera_names:
    s = slugify(n)
    j = mod.curves[n].get('join', np.nan)
    jm = mod.join_metrics(n)
    if jm is not None:
        c0, c1 = mod.continuity_label(jm['value_jump_high_minus_low'], jm['slope_jump_high_minus_low'])
        c2 = 'yes' if abs(jm['second_derivative_jump_high_minus_low']) <= 1e-8 else 'no'
    else:
        c0 = c1 = c2 = 'n/a'
    junction_cards.append(
        f'<article class="junction-card" data-slug="{s}" hidden>'
        f'<div class="junction-head"><strong>{n}</strong><span>C0: {c0} / C1: {c1} / C2: {c2}</span></div>'
        f'{svg_inner(junction_assets[n][0])}</article>'
    )

interactive_html = f'''<!doctype html>
<html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Log curve interactive comparison</title>
<style>
:root{{--bg:#fff;--fg:#171717;--muted:#777;--line:#d7d7d7;--panel:#fafafa}}
*{{box-sizing:border-box}} body{{margin:0;font-family:system-ui,-apple-system,"Noto Sans JP",sans-serif;color:var(--fg);background:var(--bg)}}
.wrap{{max-width:1500px;margin:0 auto;padding:18px}} .intro{{font-size:14px;color:#444;margin:0 0 12px}}
.controls{{display:flex;flex-wrap:wrap;gap:7px 14px;border:1px solid #ddd;border-radius:8px;padding:12px;background:#fafafa;position:sticky;top:0;z-index:20}}
.curve-option{{display:flex;align-items:center;gap:5px;font-size:13px;white-space:nowrap;cursor:pointer}} .curve-option input{{margin:0}}
.swatch{{width:12px;height:3px;display:inline-block;border-radius:2px}}
.grid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px;margin-top:14px}}
.plot-card{{border:1px solid #ddd;border-radius:8px;padding:4px;background:#fff;overflow:hidden}} .plot-card svg{{display:block;width:100%;height:auto}}
/* SVG paths are wrapped in groups whose ids start with curve-. */
g[id^="curve-"] path{{transition:opacity .14s,stroke-width .14s,stroke .14s}}
g.curve-muted path{{stroke:#b9b9b9 !important;stroke-width:.65px !important;opacity:.24 !important}}
g.curve-selected path{{stroke-width:2.65px !important;opacity:1 !important}}
.junction-section{{margin-top:24px;border-top:1px solid #ddd;padding-top:16px}}
.junction-note{{font-size:13px;color:#555}} .junction-grid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}}
.junction-card{{border:1px solid #ddd;border-radius:8px;padding:8px;background:#fff}} .junction-card svg{{width:100%;height:auto;display:block}}
.junction-head{{display:flex;justify-content:space-between;gap:12px;align-items:baseline;font-size:12px;margin-bottom:4px}} .junction-head strong{{font-size:14px}}
.empty-note{{padding:18px;border:1px dashed #bbb;border-radius:8px;color:#666;text-align:center}}
@media (max-width:900px){{.grid,.junction-grid{{grid-template-columns:1fr}} .controls{{position:static}}}}
</style></head><body><div class="wrap">
<p class="intro">チェックしたカーブを6枚の図で同時にハイライトします。未選択時は全体図として表示し、選択時は非選択カーブを薄くします。接続点の拡大図も同じチェック状態に連動します。</p>
<div class="controls">{''.join(checkboxes)}</div>
<div class="grid">{''.join(plot_blocks)}</div>
<section class="junction-section"><h2>接続点の拡大</h2><p class="junction-note">比較したいカーブを上でチェックすると、そのカーブの接続点近傍を value / 1階微分 / 2階微分で表示します。</p>
<div id="junction-empty" class="empty-note">上のチェックボックスでカーブを選択してください。</div>
<div class="junction-grid">{''.join(junction_cards)}</div></section>
</div>
<script>
const boxes=[...document.querySelectorAll('.curve-option input')];
function update(){{
  const selected=new Set(boxes.filter(b=>b.checked).map(b=>b.value));
  const active=selected.size>0;
  document.querySelectorAll('g[id^="curve-"]').forEach(g=>{{
    const slug=g.id.replace(/^curve-/, '');
    g.classList.toggle('curve-muted', active && !selected.has(slug));
    g.classList.toggle('curve-selected', active && selected.has(slug));
  }});
  document.querySelectorAll('.junction-card').forEach(card=>{{card.hidden=!selected.has(card.dataset.slug)}});
  document.getElementById('junction-empty').hidden=active;
}}
boxes.forEach(b=>b.addEventListener('change',update)); update();
</script></body></html>'''
(OUT / 'interactive_log_compare.html').write_text(interactive_html, encoding='utf-8')


# Individual contact sheets for the static PDF: full scene-domain triptych + junction triptych.
r_full = np.unique(np.r_[np.geomspace(1e-5, 0.02, 350), np.geomspace(0.02, 16.0, 550)])
# Determine global second-derivative symlog range for consistent cards.
all_d2 = np.concatenate([mod.d2(n, r_full) for n in camera_names])
finite_d2 = all_d2[np.isfinite(all_d2)]
d2_lim = max(np.percentile(np.abs(finite_d2), 99.8), 1.0)


def make_individual_sheet(name):
    j = mod.curves[name].get('join', np.nan)
    fig, axes = plt.subplots(2, 3, figsize=(12.8, 7.2))
    funcs = [mod.encode, mod.d1, mod.d2]
    titles_top = ['curve f(r)', "first derivative f'(r)", "second derivative f''(r)"]
    yscales = ['linear', 'log', 'symlog']
    for ax, fun, title, ys in zip(axes[0], funcs, titles_top, yscales):
        ax.plot(r_full, fun(name, r_full), color=curve_colors[name], linewidth=1.4)
        ax.set_xscale('log')
        if ys == 'log': ax.set_yscale('log')
        if ys == 'symlog':
            ax.set_yscale('symlog', linthresh=1e-2)
            ax.set_ylim(-d2_lim, d2_lim)
        if np.isfinite(j) and j > 0:
            ax.axvline(j, linestyle='--', linewidth=.8)
        ax.set_title(title, fontsize=10); ax.set_xlabel('r', fontsize=8); ax.tick_params(labelsize=7); ax.grid(True, which='both', alpha=.2)
    xr = junction_range(name)
    if xr is not None:
        xj = np.linspace(xr[0], xr[1], 650)
        for ax, fun, title in zip(axes[1], funcs, ['junction: value', 'junction: first derivative', 'junction: second derivative']):
            ax.plot(xj, fun(name, xj), color=curve_colors[name], linewidth=1.4)
            ax.axvline(j, linestyle='--', linewidth=.8)
            ax.set_title(title, fontsize=10); ax.set_xlabel('r', fontsize=8); ax.tick_params(labelsize=7); ax.grid(True, alpha=.2)
    fig.suptitle(name, fontsize=15, y=.985)
    src = mod.curves[name]['source_key']
    fig.text(.5, .012, f'Published-formula implementation; source key: {src}', ha='center', fontsize=8)
    fig.tight_layout(rect=[0, .03, 1, .96])
    s = slugify(name)
    svg = OUT / f'individual_{s}.svg'
    png = OUT / f'individual_{s}.png'
    fig.savefig(svg)
    fig.savefig(png, dpi=150)
    plt.close(fig)
    return svg, png

individual_assets = {n: make_individual_sheet(n) for n in camera_names}


# Build static PDF with ReportLab.
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.colors import HexColor

pdfmetrics.registerFont(UnicodeCIDFont('HeiseiKakuGo-W5'))
FONT = 'HeiseiKakuGo-W5'
PAGE = landscape(A4)
PW, PH = PAGE
pdf_path = OUT / 'log_gamma_derivatives_static_contact_sheet.pdf'
c = canvas.Canvas(str(pdf_path), pagesize=PAGE)


def page_header(title, subtitle=None):
    c.setFont(FONT, 17); c.drawString(28, PH-30, title)
    if subtitle:
        c.setFont(FONT, 8.5); c.setFillColor(HexColor('#555555')); c.drawString(28, PH-44, subtitle); c.setFillColor(HexColor('#000000'))


def page_no(n):
    c.setFont(FONT, 7.5); c.setFillColor(HexColor('#777777')); c.drawRightString(PW-24, 15, str(n)); c.setFillColor(HexColor('#000000'))

page = 1
page_header('公開仕様から見るLogカーブ - 静的図版', '微分・2階微分・接続条件 / メーカー公開文書の式を再実装した比較')
c.setFont(FONT, 10.5)
text = c.beginText(34, PH-78); text.setLeading(16)
lines = [
    'このPDFは、インタラクティブHTMLとは別系統の静的図版です。',
    '全体図は現在の比較図をそのまま残し、その後に各カーブの個別コンタクトシートを収録しています。',
    '',
    '留保：ここで扱う各社Logは、仕様書・データシート・ホワイトペーパーに記載された公開数式の再実装です。',
    '実機測定によるOETF推定ではなく、内部画像処理、センサー固有処理、EI依存処理、量子化、クリップ等を',
    '再現するものではありません。公表係数の丸めにより、接続点の微小な差が設計上の不連続か丸め誤差か',
    '区別できない場合があります。',
    '',
    '個別シート：上段 = scene-linear全域の f, f\', f\'\'。下段 = 接続点近傍の拡大。破線は公開式の接続点です。'
]
for line in lines: text.textLine(line)
c.drawText(text)
page_no(page); c.showPage(); page += 1

# Overview contact sheet page: six existing figures, 2x3.
page_header('Overview - 全カーブ比較')
overview = [
    ('camera_log_curves_scene_linear.png','scene-linear: curve'),
    ('camera_log_first_derivative_scene_linear.png','scene-linear: first derivative'),
    ('camera_log_second_derivative_scene_linear.png','scene-linear: second derivative'),
    ('camera_log_curves_stops.png','stop domain: curve'),
    ('camera_log_first_derivative_stops.png','stop domain: first derivative'),
    ('camera_log_second_derivative_stops.png','stop domain: second derivative'),
]
margin_x, top_y = 24, PH-50
cols, rows = 2, 3
gap_x, gap_y = 10, 8
cell_w = (PW-2*margin_x-gap_x)/cols
cell_h = (PH-70-gap_y*(rows-1))/rows
for idx,(fn,cap) in enumerate(overview):
    r, col = divmod(idx, cols)
    x0 = margin_x + col*(cell_w+gap_x)
    y0 = top_y - (r+1)*cell_h - r*gap_y
    img = ImageReader(str(OUT/fn)); iw, ih = img.getSize(); scale=min(cell_w/iw,(cell_h-12)/ih)
    dw, dh=iw*scale, ih*scale
    c.drawImage(img, x0+(cell_w-dw)/2, y0+12+(cell_h-12-dh)/2, dw, dh, preserveAspectRatio=True, mask='auto')
    c.setFont(FONT, 7.3); c.drawCentredString(x0+cell_w/2, y0+2, cap)
page_no(page); c.showPage(); page += 1

# Two individual sheets per page.
for i in range(0, len(camera_names), 2):
    names = camera_names[i:i+2]
    page_header('Individual curve contact sheets')
    available_h = PH-64
    card_h = (available_h-10)/2
    for k,n in enumerate(names):
        img = ImageReader(str(individual_assets[n][1])); iw,ih=img.getSize()
        x0=28; y0=PH-55-(k+1)*card_h-k*10
        maxw=PW-56; maxh=card_h-4
        scale=min(maxw/iw,maxh/ih); dw,dh=iw*scale,ih*scale
        c.drawImage(img,x0+(maxw-dw)/2,y0+(maxh-dh)/2,dw,dh,preserveAspectRatio=True,mask='auto')
    page_no(page); c.showPage(); page += 1

# References page.
page_header('参考文献 / implementation sources', '各カーブの数式を拾った公開文書。CIE L*とCineonは比較参照。')
refs = [
    ('ARRI LogC3','ARRI, ALEXA Log C Curve: Usage in VFX, 2017.'),
    ('ARRI LogC4','ARRI, ARRI LogC4 Logarithmic Color Space Specification, 2025.'),
    ('Sony S-Log3','Sony Corporation, Technical Summary for S-Gamut3.Cine/S-Log3 and S-Gamut3/S-Log3.'),
    ('Panasonic V-Log','Panasonic Corporation, V-Log/V-Gamut Reference Manual Rev.1.0, 2014.'),
    ('FUJIFILM F-Log','FUJIFILM Corporation, F-Log Data Sheet Ver.1.2, 2024.'),
    ('FUJIFILM F-Log2','FUJIFILM Corporation, F-Log2 Data Sheet Ver.1.1, 2024.'),
    ('Nikon N-Log','Nikon Corporation, N-Log Specification Document Ver.1.0.0, 2018.'),
    ('Canon Log family','Canon USA, Canon Log Gamma Curves white paper, 2018.'),
    ('RED Log3G10','RED Digital Cinema, White Paper on REDWideGamutRGB and Log3G10, Rev C.'),
    ('CIE L*','CIE, CIE 1976 L*a*b* colour space; see also ISO/CIE 11664-4.'),
    ('Cineon','Eastman Kodak, Cineon Digital Film System technical documentation; reference implementation cross-checked with FilmLight technical note.'),
]
y=PH-72
for key,desc in refs:
    c.setFont(FONT,9.5); c.drawString(34,y,key)
    c.setFont(FONT,8.2); c.setFillColor(HexColor('#444444')); c.drawString(150,y,desc); c.setFillColor(HexColor('#000000'))
    y-=22
c.setFont(FONT,8.3); c.setFillColor(HexColor('#555555'))
c.drawString(34, y-8, 'URLと完全な書誌情報は companion QMD / references.bib に収録しています。')
page_no(page); c.save()


# Patch QMD: insert interactive section if not already present.
qmd_path = OUT / 'log_gamma_derivatives_extended.qmd'
qmd = qmd_path.read_text(encoding='utf-8')
marker = '# 18%グレーでの比較'
section = '''# インタラクティブ比較と接続点拡大\n\n静的な全体図は俯瞰用として残し、下の比較ウィンドウではチェックボックスで任意のカーブをハイライトできます。選択は scene-linear / stop 軸の6図に同時反映され、同じ選択に応じて接続点近傍の value・1階微分・2階微分も表示されます。\n\n<div class="quarto-figure quarto-figure-center">\n<iframe src="interactive_log_compare.html" style="width:100%;height:1850px;border:1px solid #ddd;border-radius:8px;" loading="lazy"></iframe>\n</div>\n\n静的PDFではインタラクティブ要素を分岐し、全体図に加えて各カーブの個別コンタクトシートを収録しています。\n\n'''
if '# インタラクティブ比較と接続点拡大' not in qmd:
    qmd = qmd.replace(marker, section + marker)
qmd_path.write_text(qmd, encoding='utf-8')

print('Created:')
for p in [OUT/'interactive_log_compare.html', pdf_path, qmd_path]:
    print(p)
