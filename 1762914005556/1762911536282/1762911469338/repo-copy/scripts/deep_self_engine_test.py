"""Deeper test for the multi-layer self-modification system.

This test will:
- create a sandbox directory under `artifacts/self_engineer_deep_test`
- instantiate SafeSelfModificationSystem with `allow_live_apply=True` but only targeting the sandbox
- run a small modification plan that writes a file and appends to a memory key
- print the returned result and list sandbox contents
"""
from __future__ import annotations
import os
import sys
import json
from pathlib import Path

# ensure repo root on path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from Self_Improvement.safe_self_mod import SafeSelfModificationSystem


def main():
    sandbox_dir = os.path.join('artifacts', 'self_engineer_deep_test')
    os.makedirs(sandbox_dir, exist_ok=True)

    ssm = SafeSelfModificationSystem(sandbox_dir=sandbox_dir, allow_live_apply=True)

    plan = {
        'steps': [
            {'op': 'write_file', 'path': 'test_dir/hello.txt', 'content': 'Hello from deep self-engine test'},
            {'op': 'append_memory', 'key': 'notes', 'value': {'msg': 'deep-test-entry', 'ts': None}},
        ]
    }

    print('Running deep self-modify test; sandbox:', sandbox_dir)
    res = ssm.safe_self_modify(plan)
    print('Result:')
    print(json.dumps(res, indent=2))

    print('\nSandbox listing:')
    for root, _dirs, files in os.walk(sandbox_dir):
        for fn in files:
            p = os.path.join(root, fn)
            rel = os.path.relpath(p, sandbox_dir)
            print('-', rel)

    # If memory file exists, print its contents
    memf = os.path.join(sandbox_dir, 'memory_notes.json')
    if os.path.exists(memf):
        print('\nContents of memory_notes.json:')
        with open(memf, 'r', encoding='utf-8') as f:
            print(f.read())

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
