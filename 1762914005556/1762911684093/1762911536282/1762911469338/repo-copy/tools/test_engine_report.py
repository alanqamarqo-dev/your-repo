#!/usr/bin/env python3
"""Run tests per-file, map tests to engine areas, and produce pass % per engine.

Heuristic mapping: scan each test file for references to top-level packages (Core_Engines,
Learning_System, Engineering_Engines, Integration_Layer, Scientific_Systems, Safety_Control,
Self_Improvement). If none matched, assign to 'other'.
"""
import io
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEST_DIR = ROOT / 'tests'

ENGINES = [
    'Core_Engines',
    'Learning_System',
    'Engineering_Engines',
    'Integration_Layer',
    'Scientific_Systems',
    'Safety_Control',
    'Self_Improvement',
]


def classify_test_file(path: Path):
    text = path.read_text(encoding='utf-8', errors='ignore')
    for e in ENGINES:
        if e in text:
            return e
    # also check for test filename hints
    name = path.name.lower()
    if 'inference' in name or 'self_learning' in name or 'law' in name:
        return 'Learning_System'
    if 'protocol' in name or 'orchestrator' in name or 'planner' in name:
        return 'Integration_Layer'
    if 'quantum' in name:
        return 'Core_Engines'
    return 'other'


def run_tests_for_module(module_name: str):
    loader = unittest.TestLoader()
    try:
        suite = loader.loadTestsFromName(module_name)
    except Exception as e:
        print(f'ERROR loading {module_name}: {e}', file=sys.stderr)
        return 0, 0, 0, 0
    buf = io.StringIO()
    runner = unittest.TextTestRunner(stream=buf, verbosity=2)
    result = runner.run(suite)
    run = result.testsRun
    failed = len(result.failures) + len(result.errors)
    skipped = len(result.skipped)
    passed = run - failed - skipped
    return run, passed, failed, skipped


def main():
    stats = {}
    total_run = total_passed = total_failed = total_skipped = 0
    test_files = sorted(TEST_DIR.glob('test_*.py'))
    if not test_files:
        print('No test files found under tests/ (pattern test_*.py)')
        sys.exit(2)

    print(f'Found {len(test_files)} test files; running each and classifying by engine...')
    for p in test_files:
        engine = classify_test_file(p)
        mod_name = 'tests.' + p.stem
        run, passed, failed, skipped = run_tests_for_module(mod_name)
        total_run += run
        total_passed += passed
        total_failed += failed
        total_skipped += skipped
        stats.setdefault(engine, {'run': 0, 'passed': 0, 'failed': 0, 'skipped': 0})
        stats[engine]['run'] += run
        stats[engine]['passed'] += passed
        stats[engine]['failed'] += failed
        stats[engine]['skipped'] += skipped
        print(f'  {p.name}: engine={engine}  run={run} passed={passed} failed={failed} skipped={skipped}')

    print('\nPer-engine summary:')
    for engine, s in sorted(stats.items()):
        run = s['run']
        passed = s['passed']
        failed = s['failed']
        skipped = s['skipped']
        pct = (passed / run * 100.0) if run else 0.0
        print(f'  {engine}: run={run} passed={passed} failed={failed} skipped={skipped} pass%={pct:.2f}')

    print('\nOverall:')
    overall_pct = (total_passed / total_run * 100.0) if total_run else 0.0
    print(f'  total tests run={total_run} passed={total_passed} failed={total_failed} skipped={total_skipped} pass%={overall_pct:.2f}')


if __name__ == '__main__':
    main()
