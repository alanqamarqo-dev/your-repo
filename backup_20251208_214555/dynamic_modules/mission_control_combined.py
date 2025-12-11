"""
Combined mission control facade.
- Prefer `mission_control_enhanced` when available.
- Fall back to `mission_control` legacy functions when needed.
- Export a stable API: `SmartFocusController`, `quick_start`, `quick_start_enhanced`, `execute_mission`, `run`.
"""
import importlib
import traceback

_enh = None
_legacy = None

try:
    _enh = importlib.import_module('dynamic_modules.mission_control_enhanced')
except Exception:
    _enh = None

try:
    _legacy = importlib.import_module('dynamic_modules.mission_control')
except Exception:
    _legacy = None


def _noop(*a, **k):
    return None


# Expose SmartFocusController (if present)
SmartFocusController = getattr(_enh, 'SmartFocusController', None) or getattr(_legacy, 'SmartFocusController', None) if _legacy else None

# Quick start (legacy compatibility)
if _enh and hasattr(_enh, 'quick_start'):
    quick_start = getattr(_enh, 'quick_start')
else:
    # legacy module uses run_real_mission or quick_start-like functions
    if _legacy and hasattr(_legacy, 'run_real_mission'):
        def quick_start(mission_type: str):
            # map mission_type heuristics to legacy run_real_mission
            return _legacy.run_real_mission()
    else:
        quick_start = lambda *a, **k: "No mission controller available"


if _enh and hasattr(_enh, 'quick_start_enhanced'):
    quick_start_enhanced = getattr(_enh, 'quick_start_enhanced')
else:
    # attempt to provide a simple async wrapper around legacy functionality
    async def quick_start_enhanced(mission_type: str, topic: str):
        if _legacy and hasattr(_legacy, 'run_real_mission'):
            return _legacy.run_real_mission()
        return {"error": "No enhanced mission controller available"}


# execute_mission / run compatibility
if _enh and hasattr(_enh, 'execute_mission'):
    execute_mission = getattr(_enh, 'execute_mission')
elif _legacy and hasattr(_legacy, 'execute_mission'):
    execute_mission = getattr(_legacy, 'execute_mission')
elif _legacy and hasattr(_legacy, 'run_real_mission'):
    def execute_mission(mission_text: str, mission_type=None):
        return _legacy.run_real_mission()
else:
    execute_mission = lambda *a, **k: {"error": "No mission executor available"}


def run(mission_text: str, mission_type=None):
    try:
        return execute_mission(mission_text, mission_type)
    except Exception:
        return {"error": "execute_mission failed", "trace": traceback.format_exc()}


# Re-export other useful helpers from enhanced if present
if _enh:
    for name in ('EnhancedMissionController', 'AdvancedIntegrationEngine', 'SmartFocusController', 'LLMIntegrationEngine'):
        if hasattr(_enh, name) and name not in globals():
            globals()[name] = getattr(_enh, name)


# Helper: run coroutine safely in a background thread if needed
def _run_coro_safely(coro_func, *args, **kwargs):
    import asyncio as _asyncio
    import threading as _threading
    import inspect as _inspect

    if not _inspect.iscoroutinefunction(coro_func):
        return coro_func(*args, **kwargs)

    result = {}

    def _target():
        try:
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


def unified_ui_execute(payload: dict) -> dict:
    """Unified UI entry point.

    Accept a dictionary payload from the UI (keys: `type`/`mission_type`,
    `topic`/`mission_text`, optional `metadata`) and route to the best
    available mission executor (enhanced or legacy). Returns a normalized
    merged response containing `mission_type`, `problem`/`mission`,
    `integration_result`, and `status`.

    This function intentionally lives in the combined facade so we don't
    create new files and legacy imports can access it via the proxy.
    """
    try:
        # Normalize input
        if not isinstance(payload, dict):
            return {"error": "payload must be a dict"}

        mt = payload.get('mission_type') or payload.get('type') or payload.get('task_type')
        text = payload.get('mission_text') or payload.get('topic') or payload.get('text') or payload.get('prompt')
        metadata = payload.get('metadata') or payload.get('meta') or {}

        # Basic heuristics if mission_type missing
        if not mt:
            _txt = (text or '').lower()
            if any(k in _txt for k in ("احسب", "حساب", "معادلة", "calculate", "compute")):
                mt = 'science'
            elif any(k in _txt for k in ("ابداع", "قصة", "creative", "story")):
                mt = 'creative'
            elif any(k in _txt for k in ("تقني", "build", "design", "develop")):
                mt = 'technical'
            else:
                mt = 'creative'

        # Prefer enhanced executor if available
        try:
            if _enh:
                # enhanced exposes a convenience async quick_start_enhanced
                if hasattr(_enh, 'quick_start_enhanced'):
                    res = _run_coro_safely(getattr(_enh, 'quick_start_enhanced'), mt, text)
                    # ensure normalized shape
                    if isinstance(res, dict):
                        return res
                    return {"mission_type": mt, "problem": text, "integration_result": res, "status": "completed"}

                # fallback to enhanced.execute_mission if present
                if hasattr(_enh, 'execute_mission'):
                    res = getattr(_enh, 'execute_mission')(text, mt)
                    if isinstance(res, dict):
                        return res
                    return {"mission_type": mt, "problem": text, "integration_result": res, "status": "completed"}
        except Exception:
            # swallow and try legacy
            pass

        # Use combined-level execute_mission or legacy
        try:
            if callable(execute_mission):
                res = execute_mission(text, mt)
                if isinstance(res, dict):
                    # ensure top-level fields
                    out = {
                        "mission_type": mt,
                        "problem": text,
                        "integration_result": res.get('integration_result') or res,
                        "status": res.get('status') or 'completed'
                    }
                    # include focused_output/llm_summary when present
                    if 'focused_output' in res:
                        out['focused_output'] = res['focused_output']
                    if 'llm_summary' in res:
                        out['llm_summary'] = res['llm_summary']
                    return out
                else:
                    return {"mission_type": mt, "problem": text, "integration_result": res, "status": "completed"}
        except Exception as e:
            return {"error": "executor_failed", "detail": str(e)}

        return {"error": "no executor available"}
    except Exception as exc:
        return {"error": "unified_ui_execute_exception", "detail": str(exc), "trace": traceback.format_exc()}
