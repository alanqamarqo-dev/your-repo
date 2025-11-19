import json
from pathlib import Path
from difflib import SequenceMatcher
import textwrap

ROOT = Path('d:/AGL')
results_path = ROOT / 'artifacts' / 'agi_test_results.json'
refs_path = ROOT / 'artifacts' / 'agi_test_references.json'
out_path = ROOT / 'artifacts' / 'agi_test_evaluation.json'

if not results_path.exists():
    print('Missing results:', results_path)
    raise SystemExit(2)
if not refs_path.exists():
    print('Missing references:', refs_path)
    raise SystemExit(2)

results = json.loads(results_path.read_text(encoding='utf-8'))
refs = json.loads(refs_path.read_text(encoding='utf-8'))

def similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()

evaluation = {}
total_sim = 0.0
count = 0

for part, ref in refs.items():
    sys_out = results.get(part, {})
    ref_text = ref.get('answer','')
    sys_text = sys_out.get('response','')
    sim = similarity(ref_text, sys_text)
    # keyword coverage
    kws = ref.get('keywords', [])
    present = sum(1 for k in kws if k in sys_text)
    kw_cover = present / max(1, len(kws))
    evaluation[part] = {
        'similarity': sim,
        'keyword_coverage': kw_cover,
        'ref_len': len(ref_text),
        'sys_len': len(sys_text),
        'note': sys_out.get('raw', {}).get('note') if isinstance(sys_out.get('raw'), dict) else None,
    }
    total_sim += sim
    count += 1

overall = (total_sim / count) if count else 0.0

report = {
    'per_part': evaluation,
    'overall_similarity': overall,
}

out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')

print('\nAGI EVALUATION SUMMARY')
print('='*60)
for p, v in evaluation.items():
    print(f"{p}: similarity={v['similarity']:.3f}, keyword_coverage={v['keyword_coverage']:.2f}, sys_len={v['sys_len']}")
print('-'*60)
print(f"Overall similarity (mean): {overall:.3f}")
print('\nFull evaluation written to', out_path)
