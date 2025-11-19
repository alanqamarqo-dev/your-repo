"""Compatibility shim: delegate to Learning_System.ExperienceMemory.

This module intentionally re-exports the canonical implementation located
in `Learning_System.ExperienceMemory`. That keeps older imports targeting
`Core_Engines.experience_memory` working while the canonical code lives in
the Learning_System package.
"""

try:
    import importlib

    _mod = importlib.import_module("Learning_System.ExperienceMemory")
    for _name in dir(_mod):
        if not _name.startswith("_"):
            globals()[_name] = getattr(_mod, _name)
    __all__ = [n for n in dir() if not n.startswith("_")]
except Exception:
    # Provide lightweight placeholders so imports don't crash during lint/run
    __all__ = []

    class _ShimError(RuntimeError):
        pass

    def ExperienceMemory(*a, **kw):
        raise _ShimError("Learning_System.ExperienceMemory not importable")

    def MicroUpdateScheduler(*a, **kw):
        raise _ShimError("Learning_System.MicroUpdateScheduler not importable")

    def compute_basic_metrics(*a, **kw):
        return {}
