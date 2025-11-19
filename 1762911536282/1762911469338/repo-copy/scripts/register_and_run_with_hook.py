#!/usr/bin/env python3
"""Register a local inference hook (using TaskOrchestrator) and run a test module.

This script is safe to run locally in dev: it enables the lightweight
external-hooks glue in Integration_Layer.Domain_Router, provides a
flexible call_hook/get_external_hook adapter (accepts kwargs), registers
an "inference" hook that delegates to TaskOrchestrator.process(), and
then executes the specified test module as __main__.

Usage (from repo root):
  set AGL_EXTERNAL_HOOKS_ENABLE=1  # or in PowerShell: $env:AGL_EXTERNAL_HOOKS_ENABLE="1"
  py -3 scripts\register_and_run_with_hook.py

The script intentionally swallows non-fatal errors so it won't stop
other tests; it returns non-zero if the test module raises.
"""
import os
import sys
import importlib
import runpy

os.environ.setdefault("AGL_EXTERNAL_HOOKS_ENABLE", "1")

try:
    # Import Domain_Router and wrap call_hook to accept kwargs-friendly calls
    DR = importlib.import_module("Integration_Layer.Domain_Router")
except Exception as e:
    print("Could not import Integration_Layer.Domain_Router:", e, file=sys.stderr)
    DR = None

if DR is not None:
    # keep original
    _orig_call = getattr(DR, "call_hook", None)

    def _call_hook_flexible(name, *args, **kwargs):
        # Normalize payload: prefer a single dict positional arg, else kwargs
        payload = {}
        if args:
            first = args[0]
            if isinstance(first, dict):
                payload = first
            else:
                # treat first positional as prompt/text
                payload = {"prompt": first}
        payload.update(kwargs)
        if _orig_call:
            return _orig_call(name, payload)
        return []

    # attach wrapper
    try:
        DR._original_call_hook = _orig_call
        DR.call_hook = _call_hook_flexible  # type: ignore
    except Exception:
        pass

    # provide get_external_hook(name) -> callable(**kwargs)
    def _get_external_hook(name: str):
        def _caller(**kwargs):
            res = DR.call_hook(name, kwargs)
            # prefer first result
            if isinstance(res, list) and res:
                return res[0]
            return None
        return _caller

    try:
        DR.get_external_hook = _get_external_hook  # type: ignore
    except Exception:
        pass

    # Register a conservative inference hook that prefers Domain_Router.route
    try:
        def _inference_hook_router_first(payload: dict):
            try:
                prompt = payload.get("prompt") or payload.get("task") or payload.get("text") or ""
                # prefer using Domain_Router.route to avoid pulling external model manifests
                if DR is not None and hasattr(DR, "route"):
                    try:
                        r = DR.route(prompt)
                        if isinstance(r, dict):
                            for k in ("text", "reply_text", "answer", "output"):
                                if k in r and r.get(k) is not None:
                                    return {"text": str(r.get(k))}
                            return {"text": str(r)}
                    except Exception:
                        pass

                # fallback: try TaskOrchestrator.process if available
                try:
                    from Integration_Layer.Task_Orchestrator import TaskOrchestrator
                    _orch = TaskOrchestrator()
                    out = _orch.process(prompt)
                    if isinstance(out, dict):
                        for k in ("text", "result", "reply", "answer"):
                            if k in out and out.get(k) is not None:
                                return {"text": str(out.get(k))}
                        return {"text": str(out)}
                    return {"text": str(out)}
                except Exception:
                    return {"text": prompt}
            except Exception as e:
                return {"error": str(e)}

        try:
            DR.register_hook("inference", _inference_hook_router_first)
            print("Registered conservative inference hook (router-first) via Integration_Layer.Domain_Router.register_hook")
        except Exception as e:
            print("Failed to register inference hook:", e, file=sys.stderr)
    except Exception as e:
        print("Failed to set up router-first hook:", e, file=sys.stderr)

# Finally, execute the desired test module (default to the mini-neutral test)
module_to_run = os.environ.get("AG_TEST_MODULE", "tests.test_agi_mini_neutral")
try:
    runpy.run_module(module_to_run, run_name="__main__")
except SystemExit as e:
    # propagate the exit code
    code = int(e.code) if isinstance(e.code, int) else 0
    sys.exit(code)
except Exception as e:
    print("Test module raised an exception:", e, file=sys.stderr)
    raise
