import json, os
from pathlib import Path

IN = Path('artifacts') / 'advanced_meta_report.json'
OUT = Path('artifacts') / 'advanced_meta_report.html'
if not IN.exists():
    print('no report found at', IN)
    raise SystemExit(1)

r = json.loads(IN.read_text(encoding='utf-8'))
q = r.get('quality', {})
plan = r.get('plan', [])

lines = []
lines.append('<!doctype html>')
lines.append('<html><head><meta charset="utf-8"><title>Advanced Meta Report</title></head><body>')
lines.append('<h1>Advanced Meta-Reasoner Report</h1>')
lines.append(f"<p>Analyzed at: {q.get('analyzed_at')}</p>")

lines.append('<h2>Quality Summary</h2>')
lines.append('<ul>')
for k in ['n_traces','n_memory_entries','contradictions','textual_contradictions']:
    lines.append(f"<li>{k}: {q.get(k)}</li>")
lines.append('</ul>')

lines.append('<h3>By Type</h3>')
lines.append('<ul>')
for t, c in (q.get('by_type') or {}).items():
    lines.append(f"<li>{t}: {c}</li>")
lines.append('</ul>')

lines.append('<h2>Domain Counts</h2>')
lines.append('<ul>')
for d, c in (q.get('domain_counts') or {}).items():
    lines.append(f"<li>{d}: {c}</li>")
lines.append('</ul>')

lines.append('<h2>Improvement Plan</h2>')
if not plan:
    lines.append('<p>No high-impact actions recommended.</p>')
else:
    for a in plan:
        lines.append('<div style="border:1px solid #ccc;padding:8px;margin:6px">')
        lines.append(f"<h3>{a.get('title')}</h3>")
        lines.append(f"<p>{a.get('reason')}</p>")
        if a.get('metadata'):
            lines.append('<pre>' + json.dumps(a.get('metadata'), indent=2, ensure_ascii=False) + '</pre>')
        lines.append(f"<p>Action: <code>{a.get('action')}</code> (impact_score={a.get('impact_score')})</p>")
        lines.append('</div>')

lines.append('<h2>Textual Conflict Examples</h2>')
for ex in (q.get('textual_conflict_examples') or []):
    lines.append('<pre>' + json.dumps(ex, indent=2, ensure_ascii=False) + '</pre>')

lines.append('<h2>Graph Issues</h2>')
for gi in (q.get('graph_issues') or []):
    lines.append('<pre>' + json.dumps(gi, indent=2, ensure_ascii=False) + '</pre>')

lines.append('<p>Artifacts directory: <a href="./artifacts">artifacts/</a></p>')
lines.append('</body></html>')
OUT.write_text('\n'.join(lines), encoding='utf-8')
print('WROTE', OUT)
