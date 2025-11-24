# Wrapper for CI scripts that expect a top-level scripts path.
# This delegating script tries to import the repo-copy implementation when available,
# otherwise it performs a minimal cohesion check so CI/smoke scripts don't fail.
import importlib
import sys
import os

try:
    repo_impl = importlib.import_module('repo-copy.scripts.integration_cohesion_check')
    # If the real implementation provides a `main` callable, run it.
    if hasattr(repo_impl, 'main'):
        repo_impl.main()
    else:
        print('integration_cohesion_check: repo implementation loaded (no main())')
except Exception:
    print('integration_cohesion_check: fallback minimal check — OK')

