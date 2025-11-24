#!/usr/bin/env python3
"""Run the AGL hybrid test #1 (context understanding) using AGL core engines.

This script constructs the test input as requested and calls the AGL
instance (AGL.process_complex_problem) so the system's engines generate the
answer. It times the response, saves full JSON to reports/aglh_test_results.json
and prints a short summary to the terminal.
"""
from __future__ import annotations

import os
import time
import json
from pathlib import Path

# ensure project root is importable
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from AGL import create_agl_instance


REPORTS_DIR = Path('reports')
REPORTS_DIR.mkdir(exist_ok=True)
OUT_PATH = REPORTS_DIR / 'aglh_test_results.json'


def build_test1():
    story = (
        "كان أحمد يلعب في الحديقة. رأى قطة جميلة تلاحق فراشة.\n"
        "ثم سمع صوت بكاء طفل صغير. ترك القطة وركض لمساعدة الطفل.\n"
    )
    questions = [
        "لماذا ترك أحمد القطة؟",
        "ما هي المشاعر المحتملة لأحمد في كل موقف؟",
        "كيف كان يمكن أن يتصرف بشكل مختلف؟",
    ]
    prompt = f"قصة:\n{story}\nالأسئلة:\n" + '\n'.join(f"{i+1}. {q}" for i, q in enumerate(questions))
    return prompt


def run_test1():
    agl = create_agl_instance({'operational_mode': 'supervised_autonomy'})

    test_prompt = build_test1()

    print('Running AGL Hybrid Test #1 (Context understanding)')
    start = time.time()
    # Let AGL.process_complex_problem orchestrate across its engines
    try:
        out = agl.process_complex_problem(test_prompt, context={'audience': 'evaluation'})
    except Exception as e:
        out = {'ok': False, 'error': str(e)}
    duration = time.time() - start

    result = {
        'test': 'hybrid_test_1_context_understanding',
        'timestamp': time.time(),
        'duration_seconds': duration,
        'input': test_prompt,
        'output': out,
    }

    with open(OUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    # Print concise terminal summary
    print('\n=== Test 1 Summary ===')
    print(f"Duration: {duration:.2f}s")
    try:
        conf = out.get('confidence_score', out.get('confidence', None))
        if conf is not None:
            print(f"Reported confidence: {float(conf):.3f}")
    except Exception:
        pass

    # Attempt to extract a human-readable solution from the output
    sol = None
    try:
        sol = out.get('solution') or out.get('solution', {})
    except Exception:
        sol = out

    # fallback: print short excerpt of the formatted output
    try:
        import json as _json
        excerpt = _json.dumps(sol, ensure_ascii=False, indent=2)[:2000]
        print('\nExcerpt of output (truncated):\n')
        print(excerpt)
    except Exception:
        print('Could not render output excerpt')

    print(f"Full results written to: {OUT_PATH}")


if __name__ == '__main__':
    run_test1()
