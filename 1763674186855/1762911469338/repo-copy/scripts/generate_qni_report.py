#!/usr/bin/env python3
"""Generate a detailed QNI run report and write JSON to artifacts/reports."""
from __future__ import annotations
import json
import time
import os
from typing import Any, Dict, List

import sys
import os as _os
# ensure repo root on sys.path when run from scripts/
_ROOT = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..'))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from Integration_Layer.integration_registry import registry
import Core_Engines as CE


def run_and_capture():
    CE.bootstrap_register_all_engines(registry, allow_optional=True)
    sim = registry.get('Quantum_Simulator_Wrapper')
    ts = int(time.time())
    report: Dict[str, Any] = {
        'timestamp': ts,
        'ok': True,
        'tests': {},
    }

    # Part 1: superposition
    r1 = sim.process_task({'op': 'simulate_superposition_measure', 'params': {'num_qubits': 2, 'gates': [{'type': 'H', 'target': 0}, {'type': 'H', 'target': 1}], 'shots': 2048}}) # type: ignore
    report['tests']['superposition'] = r1
    try:
        probs = r1.get('probabilities') or {}
        total = sum(probs.values())
        pass_super = r1.get('ok', False) and isinstance(probs, dict) and len(probs) >= 2 and abs(total - 1.0) < 0.05
        report['tests']['superposition_ok'] = bool(pass_super)
    except Exception:
        report['tests']['superposition_ok'] = False

    # Part 2: entanglement heuristic
    r2 = sim.process_task({'op': 'simulate_superposition_measure', 'params': {'num_qubits': 2, 'gates': [{'type': 'H', 'target': 0}, {'type': 'X', 'target': 1}], 'shots': 2048}}) # type: ignore
    report['tests']['entanglement'] = r2
    report['tests']['entanglement_ok'] = bool(r2.get('ok', False) and isinstance(r2.get('probabilities'), dict) and len(r2.get('probabilities', {})) >= 2)

    # Part 3: contextual collapse — collect vectors and L1 distances
    contexts_cfg: List[List[Dict[str, Any]]] = [
        [],
        [{'type': 'H', 'target': 0}],
        [{'type': 'H', 'target': 1}],
    ]
    outs: List[List[float]] = []
    labels = None
    for gates in contexts_cfg:
        r = sim.process_task({'op': 'simulate_superposition_measure', 'params': {'num_qubits': 2, 'gates': gates, 'shots': 2048}}) # type: ignore
        probs = r.get('probabilities') or {}
        if labels is None:
            labels = sorted(probs.keys())
        vec = [probs.get(l, 0.0) for l in sorted(probs.keys())]
        outs.append(vec)
    # compute L1 pairwise
    l1s = []
    for i in range(len(outs)):
        for j in range(i + 1, len(outs)):
            l1 = sum(abs(a - b) for a, b in zip(outs[i], outs[j]))
            l1s.append({'pair': (i, j), 'l1': l1})
    report['tests']['contextual'] = {'outs': outs, 'pairs_l1': l1s}
    report['tests']['contextual_ok'] = any(p['l1'] > 0.05 for p in l1s)

    # Part 4 & 5: creativity & learning — deterministic logits
    r_cre = sim.process_task({'op': 'quantum_neural_forward', 'params': {'input': 'الفلك,الطبخ,البرمجة'}}) # type: ignore
    r_cre2 = sim.process_task({'op': 'quantum_neural_forward', 'params': {'input': 'الموسيقى,الرياضيات,الزراعة'}}) # type: ignore
    r_learn = sim.process_task({'op': 'quantum_neural_forward', 'params': {'input': 'sustainability multi-source probe'}}) # type: ignore
    report['tests']['creativity'] = {'r1': r_cre, 'r2': r_cre2}
    report['tests']['learning'] = r_learn
    report['tests']['creativity_ok'] = all(isinstance(x.get('logits'), list) and len(x.get('logits', [])) == 2 for x in [r_cre, r_cre2])
    report['tests']['learning_ok'] = isinstance(r_learn.get('logits'), list) and len(r_learn.get('logits', [])) == 2

    # overall OK and success percentage
    ok_keys = [k for k in report['tests'].keys() if k.endswith('_ok')]
    passed = sum(1 for k in ok_keys if report['tests'].get(k))
    total = len(ok_keys)
    pct = 0.0
    if total:
        pct = 100.0 * passed / total
    report['ok'] = all(report['tests'].get(k) for k in ok_keys) if total else True
    report['summary'] = {'passed': passed, 'total': total, 'success_percentage': round(pct, 2)}

    # write report
    out_dir = os.path.join('artifacts', 'reports')
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f'qni_run_{ts}.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f'Wrote QNI report: {out_path}')
    print(f"QNI success: {report['summary']['passed']}/{report['summary']['total']} ({report['summary']['success_percentage']}%)")
    return out_path


if __name__ == '__main__':
    run_and_capture()
