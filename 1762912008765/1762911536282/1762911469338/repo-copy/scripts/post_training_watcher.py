#!/usr/bin/env python3
"""Watch artifacts/models for new results.json and integrate them into the
advanced self-monitoring pipeline.

This script does not perform training; it detects new training results,
calls the integration script, writes self-monitoring events, and records
which results were processed to avoid duplicates.

Usage: python -m scripts.post_training_watcher --once
"""
import argparse
import json
import time
from pathlib import Path
import subprocess
import sys

ROOT = Path('.').resolve()
MODELS_DIR = ROOT / 'artifacts' / 'models'
PROCESSED = ROOT / 'artifacts' / 'processed_models.jsonl'
MONITOR_LOG = ROOT / 'artifacts' / 'self_monitoring.jsonl'


def list_results():
    out = []
    if not MODELS_DIR.exists():
        return out
    for d in MODELS_DIR.iterdir():
        if d.is_dir():
            r = d / 'results.json'
            if r.exists():
                out.append(r)
    return sorted(out, key=lambda p: p.stat().st_mtime)


def read_processed():
    seen = set()
    if PROCESSED.exists():
        try:
            for ln in PROCESSED.read_text(encoding='utf-8').splitlines():
                if not ln:
                    continue
                try:
                    rec = json.loads(ln)
                    seen.add(rec.get('result'))
                except Exception:
                    continue
        except Exception:
            pass
    return seen


def mark_processed(result_path: str):
    rec = {'ts': time.time(), 'result': result_path}
    PROCESSED.parent.mkdir(parents=True, exist_ok=True)
    with PROCESSED.open('a', encoding='utf-8') as f:
        f.write(json.dumps(rec, ensure_ascii=False) + '\n')


def append_monitor(event: dict):
    MONITOR_LOG.parent.mkdir(parents=True, exist_ok=True)
    with MONITOR_LOG.open('a', encoding='utf-8') as f:
        f.write(json.dumps(event, ensure_ascii=False) + '\n')


def detect_inconsistency(res: dict) -> dict:
    # Simple heuristics to flag possible data/format problems
    issues = []
    base = res.get('base')
    y = res.get('yname')
    x = res.get('xname')
    top = (res.get('results') or [])
    best = top[0] if top else {}
    fit = best.get('fit', {})
    rmse = fit.get('rmse')
    # If yname looks non-numeric (contains letters and not typical variable) flag it
    if isinstance(y, str) and any(c.isalpha() for c in y) and y.lower() in ('compound', 'name'):
        issues.append('non_numeric_y_column')
    if rmse == 0 or rmse == 0.0:
        issues.append('zero_rmse')
    # low sample count
    if best.get('n', best.get('n_samples', 0)) < 4:
        issues.append('low_sample_count')
    return {'issues': issues, 'n_issues': len(issues)}


def integrate_result(path: Path):
    # call existing integration module via venv python -m scripts.integrate_live_training
    py = sys.executable
    cmd = [py, '-m', 'scripts.integrate_live_training', '--result', str(path)]
    try:
        p = subprocess.run(cmd, check=False, capture_output=True, text=True)
        ok = p.returncode == 0
        out = p.stdout.strip() or p.stderr.strip()
    except Exception as e:
        ok = False
        out = str(e)
    return ok, out


def process_once():
    results = list_results()
    seen = read_processed()
    new = [r for r in results if str(r) not in seen]
    summary = {'processed': [], 'skipped': []}
    for r in new:
        try:
            data = json.loads(r.read_text(encoding='utf-8'))
        except Exception:
            data = {}
        inc = detect_inconsistency(data)
        evt = {'ts': time.time(), 'event': 'model_result_detected', 'result': str(r), 'domain': data.get('base'), 'inconsistency': inc}
        append_monitor(evt)

        ok, out = integrate_result(r)
        evt2 = {'ts': time.time(), 'event': 'integration_run', 'result': str(r), 'ok': ok, 'output': out}
        append_monitor(evt2)
        mark_processed(str(r))
        summary['processed'].append(str(r))
    return summary


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--once', action='store_true')
    args = p.parse_args()

    if args.once:
        s = process_once()
        print('Processed:', s)
        return

    # continuous mode: poll every 10s
    try:
        while True:
            process_once()
            time.sleep(10)
    except KeyboardInterrupt:
        print('post_training_watcher exiting')


if __name__ == '__main__':
    main()
