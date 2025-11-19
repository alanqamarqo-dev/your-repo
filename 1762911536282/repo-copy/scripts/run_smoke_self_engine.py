"""Lightweight smoke runner for the Self-Engineer loop.

This script invokes the existing `self_engineer_run.py` in the same
directory via runpy so it works even if `scripts/` isn't a package.

It propagates the SystemExit code from the target script so it can be
used directly from CI or the command line.
"""
from __future__ import annotations

import os
import sys
import runpy


def main(argv: list[str] | None = None) -> int:
    root = os.path.abspath(os.getcwd())
    # Ensure repo root is on path for imports used by the target script
    if root not in sys.path:
        sys.path.insert(0, root)

    target = os.path.join(os.path.dirname(__file__), 'self_engineer_run.py')
    if not os.path.exists(target):
        print('Target runner not found:', target)
        return 2

    print('Running smoke self-engineer using:', target)
    try:
        runpy.run_path(target, run_name='__main__')
    except SystemExit as e:
        code = int(e.code) if e.code is not None else 0
        print('Target exited with code:', code)
        return code
    except Exception as e:
        print('Error while running target:', e)
        return 3

    # If the target returned normally (no SystemExit), treat as success
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
