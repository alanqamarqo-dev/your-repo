#!/usr/bin/env python
"""Generate a combined system report (HTML) that aggregates JSON reports and HTML reports under `reports/`.

Usage:
  python -m scripts.report_summary --out reports/full_system_report.html
"""
from __future__ import annotations
import os, glob, json, argparse
from datetime import datetime, timezone

def safe_read(path: str) -> str:
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f'<!-- failed to read {path}: {e} -->'

def collect_reports(root: str = 'reports'):
    js = sorted(glob.glob(os.path.join(root, '**', '*.json'), recursive=True))
    hs = sorted(glob.glob(os.path.join(root, '**', '*.html'), recursive=True))
    return js, hs

HTML_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <title>AGL Full System Report</title>
  <style>
    body{font-family:system-ui,Segoe UI,Arial;margin:20px;color:#111}
    h1{margin:0 0 8px}
    .meta{color:#666;margin-bottom:16px}
    details{margin:12px 0;padding:8px;border-radius:8px;border:1px solid #eee;background:#fafafa}
    pre{background:#111;color:#eee;padding:12px;border-radius:6px;overflow:auto}
    iframe{width:100%;height:600px;border:1px solid #ddd;border-radius:6px}
    .col{display:flex;gap:12px;flex-wrap:wrap}
    .small{font-size:0.9em;color:#444}
  </style>
</head>
<body>
  <h1>AGL — Full System Report</h1>
  <div class="meta">Generated: {now} — Aggregated reports under `{root}`</div>

  <h2>HTML Reports (embedded)</h2>
  {html_blocks}

  <h2>JSON Reports (inline)</h2>
  {json_blocks}

  <footer class="small">AGL • Combined report • {now}</footer>
</body>
</html>
"""

def make_html_blocks(html_files, out_path):
    blocks = []
    out_dir = os.path.dirname(os.path.abspath(out_path)) or '.'
    for p in html_files:
        # skip the target file if inside reports
        if os.path.abspath(p) == os.path.abspath(out_path):
            continue
        rel = os.path.relpath(p, start=out_dir)
        title = os.path.basename(p)
        blk = f"<details><summary>{title}</summary>\n<iframe src=\"{rel}\"></iframe>\n</details>"
        blocks.append(blk)
    return '\n'.join(blocks) if blocks else '<div class="small">No HTML reports found.</div>'

def make_json_blocks(json_files):
    blocks = []
    for p in json_files:
        try:
            with open(p, 'r', encoding='utf-8') as f:
                j = json.load(f)
            pretty = json.dumps(j, indent=2, ensure_ascii=False)
        except Exception as e:
            pretty = f'failed to read {p}: {e}'
        title = os.path.basename(p)
        blk = f"<details><summary>{title}</summary>\n<pre>{pretty}</pre>\n</details>"
        blocks.append(blk)
    return '\n'.join(blocks) if blocks else '<div class="small">No JSON reports found.</div>'

def main():
    ap = argparse.ArgumentParser(description='Generate combined system report')
    ap.add_argument('--root', default='reports', help='reports root folder')
    ap.add_argument('--out', default='reports/full_system_report.html', help='output HTML file')
    args = ap.parse_args()

    js, hs = collect_reports(args.root)
    html_blocks = make_html_blocks(hs, args.out)
    json_blocks = make_json_blocks(js)

    now = datetime.now(timezone.utc).isoformat()
    out_html = (HTML_TEMPLATE
                .replace('{now}', now)
                .replace('{root}', args.root)
                .replace('{html_blocks}', html_blocks)
                .replace('{json_blocks}', json_blocks))
    os.makedirs(os.path.dirname(args.out) or '.', exist_ok=True)
    with open(args.out, 'w', encoding='utf-8') as f:
        f.write(out_html)
    print(f'wrote {args.out}')

if __name__ == '__main__':
    main()
