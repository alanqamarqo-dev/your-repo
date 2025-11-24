#!/usr/bin/env python3
"""Export a simple components report (JSON + CSV) classifying AGI-like components.

This script bootstraps Core_Engines into a local registry (dict), collects
registered engine names and ENGINE_SPECS, and writes a classification report
to `artifacts/components_report.json` and CSV.

It's conservative: marks a component as AGI-like when its name or module path
contains certain keywords (reason, learn, meta, planner, self, knowledge,
causal, strategic, orchestr, recall, memory, critic, reflect).
"""
from __future__ import annotations
import json
import csv
import os
from typing import Dict, Any

ROOT = os.path.dirname(os.path.dirname(__file__))
ART = os.path.join(ROOT, "artifacts")
os.makedirs(ART, exist_ok=True)

def is_agi_like(name: str, modpath: str) -> bool:
    s = (name + ' ' + (modpath or '')).lower()
    keywords = [
        'reason', 'learn', 'meta', 'planner', 'self', 'knowledge', 'causal',
        'strateg', 'orchestr', 'memory', 'critic', 'reflect', 'planner', 'agent'
    ]
    return any(k in s for k in keywords)

def main():
    # Try to read bootstrap_report.json (written by bootstrap_register_all_engines)
    bootstrap_path = os.path.join(ART, 'bootstrap_report.json')
    registered = {}
    ENGINE_SPECS = {}
    try:
        if os.path.exists(bootstrap_path):
            with open(bootstrap_path, 'r', encoding='utf-8') as f:
                br = json.load(f)
            for k in br.get('registered', []):
                registered[k] = True
            skipped = br.get('skipped', {}) or {}
        # try importing ENGINE_SPECS for module paths when available
        try:
            from Core_Engines import ENGINE_SPECS as ES  # type: ignore
            ENGINE_SPECS = ES or {}
        except Exception:
            ENGINE_SPECS = {}
    except Exception:
        # fallback: ensure variables exist
        registered = {}
        ENGINE_SPECS = {}

    # produce entries
    entries = []
    keys = set(list(registered.keys()) + list(ENGINE_SPECS.keys()))
    for k in sorted(keys):
        modpath = None
        try:
            spec = ENGINE_SPECS.get(k)
            if spec and isinstance(spec, (list, tuple)) and len(spec) >= 1:
                modpath = spec[0]
        except Exception:
            modpath = None
        agi_like = is_agi_like(k, modpath or '')
        entries.append({
            'name': k,
            'module': modpath or '',
            'registered': k in registered,
            'agi_like': agi_like,
        })

    out_json = os.path.join(ART, 'components_report.json')
    out_csv = os.path.join(ART, 'components_report.csv')
    with open(out_json, 'w', encoding='utf-8') as f:
        json.dump({'components': entries}, f, indent=2, ensure_ascii=False)

    with open(out_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['name', 'module', 'registered', 'agi_like'])
        writer.writeheader()
        for e in entries:
            writer.writerow(e)

    # summary
    total = len(entries)
    agi_count = sum(1 for e in entries if e['agi_like'])
    summary = {'total_components': total, 'agi_like_count': agi_count, 'agi_like_percent': (agi_count/total*100) if total else 0.0}
    with open(os.path.join(ART, 'components_report_summary.json'), 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print('Wrote', out_json, out_csv)
    print('Summary:', summary)

if __name__ == '__main__':
    main()
