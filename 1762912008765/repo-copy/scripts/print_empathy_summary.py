import json
from pathlib import Path

p = Path('reports') / 'agl_emotion_training_results.json'
if not p.exists():
    print('Report file not found:', p)
    raise SystemExit(1)

data = json.loads(p.read_text(encoding='utf-8'))

total = len(data)
init_ok = 0
rev_ok = 0

print('نتائج التدريب العاطفي — ملخّص')
print('-----------------------------------')
for item in data:
    id = item.get('id')
    scenario = item.get('scenario')
    init = bool(item.get('init_empathy'))
    rev = bool(item.get('rev_empathy'))
    if init:
        init_ok += 1
    if rev:
        rev_ok += 1
    print(f"#{id}: init_empathy={init}  rev_empathy={rev}  - {scenario[:80].replace('\n',' ')}")

init_pct = (init_ok / total) * 100 if total else 0
rev_pct = (rev_ok / total) * 100 if total else 0

print('\n-----------------------------------')
print(f'عدد الأمثلة: {total}')
print(f'إجابات أولية متعاطفة: {init_ok} / {total}  ({init_pct:.1f}%)')
print(f'إجابات مُنقّحة متعاطفة: {rev_ok} / {total}  ({rev_pct:.1f}%)')
print('النسبة النهائية للاجابات الصحيحة (المُنقّحة): {:.1f}%'.format(rev_pct))
