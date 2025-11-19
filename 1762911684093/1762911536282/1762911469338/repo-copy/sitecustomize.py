"""Ensure repo-copy root is on sys.path for all python invocations started from this tree.

This file is automatically imported by Python at startup when present on sys.path
and allows us to reliably add the repo root to sys.path so tests and imports
like `import agl` resolve consistently in the venv/CI environment.

Path: D:\AGL\repo-copy\sitecustomize.py
"""
import sys
import os

root = os.path.dirname(__file__)
if root not in sys.path:
    # Insert at position 0 so local package names take precedence during tests
    sys.path.insert(0, root)


# Optional bootstrap: auto-load persistent memory and build semantic index.
# Controlled by env var AGL_AUTO_LOAD_MEMORY (defaults to '1'). This keeps
# startup fast when disabled and ensures memory is ready for interactive/CI runs.
try:
    if os.getenv("AGL_AUTO_LOAD_MEMORY", "1").strip() not in ("0", "false", "no"):
        import logging as _logging
        _log = _logging.getLogger("AGL.bootstrap")
        _log.addHandler(_logging.StreamHandler())
        _log.setLevel(_logging.INFO)
        try:
            # import the bridge singleton and attempt to import DB and build index
            from Core_Memory.bridge_singleton import get_bridge as _get_bridge
            _br = _get_bridge()
            if _br is not None:
                try:
                    n = 0
                    try:
                        n = _br.import_ltm_from_db()
                    except Exception:
                        _log.debug("No DB import available or failed; skipping import.")
                    _log.info("Memory bootstrap: imported %d LTM rows", n)
                    try:
                        idx = _br.build_semantic_index()
                        _log.info("Memory bootstrap: semantic index built (%d docs)", idx)
                    except Exception:
                        _log.debug("Semantic indexing not available in this environment.")
                except Exception:
                    _log.debug("Bridge exists but import/index operations failed.")
            else:
                _log.debug("No ConsciousBridge available at bootstrap; skipping memory load.")
        except Exception:
            # Keep sitecustomize robust: do not fail interpreter startup on any error
            try:
                _log.debug("Memory bootstrap not completed (import error).")
            except Exception:
                pass
except Exception:
    # never fail on sitecustomize
    pass
