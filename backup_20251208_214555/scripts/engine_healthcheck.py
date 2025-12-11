#!/usr/bin/env python3
"""Quick healthcheck runner for Core_Engines modules.

Tries to import each python module under Core_Engines and call a
module-level `healthcheck()` function if present, otherwise attempt to
find a class with a `healthcheck` or `process_task` method and call it.

Prints a concise per-engine status line.
"""
import os
import sys
import importlib
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / 'Core_Engines'

sys.path.insert(0, str(ROOT))

results = []

for p in sorted(CORE.glob('*.py')):
    name = p.stem
    if name.startswith('_'):
        continue
    modname = f"Core_Engines.{name}"
    try:
        mod = importlib.import_module(modname)
    except Exception as e:
        results.append((name, 'import-error', str(e)))
        continue
    # Try module-level healthcheck
    try:
        if hasattr(mod, 'healthcheck') and callable(getattr(mod, 'healthcheck')):
            ok = mod.healthcheck()
            results.append((name, 'ok', ok))
            continue
    except Exception as e:
        results.append((name, 'healthcheck-failed', str(e)))
        continue
    # Try class-based instance healthcheck
    try:
        # find any attribute that looks like Engine class
        inst = None
        for attr in dir(mod):
            if attr[0].isupper():
                cls = getattr(mod, attr)
                try:
                    obj = None
                    if isinstance(cls, type):
                        try:
                            obj = cls()
                        except Exception:
                            # try with no-arg failure fallback: skip
                            obj = None
                    if obj and hasattr(obj, 'healthcheck') and callable(getattr(obj, 'healthcheck')):
                        hc = obj.healthcheck()
                        results.append((name, 'ok', { 'class': attr, 'health': hc }))
                        inst = True
                        break
                except Exception:
                    continue
        if inst:
            continue
    except Exception as e:
        results.append((name, 'instance-check-failed', str(e)))
        continue
    # fallback: try process_task
    try:
        for attr in dir(mod):
            if attr[0].isupper():
                cls = getattr(mod, attr)
                if isinstance(cls, type):
                    try:
                        obj = cls()
                        if hasattr(obj, 'process_task') and callable(getattr(obj, 'process_task')):
                            try:
                                res = obj.process_task({'task': 'health'})
                                results.append((name, 'ok', { 'class': attr, 'process_task': res }))
                                break
                            except Exception as e:
                                results.append((name, 'process_task-failed', str(e)))
                                break
                    except Exception:
                        continue
    except Exception as e:
        results.append((name, 'final-failed', str(e)))
        continue
    # If nothing matched, report unknown
    results.append((name, 'no-check', 'no healthcheck or class found'))

# print summary
for r in results:
    name, status, detail = r
    print(f"{name:30} | {status:20} | {str(detail)[:200]}")

# exit with non-zero if any import-errors
import_errors = [r for r in results if r[1].endswith('error') or r[1].endswith('failed')]
if import_errors:
    sys.exit(2)

sys.exit(0)
