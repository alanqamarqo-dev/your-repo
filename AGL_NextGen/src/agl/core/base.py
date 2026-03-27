import asyncio
import importlib.util
import os
import sys
from types import ModuleType


def _load_module_from_path(path: str, name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    loader = spec.loader
    if loader is None:
        raise ImportError(f"Cannot load module {name} from {path}")
    loader.exec_module(module)
    return module


# Make sure repo-copy is on sys.path so imports inside mission_control work
_repo_copy_dir = os.path.join(os.path.dirname(__file__), 'repo-copy')
if _repo_copy_dir not in sys.path:
    sys.path.insert(0, _repo_copy_dir)

# Try to find the mission control module in the repo
_mc_path = os.path.join(_repo_copy_dir, 'dynamic_modules', 'mission_control_enhanced.py')
_mc = None
if os.path.exists(_mc_path):
    try:
        _mc = _load_module_from_path(_mc_path, 'mission_control_enhanced')
    except Exception:
        # fall back to importing by name
        try:
            import mission_control_enhanced as _mc
        except Exception:
            _mc = None


class _AGL:
    def __init__(self, backend_module: ModuleType | None):
        self._m = backend_module

    def _normalize_result(self, res):
        # Accept strings, dicts, objects — try to return a string
        if res is None:
            return ''
        if isinstance(res, str):
            return res
        if isinstance(res, dict):
            for k in ('reply', 'result', 'response', 'text'):
                if k in res:
                    return res[k]
            # fallback to raw or join values
            if 'raw' in res:
                return str(res['raw'])
            return str(res)
        return str(res)

    def ask(self, prompt: str, timeout: float = 60.0) -> str:
        """Synchronous convenience wrapper used by tests. Attempts to call
        available backend functions in `_mc` and returns a string.
        """
        if self._m is None:
            raise ImportError('mission_control_enhanced backend not found')

        # Candidate callables in order of preference
        candidates = [
            'ask',
            'process_with_unified_agi',
            'creative_innovate_unified',
            'reason_with_unified',
        ]

        for name in candidates:
            fn = getattr(self._m, name, None)
            if not fn:
                continue
            try:
                if asyncio.iscoroutinefunction(fn):
                    res = asyncio.run(fn(prompt))
                else:
                    # Some wrappers expect dict payloads
                    try:
                        res = fn(prompt)
                    except TypeError:
                        res = fn({'task_text': prompt})
                return self._normalize_result(res)
            except Exception:
                # try next candidate
                continue

        raise RuntimeError('No suitable backend function found to handle ask()')


# exported instance
agl = _AGL(_mc)
