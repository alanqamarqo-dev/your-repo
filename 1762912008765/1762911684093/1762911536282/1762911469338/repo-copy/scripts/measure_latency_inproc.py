"""Measure latency using FastAPI TestClient (in-process) so we don't need uvicorn.

This calls server.app endpoints directly and reports mean/p95 and fallback counts.
"""
import time
import json
import statistics
from fastapi.testclient import TestClient
import os, sys
# ensure project root is on sys.path
sys.path.append(os.getcwd())
from server import app


def measure_call(client: TestClient, method: str, path: str, json_body: dict):
    start = time.perf_counter()
    r = client.post(path, json=json_body)
    dur = (time.perf_counter() - start) * 1000
    data = None
    try:
        data = r.json()
    except Exception:
        data = {'raw': r.text}
    return {'ok': r.status_code == 200, 'status_code': r.status_code, 'latency_ms': dur, 'data': data}


def summarize(latencies):
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


def run(runs=10):
    client = TestClient(app)
    endpoints = [
        ('process', '/process', {'text': "Explain Newton's laws briefly."}),
        ('rag', '/rag/answer', {'query': 'List three uses of graphite.'}),
        ('meta', '/meta/evaluate', {'plan': 'Step1: collect data; Step2: analyze; Step3: report'})
    ]

    results = {name: {'latencies': [], 'fallbacks': 0, 'success': 0, 'errors': []} for name, _, _ in endpoints}

    for i in range(runs):
        for name, path, body in endpoints:
            r = measure_call(client, 'post', path, body)
            results[name]['latencies'].append(r['latency_ms'])
            if not r['ok']:
                results[name]['errors'].append(r.get('status_code'))
            else:
                results[name]['success'] += 1
                data = r.get('data') or {}
                engine = data.get('engine') if isinstance(data, dict) else None
                is_fallback = False
                if isinstance(engine, str) and engine.lower() in ('noop', 'none', 'fallback'):
                    is_fallback = True
                if name == 'meta' and data.get('evaluation', {}).get('notes', '').startswith('fallback'):
                    is_fallback = True
                results[name]['fallbacks'] += 1 if is_fallback else 0

    summary = {}
    for name in results:
        s = summarize(results[name]['latencies'])
        s.update({'success': results[name]['success'], 'fallbacks': results[name]['fallbacks'], 'errors': results[name]['errors']})
        summary[name] = s

    print(json.dumps({'runs': runs, 'summary': summary}, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    run(runs=10)
