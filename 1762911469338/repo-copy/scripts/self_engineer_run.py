"""Lightweight runner for the Self-Engineer loop.

Behavior:
 - Loads rules JSON
 - Ensures KB exists by copying lock -> main if present
 - Runs the available Self-Engineer CLI or falls back to Self_Improvement.self_engineer_smoke.quick_smoke
 - Writes outputs to the requested out dir
"""
from __future__ import annotations
import os
import sys
import json
import shutil
from datetime import datetime, timezone

ROOT = os.path.abspath(os.getcwd())
RULES_DEFAULT = os.path.join(ROOT, 'configs', 'self_engineer_rules.json')

def ensure_kb():
    lock = os.path.join('Knowledge_Base', 'Learned_Patterns.lock.json')
    dest = os.path.join('Knowledge_Base', 'Learned_Patterns.json')
    if os.path.exists(lock):
        shutil.copyfile(lock, dest)

def load_rules(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def main(argv=None):
    import argparse
    import sys
    from pathlib import Path

    # ensure repo root on path
    ROOT = Path(__file__).resolve().parents[1]
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    argv = argv or sys.argv[1:]
    parser = argparse.ArgumentParser()
    parser.add_argument('--rules', default=RULES_DEFAULT)
    parser.add_argument('--out', default='reports/self_engineer')
    parser.add_argument('--sandbox', default='artifacts/self_engineer_runs')
    parser.add_argument('--loop', action='store_true', help='Run Self-Engineer in loop mode')
    parser.add_argument('--max-iters', type=int, default=3)
    parser.add_argument('--auto-promote', action='store_true')
    args = parser.parse_args(argv)

    out = args.out
    sandbox_root = args.sandbox
    rules = args.rules

    os.makedirs(out, exist_ok=True)
    os.makedirs(sandbox_root, exist_ok=True)

    ensure_kb()

    try:
        r = load_rules(rules)
    except Exception:
        r = {}

    timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
    run_dir = os.path.join(sandbox_root, f'run_{timestamp}')
    os.makedirs(run_dir, exist_ok=True)

    # Prefer an existing CLI module (try multiple interfaces safely)
    decision = None
    # Try Self_Improvement variant first
    try:
        from Self_Improvement.Self_Engineer import SelfEngineer as SE1  # type: ignore
        try:
            # try constructor with expected args
            se = SE1(rules=r, out_dir=out, sandbox=run_dir)  # type: ignore
            if hasattr(se, 'run_cycle'):
                decision = se.run_cycle(dry_run=False)  # type: ignore
        except TypeError:
            # fallback to no-arg constructor
            se = SE1()  # type: ignore
            if hasattr(se, 'run_cycle'):
                decision = se.run_cycle(task=r.get('suggested_task', 'predict_y') if isinstance(r, dict) else 'predict_y', models_report={}, data_profile={}, budget=3, dry_run=False)  # type: ignore
    except Exception:
        # ignore and try next
        decision = None

    # If still nothing, try Learning_System helper module
    if decision is None:
        try:
            import Learning_System.Self_Engineer as se_mod  # type: ignore
            SE2 = getattr(se_mod, 'SelfEngineer', None)
            if SE2:
                se2 = SE2(load_rules(rules) if isinstance(rules, str) else {})
                if args.loop and hasattr(se2, 'run_loop'):
                    decision = se2.run_loop(task='predict_y', models_report={}, data_profile={}, max_iters=args.max_iters, auto_promote=args.auto_promote, out_dir=out)
                elif hasattr(se2, 'run_cycle'):
                    decision = se2.run_cycle(task='predict_y', models_report={}, data_profile={}, budget=3, dry_run=False)
            else:
                # fallback to module-level quick_smoke
                if hasattr(se_mod, 'quick_smoke'):
                    decision = se_mod.quick_smoke()
        except Exception as e:
            print('Self-Engineer runner failed:', e)
            return 2

    if decision is None:
        print('Self-Engineer runner produced no decision')
        return 2

    with open(os.path.join(out, 'decision_report.json'), 'w', encoding='utf-8') as f:
        json.dump(decision, f, indent=2)

    # touch summary and patch placeholders
    with open(os.path.join(out, 'summary.txt'), 'w', encoding='utf-8') as f:
        f.write('Self-Engineer run completed. See decision_report.json for details.\n')

    patch_file = os.path.join(out, 'patch.diff')
    open(patch_file, 'a', encoding='utf-8').close()

    print('Self-Engineer run complete. Outputs in:', out)
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
