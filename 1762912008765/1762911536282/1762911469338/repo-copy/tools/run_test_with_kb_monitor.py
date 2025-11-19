#!/usr/bin/env python3
"""Run a unittest module while monitoring Knowledge_Base for deletes/renames.

This script monkeypatches os.remove, os.unlink, pathlib.Path.unlink and
shutil.rmtree to log calls that touch Knowledge_Base/Learned_Patterns.json. It
also polls the Knowledge_Base directory to detect when the canonical file
disappears or is renamed. Use this to reproduce and capture who removes the
KB during tests.
"""
import sys
import os
import time
import json
import shutil
import unittest
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

KB = Path(ROOT) / 'Knowledge_Base' / 'Learned_Patterns.json'
KB_DIR = KB.parent

log = []
lock = threading.Lock()

def _now():
    return time.time()

def record(evt: str, path=None, info=None):
    with lock:
        log.append({'t': _now(), 'evt': evt, 'path': str(path) if path is not None else None, 'info': info})

# Monkeypatch critical removal functions
orig_remove = os.remove
orig_unlink = os.unlink
orig_rmtree = shutil.rmtree
orig_path_unlink = Path.unlink

def watch_path(p):
    try:
        p = Path(p)
    except Exception:
        return False
    try:
        return KB in (p.resolve().parents or []) or p.resolve() == KB.resolve()
    except Exception:
        # could not resolve (file missing) — still check string containment
        return 'Knowledge_Base' in str(p)

def _rm(path, *args, **kwargs):
    record('os.remove', path)
    return orig_remove(path, *args, **kwargs)

def _unlink(path, *args, **kwargs):
    record('os.unlink', path)
    return orig_unlink(path, *args, **kwargs)

def _rmtree(path, *args, **kwargs):
    record('shutil.rmtree', path)
    return orig_rmtree(path, *args, **kwargs)

def _path_unlink(self, *args, **kwargs):
    record('Path.unlink', getattr(self, 'name', repr(self)))
    return orig_path_unlink(self, *args, **kwargs)

def poll_kb(stop_event: threading.Event):
    """Poll Knowledge_Base directory and record timeline of presence/absence."""
    last_exists = None
    last_listing = None
    while not stop_event.is_set():
        exists = KB.exists()
        try:
            listing = sorted([p.name for p in KB_DIR.iterdir()]) if KB_DIR.exists() else []
        except Exception as e:
            listing = ['<err:' + str(e) + '>']
        if exists != last_exists or listing != last_listing:
            record('poll_snapshot', {'exists': exists, 'listing': listing})
            last_exists = exists
            last_listing = listing
        time.sleep(0.05)

def run_tests(modules):
    # install monkeypatches
    os.remove = _rm
    os.unlink = _unlink
    shutil.rmtree = _rmtree
    Path.unlink = _path_unlink
    stop = threading.Event()
    t = threading.Thread(target=poll_kb, args=(stop,), daemon=True)
    t.start()
    try:
        loader = unittest.TestLoader()
        suite = unittest.TestSuite()
        for m in modules:
            suite.addTests(loader.loadTestsFromName(m))
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        record('unittest_result', {'testsRun': result.testsRun, 'failures': len(result.failures), 'errors': len(result.errors)})
        return result
    finally:
        stop.set()
        t.join(timeout=1.0)
        # restore
        os.remove = orig_remove
        os.unlink = orig_unlink
        shutil.rmtree = orig_rmtree
        Path.unlink = orig_path_unlink

if __name__ == '__main__':
    mods = ['tests.test_ensemble_selector']
    record('start', {'modules': mods})
    # ensure KB snapshot exists at start
    record('kb_initial_exists', KB.exists())
    res = run_tests(mods)
    record('kb_final_exists', KB.exists())
    # write log to file for inspection
    out = ROOT / 'logs' / 'kb_monitor_log.json'
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(log, f, ensure_ascii=False, indent=2)
    print('\nKB monitor finished; log written to:', out)
    # also print summary of interesting events
    for e in log:
        if e['evt'] in ('os.remove', 'os.unlink', 'shutil.rmtree', 'Path.unlink', 'poll_snapshot'):
            print(e)