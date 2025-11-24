# -*- coding: utf-8 -*-
"""
يصنع تقرير HTML يلخّص أفضل النماذج وملاحظات مشتقة
Usage:
  python -m scripts.make_models_report --patterns Knowledge_Base/Learned_Patterns.json --out reports/models_report.html [--ascii]
"""
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import json, os, argparse
from datetime import datetime

def html_escape(s):
    return (str(s)
            .replace("&","&amp;")
            .replace("<","&lt;")
            .replace(">","&gt;")
            .replace('"','&quot;')
            .replace("'","&#39;"))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--patterns", default="Knowledge_Base/Learned_Patterns.json")
    ap.add_argument("--out", default="reports/models_report.html")
    ap.add_argument("--ascii", action="store_true")
    args = ap.parse_args()

    with open(args.patterns, "r", encoding="utf-8-sig") as f:
        J = json.load(f)

    # Build a mapping to dedupe by (base, winner) keeping best (lowest) RMSE
    dedupe = {}
    total_patterns = 0
    improved_today = 0
    for p in J.get("patterns", []):
        total_patterns += 1
        # Skip incomplete records
        if not p.get('base') or not p.get('winner') or not p.get('fit'):
            continue
        # Accept missing status as accepted; also accept 'validated'
        if p.get("status") not in (None, "accepted", "validated"):
            continue
        base = p.get('base')
        winner = p.get('winner')
        fit = p.get('fit', {})
        rmse = fit.get('rmse')
        key = (base, winner)
        # choose entry with lowest RMSE
        if key not in dedupe or (rmse is not None and (dedupe[key].get('fit',{}).get('rmse') is None or rmse < dedupe[key]['fit'].get('rmse'))):
            dedupe[key] = p
        # count 'improved' marker if present
        if p.get('tags') and 'improved' in p.get('tags'):
            improved_today += 1

    # Prepare sorted rows: sort by base then ascending RMSE
    rows = []
    for (base, winner), p in sorted(dedupe.items(), key=lambda it: (it[0][0] or '', (it[1].get('fit',{}).get('rmse') or float('inf')))):
        fit = p.get('fit', {})
        a = fit.get('a'); b = fit.get('b')
        rmse = fit.get('rmse'); conf = fit.get('confidence')
        schema = p.get('schema', '')
        derived = p.get('derived', {})
        d_kv = ", ".join([f"{k}={v:.6g}" if isinstance(v,(int,float)) else f"{k}={v}" for k, v in derived.items()])
        # status badge
        status = p.get('status') or 'accepted'
        rows.append({
            'base': base,
            'winner': winner,
            'a': a,
            'b': b,
            'rmse': rmse,
            'conf': conf,
            'schema': schema,
            'derived': d_kv,
            'status': status,
            'units': p.get('units', {}),
            'notes': p.get('notes', '')
        })

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    sym_approx = "~" if args.ascii else "≈"
    html = []
    html.append("<!DOCTYPE html><meta charset='utf-8'>")
    html.append(f"<title>AGL Models Report</title>")
    # No-wrap table cells, KPI cards, badges and RTL for Arabic title area
    html.append("<style>body{font-family:system-ui,Segoe UI,Arial;margin:24px} .kpi{display:inline-block;padding:12px 16px;border-radius:8px;background:#f5f5f5;margin-right:12px} .badge{display:inline-block;padding:2px 8px;border-radius:8px;color:#fff;font-size:12px} .badge-new{background:#2e7d32}.badge-default{background:#1976d2} table{border-collapse:collapse;width:100%} th,td{border:1px solid #ddd;padding:8px;white-space:nowrap} th{background:#f5f5f5;text-align:left} .small{font-size:0.9em;color:#666}</style>")
    # Arabic title with small KPI cards
    html.append(f"<h1>تقرير النماذج AGL <span class='small' style='margin-left:8px'>updated {html_escape(datetime.now().isoformat(timespec='seconds'))}</span></h1>")
    # KPI cards
    total_rules = len(rows)
    rmse_values = [r['rmse'] for r in rows if r.get('rmse') is not None]
    best_rmse = min(rmse_values) if rmse_values else None
    best_name = next((r['base'] for r in rows if r.get('rmse') == best_rmse), '')
    html.append(f"<div style='margin-bottom:12px'><span class='kpi'>عدد القواعد: <strong>{total_rules}</strong></span><span class='kpi'>أفضل RMSE: <strong>{'' if best_rmse is None else f'{best_rmse:.6g}'}</strong> <small>({html_escape(best_name)})</small></span><span class='kpi'>نماذج محسّنة اليوم: <strong>{improved_today}</strong></span></div>")
    # Download button (keeps prior behavior)
    html.append("<div style='margin:12px 0;'><a id='download-pdf' href='AGL_report.pdf' download='AGL_report.pdf' style='display:inline-block;padding:8px 12px;background:#1976d2;color:#fff;border-radius:6px;text-decoration:none'>Download PDF</a> <span id='pdf-note' style='margin-left:8px;color:#666;font-size:0.9em'></span></div>")
    html.append("<table>")
    html.append("<tr><th>Base</th><th>Winner</th><th>a</th><th>b</th><th>RMSE</th><th>Confidence</th><th>Schema</th><th>Derived</th><th>Units/Notes</th><th>Status</th></tr>")
    # rows already sorted
    for r in rows:
        # formatting numbers: a/b -> 4 decimals max, rmse 4-6 decimals
        def fmt_param(x):
            if x is None: return ''
            try:
                return f"{x:.4g}"
            except:
                return html_escape(x)
        def fmt_rmse(x):
            if x is None: return ''
            return f"{x:.6g}" if x < 0.0001 else f"{x:.4g}"
        badge_class = 'badge-new' if ('improved' in (r.get('notes','') or '').lower() or 'improved' in (r.get('status') or '')) else 'badge-default'
        badge_text = 'محسّن' if badge_class == 'badge-new' else 'موجود'
        html.append("<tr>")
        html.append(f"<td>{html_escape(r['base'])}</td>")
        html.append(f"<td>{html_escape(r['winner'])}</td>")
        html.append(f"<td>{fmt_param(r['a'])}</td>")
        html.append(f"<td>{fmt_param(r['b'])}</td>")
        html.append(f"<td>{fmt_rmse(r['rmse'])}</td>")
        html.append(f"<td>{'' if r.get('conf') is None else f"{r['conf']:.4g}"}</td>")
        html.append(f"<td>{html_escape(r['schema'])}</td>")
        html.append(f"<td>{html_escape(r['derived'])}</td>")
        units_and_notes = []
        if r.get('units'):
            units_and_notes.append(', '.join([f"{k}={v}" for k,v in r['units'].items()]))
        if r.get('notes'):
            units_and_notes.append(html_escape(r['notes']))
        html.append(f"<td>{html_escape('; '.join(units_and_notes))}</td>")
        html.append(f"<td><span class='{badge_class}'>" + html_escape(badge_text) + "</span></td>")
        html.append("</tr>")
    html.append("</table>")
    with open(args.out, "w", encoding="utf-8") as f:
        f.write("\n".join(html))
    print(f"✅ wrote {args.out}")

if __name__ == "__main__":
    main()
