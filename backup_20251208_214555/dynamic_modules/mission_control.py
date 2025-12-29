
"""
Proxy loader for mission control.

This file intentionally re-exports the merged/combined mission control API so
that any imports of `dynamic_modules.mission_control` (legacy callers and the
server code) will receive the unified implementation from
`dynamic_modules.mission_control_combined`.

It keeps the module surface stable: `execute_mission`, `run`, `quick_start`,
`quick_start_enhanced`, and `SmartFocusController` are forwarded when available.

If the combined module is missing, it falls back to the original legacy module
behavior to remain conservative.
"""

import importlib
import traceback

_combined = None
_legacy = None

try:
    _combined = importlib.import_module('dynamic_modules.mission_control_combined')
except Exception:
    _combined = None

if _combined:
    # re-export common symbols
    for _name in ('execute_mission', 'run', 'quick_start', 'quick_start_enhanced', 'SmartFocusController', 'unified_ui_execute'):
        if hasattr(_combined, _name):
            globals()[_name] = getattr(_combined, _name)
else:
    # fallback to legacy implementation if combined not available
    try:
        _legacy = importlib.import_module('dynamic_modules.mission_control')
    except Exception:
        _legacy = None

    if _legacy:
        for _name in ('execute_mission', 'run', 'quick_start', 'quick_start_enhanced', 'SmartFocusController', 'unified_ui_execute'):
            if hasattr(_legacy, _name):
                globals()[_name] = getattr(_legacy, _name)
    else:
        # last-resort stubs
        def execute_mission(*a, **k):
            return {"error": "no mission control available"}

        def run(*a, **k):
            return execute_mission(*a, **k)


# Defensive fallback: ensure `execute_mission` is always available for legacy callers.
# This handles cases where circular imports or import-time failures prevent the
# combined module from exporting the symbol.
if 'execute_mission' not in globals():
    import asyncio as _asyncio
    import threading as _threading
    import inspect as _inspect

    def _run_coro_in_thread(coro_func, *args, **kwargs):
        """Run a coroutine function in a fresh event loop inside a background thread
        and return its result synchronously. This avoids calling asyncio.run() from
        within an already-running event loop.
        """
        result = {}

        def _target():
            try:
                # Each thread needs its own event loop
                loop = _asyncio.new_event_loop()
                try:
                    _asyncio.set_event_loop(loop)
                    res = loop.run_until_complete(coro_func(*args, **kwargs))
                    result['value'] = res
                finally:
                    try:
                        loop.close()
                    except Exception:
                        pass
            except Exception as e:
                result['exc'] = e

        t = _threading.Thread(target=_target, daemon=True)
        t.start()
        t.join()
        if 'exc' in result:
            raise result['exc']
        return result.get('value')

    def execute_mission(mission_text: str, mission_type=None):
        # Try combined module first (if it was imported earlier)
        try:
            if _combined and hasattr(_combined, 'execute_mission'):
                return getattr(_combined, 'execute_mission')(mission_text, mission_type)
        except Exception:
            pass

        # Try enhanced module directly
        try:
            _enh_mod = importlib.import_module('dynamic_modules.mission_control_enhanced')
            # If enhanced exposes a synchronous execute_mission, call it
            if hasattr(_enh_mod, 'execute_mission'):
                return getattr(_enh_mod, 'execute_mission')(mission_text, mission_type)

            # If it exposes an async quick_start_enhanced, run it safely in a thread
            if hasattr(_enh_mod, 'quick_start_enhanced'):
                qse = getattr(_enh_mod, 'quick_start_enhanced')
                if _inspect.iscoroutinefunction(qse):
                    return _run_coro_in_thread(qse, mission_type or 'creative', mission_text)
                else:
                    # it's synchronous
                    return qse(mission_type or 'creative', mission_text)
        except Exception:
            pass

        # Legacy fallback
        try:
            if _legacy and hasattr(_legacy, 'execute_mission'):
                return getattr(_legacy, 'execute_mission')(mission_text, mission_type)
            if _legacy and hasattr(_legacy, 'run_real_mission'):
                return _legacy.run_real_mission()
        except Exception:
            pass

        # Last-resort stub
        return {"error": "no mission control execute_mission available"}

    # (Duplicate/older execute_mission removed — safe implementation above is used.)

