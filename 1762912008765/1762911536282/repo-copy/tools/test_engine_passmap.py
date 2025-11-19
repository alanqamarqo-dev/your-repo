#!/usr/bin/env python3
import unittest
import json
from pathlib import Path
import sys
import importlib.util

ROOT = Path(__file__).resolve().parents[1]
TEST_DIR = ROOT / 'tests'

# Ensure repository root is on sys.path so tests can import project modules
sys.path.insert(0, str(ROOT))

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
    name = path.name.lower()
    if 'inference' in name or 'self_learning' in name or 'law' in name:
        return 'Learning_System'
    if 'protocol' in name or 'orchestrator' in name or 'planner' in name:
        return 'Integration_Layer'
    if 'quantum' in name:
        return 'Core_Engines'
    return 'other'


class Collector(unittest.TextTestRunner):
    pass


def run_and_collect():
    loader = unittest.TestLoader()
    test_files = sorted(TEST_DIR.glob('test_*.py'))
    if not test_files:
        print('No test files found under tests/ (pattern test_*.py)')
        return

    engine_stats = {}
    total_run = total_passed = total_failed = total_skipped = 0
    for p in test_files:
        # Load the test file as a module directly from its path to avoid
        # requiring a tests package or relying on import machinery.
        try:
            spec = importlib.util.spec_from_file_location(p.stem, str(p))
            if spec is None or spec.loader is None:
                raise ImportError(f'Could not create import spec for {p}')
            mod = importlib.util.module_from_spec(spec)
            # mypy/linters may complain; we ensured spec and loader are not None above
            spec.loader.exec_module(mod)  # type: ignore[attr-defined]
            suite = loader.loadTestsFromModule(mod)
        except Exception as e:
            print(f'ERROR loading {p}: {e}')
            # record as a single failing test for reporting consistency
            # create a dummy failed result by running a failing TestCase
            suite = unittest.TestSuite()
            def _fail():
                raise ImportError(f'Failed to load {p}')
            class _FailCase(unittest.TestCase):
                def runTest(self):
                    _fail()
            suite.addTest(_FailCase())
        # run
        runner = unittest.TextTestRunner(stream=sys.stdout, verbosity=2)
        result = runner.run(suite)
        run = result.testsRun
        failed = len(result.failures) + len(result.errors)
        skipped = len(result.skipped)
        passed = run - failed - skipped

        engine = classify_test_file(p) if p.exists() else 'other'
        stats = engine_stats.setdefault(engine, {'run': 0, 'passed': 0, 'failed': 0, 'skipped': 0})
        stats['run'] += run
        stats['passed'] += passed
        stats['failed'] += failed
        stats['skipped'] += skipped

        total_run += run
        total_passed += passed
        total_failed += failed
        total_skipped += skipped
        print(f'  {p.name}: engine={engine}  run={run} passed={passed} failed={failed} skipped={skipped}')

    overall = {
        'total_run': total_run,
        'total_passed': total_passed,
        'total_failed': total_failed,
        'total_skipped': total_skipped,
    }

    out = {'per_engine': engine_stats, 'overall': overall}
    # write to file for inspection
    out_path = ROOT / 'reports' / 'test_engine_summary.json'
    out_path.parent.mkdir(exist_ok=True, parents=True)
    out_path.write_text(json.dumps(out, indent=2), encoding='utf-8')
    print(json.dumps(out, indent=2))


if __name__ == '__main__':
    run_and_collect()
