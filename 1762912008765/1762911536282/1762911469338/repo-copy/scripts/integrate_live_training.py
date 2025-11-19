#!/usr/bin/env python3
"""Integrate a live training dry-run result into improvement history and memory candidates.

Usage: python scripts/integrate_live_training.py --result artifacts/models/physics_live_1/results.json
"""
import argparse
import json
import os
from pathlib import Path
from Knowledge_Base.Improvement_History import ImprovementHistory
from infra.adaptive.AdaptiveMemory import MEM_PATH


def normalize_result(res: dict, src_path: str) -> dict:
    base = res.get('base') or Path(src_path).stem
    y = res.get('yname')
    x = res.get('xname')
    top = res.get('results', [])
    best = top[0] if top else {}
    fit = best.get('fit', {})
    rec = {
        'source': src_path,
        'base': base,
        'yname': y,
        'xname': x,
        'fit': fit,
        'n_samples': best.get('n_samples', res.get('n_samples', 0)),
    }
    return rec


def append_candidate(candidate: dict, out_path: str):
    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open('a', encoding='utf-8') as f:
        f.write(json.dumps(candidate, ensure_ascii=False) + '\n')


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--result', required=True, help='Path to results.json produced by safe training')
    p.add_argument('--candidates', default='artifacts/memory/long_term_candidates.jsonl')
    args = p.parse_args()

    path = Path(args.result)
    if not path.exists():
        print('Result file not found:', str(path))
        return

    try:
        res = json.loads(path.read_text(encoding='utf-8'))
    except Exception as e:
        print('Failed to read result JSON:', e)
        return

    rec = normalize_result(res, str(path))

    # record to improvement history
    try:
        ih = ImprovementHistory()
        ih.record({'type': 'live_training_result', 'data': rec})
    except Exception:
        pass

    # append to candidate list
    try:
        append_candidate({'ts': __import__('time').time(), 'candidate': rec}, args.candidates)
    except Exception:
        pass

    # also append a short entry to the long-term memory file for inspection (but not promoted)
    try:
        from infra.adaptive.AdaptiveMemory import MEM_PATH as LT
        LT.parent.mkdir(parents=True, exist_ok=True)
        with LT.open('a', encoding='utf-8') as f:
            f.write(json.dumps({'ts': __import__('time').time(), 'kind': 'candidate', 'domain': rec.get('base'), 'text': json.dumps(rec, ensure_ascii=False)}, ensure_ascii=False) + '\n')
    except Exception:
        pass

    # touch a signal file for the meta controller
    try:
        sig = Path('artifacts/training_cycle_signal.json')
        sig.write_text(json.dumps({'last_result': str(path), 'domain': rec.get('base')}), encoding='utf-8')
    except Exception:
        pass

    print('Integrated', str(path))


if __name__ == '__main__':
    main()
