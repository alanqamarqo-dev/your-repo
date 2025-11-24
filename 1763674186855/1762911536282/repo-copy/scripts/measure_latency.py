"""Lightweight latency and fallback measurement script.

Calls /process, /rag/answer, and /meta/evaluate on the local dev server
and computes mean and p95 latencies as well as counts of fallback vs real
engine responses.

Usage:
    python scripts/measure_latency.py --base http://127.0.0.1:8000 --runs 10
"""
import argparse
import json
import time
import statistics
from typing import List, Dict

import requests


def measure_once(session: requests.Session, url: str, json_body: dict) -> Dict:
    start = time.perf_counter()
    try:
        r = session.post(url, json=json_body, timeout=30)
        latency = (time.perf_counter() - start) * 1000
        data = r.json() if r.headers.get('content-type', '').startswith('application/json') else {'raw': r.text}
        return {'ok': r.ok, 'status_code': r.status_code, 'latency_ms': latency, 'data': data}
    except Exception as e:
        latency = (time.perf_counter() - start) * 1000
        return {'ok': False, 'status_code': None, 'latency_ms': latency, 'error': str(e), 'data': {}}


def summarize(latencies: List[float]):
    if not latencies:
        return {'count': 0}
    s = sorted(latencies)
    return {
        'count': len(s),
        'mean_ms': statistics.mean(s),
        'p95_ms': s[int(len(s) * 0.95) - 1] if len(s) >= 1 else s[-1],
        'min_ms': s[0],
        'max_ms': s[-1]
    }


def run(base: str, runs: int = 10):
    sess = requests.Session()
    endpoints = [
        ('process', f'{base.rstrip("/")}/process', {'text': 'Explain Newton\'s laws briefly.'}),
        ('rag', f'{base.rstrip("/")}/rag/answer', {'query': 'List three uses of graphite.'}),
        ('meta', f'{base.rstrip("/")}/meta/evaluate', {'plan': 'Step1: collect data; Step2: analyze; Step3: report'})
    ]

    results = {name: {'latencies': [], 'fallbacks': 0, 'success': 0, 'errors': [], 'nonempty_sources': 0, 'meta_scores': []} for name, _, _ in endpoints}

    for i in range(runs):
        for name, url, body in endpoints:
            r = measure_once(sess, url, body)
            results[name]['latencies'].append(r['latency_ms'])
            if not r.get('ok'):
                results[name]['errors'].append(r.get('error') or r.get('status_code'))
            else:
                results[name]['success'] += 1
                # detect fallback by engine=='noop' or presence of fallback note
                data = r.get('data') or {}
                engine = data.get('engine') or (data.get('evaluation') or {}).get('engine')
                # some endpoints embed engine inside data/raw
                is_fallback = False
                if isinstance(engine, str) and engine.lower() in ('noop', 'none', 'fallback'):
                    is_fallback = True
                # heuristic: meta fallback returns evaluation.score with note
                if name == 'meta' and data.get('evaluation', {}).get('notes', '').startswith('fallback'):
                    is_fallback = True
                results[name]['fallbacks'] += 1 if is_fallback else 0
                # record if RAG returned non-empty sources
                if name == 'rag':
                    sources = data.get('sources') if isinstance(data.get('sources'), list) else (data.get('raw', {}).get('sources') if isinstance(data.get('raw'), dict) else None)
                    if sources and isinstance(sources, list) and len(sources) > 0:
                        results[name]['nonempty_sources'] += 1
                # record meta evaluation scores
                if name == 'meta':
                    eval_obj = data.get('evaluation') if isinstance(data.get('evaluation'), dict) else None
                    score = None
                    if eval_obj and isinstance(eval_obj.get('score'), (int, float)):
                        score = float(eval_obj.get('score'))
                    # some implementations return {'score': 0.5} as nested
                    if score is not None:
                        results[name]['meta_scores'].append(score)

    summary = {}
    for name in results:
        s = summarize(results[name]['latencies'])
        s.update({
            'success': results[name]['success'],
            'fallbacks': results[name]['fallbacks'],
            'errors': results[name]['errors'],
            'nonempty_sources': results[name].get('nonempty_sources', 0),
            'meta_scores': results[name].get('meta_scores', [])
        })
        # compute meta score stats if present
        scores = s.get('meta_scores') or []
        if isinstance(scores, list) and len(scores) > 0:
            s['meta_score_mean'] = statistics.mean(scores)
            s['meta_score_min'] = min(scores)
            s['meta_score_max'] = max(scores)
        summary[name] = s

    # persist summary to logs/latency_summary.json
    try:
        import os
        logdir = os.path.join(os.getcwd(), 'logs')
        os.makedirs(logdir, exist_ok=True)
        outp = os.path.join(logdir, 'latency_summary.json')
        with open(outp, 'w', encoding='utf-8') as f:
            json.dump({'base': base, 'runs': runs, 'summary': summary}, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

    print(json.dumps({'base': base, 'runs': runs, 'summary': summary}, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--base', default='http://127.0.0.1:8000', help='Base URL of dev server')
    p.add_argument('--runs', type=int, default=5, help='Number of iterations per endpoint')
    args = p.parse_args()
    run(args.base, runs=args.runs)
