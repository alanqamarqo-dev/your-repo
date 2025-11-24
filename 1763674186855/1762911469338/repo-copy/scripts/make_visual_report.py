#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import annotations
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import os, json, argparse, datetime, math
from string import Template
from Learning_System.visualizer import render_model_png

TEMPLATE = Template("""<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>AGL Visual Models Report</title>
<style>
body{font-family:system-ui,-apple-system,Segoe UI,Roboto; margin:24px; background:#0b0e11; color:#e8eef5;}
h1{margin:0 0 16px 0}
.card{background:#121820; border:1px solid #1d2633; border-radius:12px; padding:16px; margin-bottom:16px;}
.meta{font-size:13px; opacity:.9; margin:6px 0 12px}
img{max-width:100%; height:auto; border-radius:8px; border:1px solid #1d2633; background:#0b0e11}
kbd{background:#1a2230; padding:2px 6px; border-radius:6px; border:1px solid #283347}
small{opacity:.85}
footer{margin-top:28px; font-size:12px; opacity:.75}
</style>
</head>
<body>
<h1>📊 تقرير النماذج البصرية (AGL)</h1>
<div class="meta">
تم الإنشاء: <b>$date</b> · عدد النماذج: <b>$count</b>
</div>

$cards

<footer>
تم الإنشاء آليًا بواسطة AGL · ملف التقرير: <kbd>$out_html</kbd>
</footer>
</body>
</html>
""")

CARD = """<div class="card">
  <h3>{base} → <small>{winner}</small></h3>
  <div class="meta">
    rmse = <b>{rmse:.6g}</b> · n = <b>{n}</b> · y={yname}, x={xname}<br/>
    a = <b>{a:.6g}</b> · b = <b>{b:.6g}</b>
  </div>
  <img src="{rel_png}" alt="{base} plot"/>
</div>
"""


def main():
    ap = argparse.ArgumentParser(description="Make visual HTML report for AGL models")
    ap.add_argument("--glob-dir", dest="glob_dir", default="artifacts/models", help="root dir containing results.json files")
    ap.add_argument("--out", default="reports/models_visual.html", help="output HTML path")
    ap.add_argument("--figdir", dest="figdir", default="reports/figs", help="directory to write PNGs")
    args = ap.parse_args()

    # جمع كل results.json
    result_files = []
    for root, _, files in os.walk(args.glob_dir):
        for f in files:
            if f.lower() == "results.json":
                result_files.append(os.path.join(root, f))
    result_files.sort()

    os.makedirs(args.figdir, exist_ok=True)

    # load KB statuses (Learned_Patterns.json) if available
    kb_map = {}
    kb_path = os.path.join('Knowledge_Base', 'Learned_Patterns.json')
    try:
        if os.path.exists(kb_path):
            with open(kb_path, 'r', encoding='utf-8-sig') as fh:
                kb = json.load(fh)
                for item in kb.get('patterns', kb if isinstance(kb, list) else []):
                    base = item.get('base') or item.get('law') or item.get('name')
                    if base:
                        kb_map[base] = item
    except Exception:
        kb_map = {}

    metas = []
    for rp in result_files:
        base_name = os.path.basename(os.path.dirname(rp))
        png_path = os.path.join(args.figdir, f"{base_name}.png")
        try:
            meta = render_model_png(rp, png_path, title=base_name)
            # include pdf and plotted points
            meta['result_path'] = rp
            meta['png_path'] = png_path
            meta['pdf_path'] = os.path.splitext(png_path)[0] + '.pdf'
            meta['base_name'] = base_name
            metas.append(meta)
        except Exception as e:
            print(f"skipping {rp}: {e}")
            continue

    # compute RMSE quantiles for coloring
    rmses = [m.get('rmse', float('nan')) for m in metas if isinstance(m.get('rmse'), (int, float)) and not math.isnan(m.get('rmse'))]
    rmses_sorted = sorted(rmses)
    def quantile(arr, q):
        if not arr:
            return None
        idx = int(len(arr) * q)
        idx = max(0, min(len(arr)-1, idx))
        return arr[idx]

    q1 = quantile(rmses_sorted, 0.33) or 0.0
    q2 = quantile(rmses_sorted, 0.66) or 0.0

    cards = []
    for meta in metas:
        base = meta.get('base_name')
        rmse = meta.get('rmse') or 0.0
        # color by rmse (green->low, yellow->mid, red->high)
        if q1 is None or q2 is None:
            color = '#2ecc71'
        else:
            try:
                if rmse <= q1:
                    color = '#2ecc71'
                elif rmse <= q2:
                    color = '#f1c40f'
                else:
                    color = '#e74c3c'
            except Exception:
                color = '#95a5a6'

        # KB badge
        kb_item = kb_map.get(base, {})
        status = kb_item.get('status') or kb_item.get('state') or kb_item.get('phase') or 'unknown'
        badge = f"<span style='background:#111;padding:4px 8px;border-radius:8px;border:1px solid #333;color:{color};font-weight:600'>{status}</span>"

        rel_png = os.path.relpath(meta['png_path'], start=os.path.dirname(args.out)).replace("\\","/")
        rel_pdf = os.path.relpath(meta['pdf_path'], start=os.path.dirname(args.out)).replace("\\","/")

        cards.append(CARD.format(
            base=meta.get('base'), winner=meta.get('winner'),
            rmse=meta.get('rmse'), n=meta.get('n'), a=meta.get('a'), b=meta.get('b'),
            xname=meta.get('xname'), yname=meta.get('yname'), rel_png=rel_png
        ) + f"\n<div style='margin-top:8px'>Status: {badge} &nbsp; <a href=\"{rel_png}\">PNG</a> · <a href=\"{rel_pdf}\">PDF</a> · points={meta.get('plotted_points',0)}</div>")

    html = TEMPLATE.substitute(
        date=datetime.datetime.now().isoformat(),
        count=len(cards),
        cards="\n".join(cards),
        out_html=args.out
    )

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
