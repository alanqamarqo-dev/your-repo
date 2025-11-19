import json
from pathlib import Path

files = [
    Path('artifacts/reports/agi_adv_case1.json'),
    Path('artifacts/reports/agi_adv_case2.json'),
    Path('artifacts/reports/agi_adv_case3.json'),
    Path('artifacts/reports/academic_agi_results.json'),
]

for f in files:
    print('='*60)
    print(f)
    if not f.exists():
        print('MISSING')
        continue
    try:
        s = f.read_text(encoding='utf-8')
        print(s)
        d = json.loads(s)
        # heuristic: if score_total present
        if isinstance(d, dict) and 'score_total' in d:
            print('\nنسبة الإجابات الصحيحة: {:.2f}%'.format(d.get('score_total', 0)))
        # academic results may be a dict with domains list
        elif isinstance(d, dict) and 'domains' in d and isinstance(d['domains'], list):
            vals = []
            for item in d['domains']:
                if isinstance(item, dict) and 'overall_score' in item:
                    vals.append(float(item['overall_score']))
            if vals:
                print('\nمتوسط النسبة عبر المجالات: {:.2f}%'.format(sum(vals)/len(vals)))
        # or list of reports
        elif isinstance(d, list):
            # try to average score_total if present
            vals = []
            for it in d:
                if isinstance(it, dict) and 'score_total' in it:
                    vals.append(float(it['score_total']))
            if vals:
                print('\nمتوسط score_total: {:.2f}%'.format(sum(vals)/len(vals)))
    except Exception as e:
        print('ERROR reading/parsing:', e)

print('='*60)
