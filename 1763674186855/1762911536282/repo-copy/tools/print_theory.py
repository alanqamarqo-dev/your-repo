#!/usr/bin/env python3
import json
from pathlib import Path
import sys

TB = Path('artifacts') / 'theory_bundle.json'
HTML = Path('reports') / 'theory_report.html'

def short(s, n=300):
    if s is None:
        return ''
    s = str(s).strip()
    return s if len(s) <= n else s[:n].rsplit(' ',1)[0] + '...'

def main():
    if not TB.exists():
        print('ملف theory_bundle.json غير موجود في artifacts. شغّل pipeline أولاً (tools/run_theory.py).')
        return 2
    data = json.loads(TB.read_text(encoding='utf-8'))
    metrics = data.get('metrics', {})
    narr = data.get('narratives', [])
    links = data.get('links', [])

    print('\n========== تقرير النتيجة — AGL-III (المرحلة) ==========' )
    print('\nالملف:', TB)
    if HTML.exists():
        print('تقرير HTML:', HTML)
    print('\nالملخّص:')
    print('  - عدد السرديات:', metrics.get('narratives_count', len(narr)))
    print('  - عدد المجالات المغطاة:', metrics.get('domains_count', len(set(n.get("domain") for n in narr))))
    print('  - الروابط المكتشفة:', metrics.get('links_count', len(links)))
    print('  - coherence:', metrics.get('coherence'))
    print('  - consistency:', metrics.get('consistency'))
    print('  - falsifiability:', metrics.get('falsifiability'))
    print('  - coverage:', metrics.get('coverage'))

    print('\nأمثلة (أعلى 5 سرديات حسب الترتيب):\n')
    for i, n in enumerate(narr[:5], start=1):
        print(f"#{i} — domain: {n.get('domain','-')}  confidence: {n.get('confidence', 0):.2f}")
        print('id:', n.get('id'))
        print(short(n.get('text'), 800))
        print('-' * 60)

    if links:
        print('\nروابط عينة:')
        for l in links[:10]:
            # support multiple possible link schemas: (a_idx,b_idx,score) or (a,b,weight) or (a,b,score)
            a_lbl = None
            b_lbl = None
            # prefer index labels if present
            if l.get('a_idx') is not None:
                a_lbl = l.get('a_idx')
            elif l.get('a') is not None:
                a_lbl = l.get('a')
            else:
                a_lbl = l.get('a_label') if l.get('a_label') is not None else 'N/A'

            if l.get('b_idx') is not None:
                b_lbl = l.get('b_idx')
            elif l.get('b') is not None:
                b_lbl = l.get('b')
            else:
                b_lbl = l.get('b_label') if l.get('b_label') is not None else 'N/A'

            # score may be under different keys
            score = l.get('score')
            if score is None:
                score = l.get('weight')
            if score is None:
                score_str = 'N/A'
            else:
                try:
                    score_str = f"{float(score):.2f}"
                except Exception:
                    score_str = str(score)

            print(f"- {a_lbl} <-> {b_lbl} (score={score_str})")
    else:
        print('\nلا توجد روابط مكتشفة في هذه النسخة.')

    print('\nملف bundle كامل: artifacts/theory_bundle.json')
    print('تقرير HTML مفصل: reports/theory_report.html')
    print('\n===== نهاية التقرير =====\n')
    return 0

if __name__ == '__main__':
    sys.exit(main())
