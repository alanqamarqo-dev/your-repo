import json
from pathlib import Path

ROOT = Path('d:/AGL')
outputs = ROOT / 'artifacts' / 'agi_system_run_outputs.json'
evalf = ROOT / 'artifacts' / 'agi_test_evaluation.json'
resultsf = ROOT / 'artifacts' / 'agi_test_results.json'

if not outputs.exists():
    print('No system outputs found at', outputs); raise SystemExit(2)
data = json.loads(outputs.read_text(encoding='utf-8'))

# Print Q&A
print('\nQUESTIONS & SYSTEM ANSWERS')
print('='*80)
for part, entry in data.items():
    prompt = None
    # try to fetch prompt from results artifact if available
    if resultsf.exists():
        r = json.loads(resultsf.read_text(encoding='utf-8'))
        if part in r:
            prompt = r[part].get('prompt')
    print(f'PART: {part}')
    if prompt:
        print('Q:', prompt)
    else:
        print('Q: (prompt not available)')
    print('Engine:', entry.get('engine'))
    print('Intent:', entry.get('intent'))
    print('A:')
    print(entry.get('reply'))
    print('-'*80)

# Compute simple success percentage using keyword_score threshold (fallback to results file)
threshold = 0.6
total = 0
passed = 0
if resultsf.exists():
    r = json.loads(resultsf.read_text(encoding='utf-8'))
    for part, v in r.items():
        total += 1
        ks = v.get('keyword_score', 0)
        ok = v.get('ok', False)
        if ok and ks >= threshold:
            passed += 1

pct = (passed / total * 100) if total else 0.0

# Also report overall similarity if evaluation file exists
sim = None
if evalf.exists():
    ev = json.loads(evalf.read_text(encoding='utf-8'))
    sim = ev.get('overall_similarity')

print('\nSUMMARY')
print('='*40)
print(f'Parts evaluated: {total}')
print(f'Passed (keyword_score >= {threshold} and ok): {passed} -> {pct:.1f}%')
if sim is not None:
    print(f'Overall similarity (mean): {sim:.3f} -> {sim*100:.1f}%')

print('\nReport artifacts:')
print(' - System outputs:', outputs)
print(' - Results (keyword scores):', resultsf if resultsf.exists() else '(missing)')
print(' - Evaluation (similarity):', evalf if evalf.exists() else '(missing)')
