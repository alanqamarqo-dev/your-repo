"""Shared process_task template and helper utilities for engines.

Engines that don't implement `process_task` can be given a safe default
adapter using `attach_default_process_task(obj, name)`. The adapter returns
an informative dict and avoids engine skips during bootstrap.
"""
from typing import Any, Callable
import logging

log = logging.getLogger("AGL.Core_Engines.process_task_template")


def make_default_process_task(name: str) -> Callable[[dict], dict]:
    def _process_task(payload: dict) -> dict:
        try:
            kind = (payload or {}).get("kind") if isinstance(payload, dict) else None
        except Exception:
            kind = None
        return {
            "ok": True,
            "engine": name,
            "note": "default process_task (no-op)",
            "kind": kind,
        }

    return _process_task


def attach_default_process_task(obj: Any, name: str) -> None:
    """Attach a default process_task to `obj` if missing.

    This binds a plain function as an attribute so callers can do `obj.process_task(payload)`.
    """
    if hasattr(obj, "process_task"):
        return
    fn = make_default_process_task(name)
    try:
        setattr(obj, "process_task", fn)
        log.debug("Attached default process_task to %s", name)
    except Exception:
        log.warning("Could not attach default process_task to %s", name)
