#!/usr/bin/env python3
"""Inject a top 'Meta-Ensembler' blended badge into all HTML reports,
generate an ensemble_summary.html from self_optimization and fusion_weights,
update reports/report_manifest.json, and commit changes.
"""
import os, json, glob, subprocess

ROOT = os.path.dirname(os.path.dirname(__file__))
os.chdir(ROOT)

badge = ("<div style=\"position:sticky;top:0;z-index:9999;font-family:ui-sans-serif,system-ui,-apple-system;"
         "background:linear-gradient(90deg,#0ea5e9,#8b5cf6);color:white;padding:10px 14px;margin:0 0 12px 0;"
         "box-shadow:0 2px 10px rgba(0,0,0,.15);border-bottom-left-radius:10px;border-bottom-right-radius:10px\">"
         "  <strong>Meta-Ensembler</strong> — <span style=\"opacity:.9\">Blended results enabled</span>"
         "</div>\n")

def inject_badge_into_html():
    files = [p for p in glob.glob(os.path.join('reports','**','*.html'), recursive=True)]
    count = 0
    for f in files:
        try:
            with open(f, 'r', encoding='utf-8') as fh:
                t = fh.read()
        except Exception:
            continue
        if 'Meta-Ensembler' in t:
            continue
        new = t.replace('<body', '<body', 1)
        # insert badge after first <body...>
        import re
        m = re.search(r'<body([^>]*)>', new, flags=re.IGNORECASE)
        if m:
            idx = m.end()
            new = new[:idx] + '\n' + badge + new[idx:]
            with open(f, 'w', encoding='utf-8') as fh:
                fh.write(new)
            count += 1
    print(f"✅ Injected 'Blended' badge into {count} HTML files.")

def build_ensemble_summary():
    so_path = os.path.join('reports','self_optimization','self_optimization.json')
    fw_path = os.path.join('config','fusion_weights.json')
    if not os.path.exists(so_path):
        print(f"Self-optimization JSON not found at {so_path} — skipping ensemble summary generation")
        return False
    with open(so_path, 'r', encoding='utf-8') as fh:
        so = json.load(fh)
    fw = {}
    if os.path.exists(fw_path):
        with open(fw_path, 'r', encoding='utf-8') as fh:
            try:
                fw = json.load(fh)
            except Exception:
                fw = {}

    rows = []
    for base, sig in so.get('model_signals', {}).items():
        rmse = sig.get('rmse')
        conf = sig.get('confidence')
        rows.append(f"<tr><td style='padding:.5rem .75rem;border-bottom:1px solid #eee'>{base}</td><td style='padding:.5rem .75rem;border-bottom:1px solid #eee'>{rmse:.6f}</td><td style='padding:.5rem .75rem;border-bottom:1px solid #eee'>{conf:.3f}</td></tr>")

    w_items = []
    for k,v in (fw or {}).items():
        w_items.append(f"<li><code>{k}</code>: <b>{v}</b></li>")

    html = [
        '<!doctype html>',
        '<html lang="ar" dir="rtl">',
        '<head>',
        '<meta charset="utf-8"/>',
        '<title>AGL — ملخّص المزج (Meta-Ensembler)</title>',
        '<meta name="viewport" content="width=device-width, initial-scale=1"/>',
        '<style>body{font-family:ui-sans-serif,system-ui,-apple-system;background:#0b1220;color:#e5e7eb;margin:0;padding:24px}.card{background:rgba(255,255,255,.05);backdrop-filter:blur(6px);border:1px solid rgba(255,255,255,.09);border-radius:14px;padding:16px;margin:12px 0}h1{margin:.2rem 0 1rem 0} h2{margin:.5rem 0}table{width:100%;border-collapse:collapse;background:rgba(255,255,255,.02);border-radius:12px;overflow:hidden}a{color:#7dd3fc}.badge{display:inline-block;background:linear-gradient(90deg,#0ea5e9,#8b5cf6);color:#fff;padding:.35rem .6rem;border-radius:999px;font-size:.85rem}</style>',
        '</head>',
        '<body>',
        '<div class="badge">Meta-Ensembler — Blended</div>',
        '<h1>ملخّص المزج (Meta-Ensembler)</h1>',
        '<div class="card">',
        '  <h2>أوزان القنوات (Fusion Weights)</h2>',
        '  <ul>',
        '\n'.join(w_items),
        '  </ul>',
        '</div>',
        '<div class="card">',
        '  <h2>إشارات النماذج (Self-Optimization)</h2>',
        '  <table>',
        '    <thead>',
        '      <tr><th style="text-align:right;padding:.5rem .75rem;border-bottom:1px solid #eee">النموذج</th><th style="text-align:right;padding:.5rem .75rem;border-bottom:1px solid #eee">RMSE</th><th style="text-align:right;padding:.5rem .75rem;border-bottom:1px solid #eee">Confidence</th></tr>',
        '    </thead>',
        '    <tbody>',
        '\n'.join(rows),
        '    </tbody>',
        '  </table>',
        '  <p style="opacity:.85;margin-top:.75rem">البيانات مأخوذة من reports/self_optimization/self_optimization.json</p>',
        '</div>',
        '<div class="card">',
        '  <h2>روابط سريعة</h2>',
        '  <p><a href="models_report.html">models_report.html</a> — <a href="models_visual.html">models_visual.html</a> — <a href="safety_suite/safety_report.html">safety report</a></p>',
        '</div>',
        '</body>',
        '</html>'
    ]

    os.makedirs('reports', exist_ok=True)
    outpath = os.path.join('reports','ensemble_summary.html')
    with open(outpath, 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(html))
    print(f"✅ wrote {outpath}")
    return True

def update_manifest():
    mf = os.path.join('reports','report_manifest.json')
    if os.path.exists(mf):
        with open(mf, 'r', encoding='utf-8-sig') as fh:
            m = json.load(fh)
    else:
        m = { 'html': [], 'json': [] }
    if 'ensemble_summary.html' not in m.get('html', []):
        m['html'] = ['ensemble_summary.html'] + m.get('html', [])
    with open(mf, 'w', encoding='utf-8') as fh:
        json.dump(m, fh, ensure_ascii=False, indent=2)
    print('✅ manifest updated → reports/report_manifest.json')

def git_commit():
    try:
        subprocess.run(['git','add','reports','reports/report_manifest.json','config/fusion_weights.json'], check=False)
        subprocess.run(['git','commit','-m','UX: Inject Blended badge + add ensemble_summary.html (Meta-Ensembler)'], check=False)
        print('Committed changes (if any).')
    except Exception as e:
        print('git commit failed:', e)

def main():
    inject_badge_into_html()
    built = build_ensemble_summary()
    if built:
        update_manifest()
    git_commit()

if __name__ == '__main__':
    main()
