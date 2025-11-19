from pathlib import Path
import json

ART = Path("artifacts")
REPORTS = Path("reports")
REPORTS.mkdir(parents=True, exist_ok=True)

TEMPLATE = """
<!doctype html>
<html>
<head><meta charset="utf-8"><title>Theory Report</title></head>
<body>
<h1>Theory Report</h1>
<p>Metrics: {metrics}</p>
<h2>Narratives</h2>
{narratives}
<h2>Links</h2>
{links}
</body>
</html>
"""

def render(theory_bundle_path: Path):
    data = json.loads(theory_bundle_path.read_text(encoding='utf-8'))
    metrics = data.get('metrics', {})
    narratives = data.get('narratives', [])
    links = data.get('links', [])

    nar_html = ''.join([f"<div><h3>{i+1}. {n.get('domain','')}</h3><p>{n.get('text')}</p></div>" for i,n in enumerate(narratives)])
    items = []
    for l in links:
        a = l.get('a_idx') or l.get('a') or l.get('a_id') or ''
        b = l.get('b_idx') or l.get('b') or l.get('b_id') or ''
        score = l.get('score') if l.get('score') is not None else l.get('weight') if l.get('weight') is not None else None
        if score is None:
            score_s = ''
        else:
            try:
                score_s = f" (score={float(score):.2f})"
            except Exception:
                score_s = f" (score={score})"
        items.append(f"<li>{a} - {b}{score_s}</li>")
    links_html = '<ul>' + ''.join(items) + '</ul>'

    out = TEMPLATE.format(metrics=json.dumps(metrics, ensure_ascii=False), narratives=nar_html, links=links_html)
    target = REPORTS / "theory_report.html"
    target.write_text(out, encoding='utf-8')
    return target

if __name__ == '__main__':
    tb = ART / 'theory_bundle.json'
    if not tb.exists():
        print('theory_bundle.json not found in artifacts. Run reasoning/theory_pipeline.py first.')
    else:
        r = render(tb)
        print('WROTE', r)
