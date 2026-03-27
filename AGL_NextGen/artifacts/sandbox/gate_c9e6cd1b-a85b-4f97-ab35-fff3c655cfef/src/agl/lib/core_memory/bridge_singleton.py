from typing import Optional

# Prefer NextGen in-package path; fall back to legacy top-level paths if present.
try:
    from agl.lib.core_memory.Conscious_Bridge import ConsciousBridge
except Exception:
    try:
        from Core_Memory.Conscious_Bridge import ConsciousBridge  # type: ignore
    except Exception:
        try:
            from Conscious_Bridge import ConsciousBridge  # type: ignore
        except Exception:
            ConsciousBridge = None  # safe fallback if module missing
import builtins


def get_bridge():
    """Return a process-wide ConsciousBridge singleton.

    We store the instance on the builtin module to avoid duplicated
    module imports (pytest/test collection can import modules via
    different paths, leading to multiple bridge_singleton module objects).
    """
    if ConsciousBridge is None:
        return None
    name = '_AGL_CONSCIOUS_BRIDGE_SINGLETON'
    try:
        br = getattr(builtins, name, None)
        if br is None:
            br = ConsciousBridge(stm_capacity=512)
            try:
                setattr(builtins, name, br)
            except Exception:
                # fallback: if builtins is not writable for some reason,
                # keep br in a module-global variable as last resort
                global _BRIDGE
                _BRIDGE = br
        return br
    except Exception:
        return None
