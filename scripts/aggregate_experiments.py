import json
from collections import defaultdict, Counter
import sys

path = r"d:/AGL/artifacts/experiments.jsonl"
try:
    with open(path, 'r', encoding='utf-8') as f:
        lines = [json.loads(l) for l in f if l.strip()]
except Exception as e:
    print(f'ERROR reading {path}: {e}', file=sys.stderr)
    sys.exit(2)

# Aggregate per integration_id and lang
per_run = defaultdict(lambda: defaultdict(lambda: {
    'total': 0, 'correct': 0, 'similarities': [], 'winners': Counter(), 'fallback_hosted': 0
}))
overall = defaultdict(lambda: {'total': 0, 'correct': 0, 'similarities': []})
winner_counts = Counter()
fallback_hosted_count = 0

for obj in lines:
    iid = obj.get('integration_id')
    # summary entry
    if 'summary' in obj:
        s = obj['summary']
        lang = s.get('lang', 'unknown')
        if iid is None:
            iid = 'unknown'
        per_run[iid][lang]['total'] = s.get('total', per_run[iid][lang]['total'])
        per_run[iid][lang]['correct'] = s.get('correct', per_run[iid][lang]['correct'])
        overall[lang]['total'] += s.get('total', 0)
        overall[lang]['correct'] += s.get('correct', 0)
        continue

    # per-question entry
    lang = obj.get('lang')
    if iid is None or lang is None:
        # fallback entries like winner announcements without integration id
        # attempt to capture winner field
        w = obj.get('winner')
        if w:
            winner_counts[w] += 1
        continue

    # update per-run counters
    per_run[iid][lang]['total'] += 1
    sim = obj.get('similarity')
    if isinstance(sim, (int, float)):
        per_run[iid][lang]['similarities'].append(sim)
        overall[lang]['similarities'].append(sim)
    corr = obj.get('correct')
    if isinstance(corr, bool) and corr:
        per_run[iid][lang]['correct'] += 1
        overall[lang]['correct'] += 1
    # winner engine
    w = obj.get('winner_engine') or obj.get('winner')
    if w:
        per_run[iid][lang]['winners'][w] += 1
        winner_counts[w] += 1
    if obj.get('fallback_hosted'):
        per_run[iid][lang]['fallback_hosted'] += 1
        fallback_hosted_count += 1

# Print results
print('\nPer-run (integration_id) summaries:')
for iid, langs in per_run.items():
    print(f'\nIntegration id: {iid}')
    for lang, data in langs.items():
        total = data['total']
        correct = data['correct']
        acc = (correct/total) if total else 0
        avg_sim = (sum(data['similarities'])/len(data['similarities'])) if data['similarities'] else None
        winners = ', '.join(f'{k}:{v}' for k,v in data['winners'].most_common()) or 'None'
        print(f'  lang={lang:2} total={total:2} correct={correct:2} accuracy={acc:.2%} avg_sim={avg_sim if avg_sim is not None else "N/A"} winners={winners} fallback_hosted={data["fallback_hosted"]}')

print('\nOverall aggregates by language:')
for lang, data in overall.items():
    total = data['total']
    correct = data['correct']
    acc = (correct/total) if total else 0
    avg_sim = (sum(data['similarities'])/len(data['similarities'])) if data['similarities'] else None
    print(f'  lang={lang:2} total={total:2} correct={correct:2} accuracy={acc:.2%} avg_sim={avg_sim if avg_sim is not None else "N/A"}')

print('\nTop winner engines overall:')
for k,v in winner_counts.most_common(10):
    print(f'  {k:20} {v}')

print(f'\nTotal fallback_hosted occurrences: {fallback_hosted_count}')

# Quick observations
print('\nObservations:')
for lang, data in overall.items():
    total = data['total']
    correct = data['correct']
    acc = (correct/total) if total else 0
    print(f' - {lang}: accuracy {acc:.2%} ({correct}/{total})')

print('\nNotes:')
print(' - Many engine outputs are structured (deliberation/planner/gen_creativity) and were not extractive; hosted_storyqa was used as fallback in several runs.')
print(' - If you want a CSV or a plotted summary, I can write the exporter and generate it now.')

sys.exit(0)
