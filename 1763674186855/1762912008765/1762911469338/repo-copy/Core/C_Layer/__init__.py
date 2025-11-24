"""Core C-Layer (Consciousness orchestration) package.

This module exposes light-weight components and a small factory so the
state logger can be created by the system bootstrap without import cycles.

Usage:
    from Core.C_Layer import create_state_logger
    logger = create_state_logger(config={})

The factory `create_engine` is provided as an alias so existing bootstrap
helpers that look for `create_engine` will detect and instantiate the
component automatically.
"""

from .intent_types import Intent, IntentKind
from .intent_generator import IntentGenerator
from .intent_planner import IntentPlanner
from .perception_loop import PerceptionLoop as PerceptionProvider
from .state_logger import StateLogger as CStateLogger
from .c_layer import CLayer


def create_state_logger(config: dict | None = None, bridge: object | None = None, registry: object | None = None):
    """Factory for the C-Layer StateLogger.

    - `config` is currently unused but accepted for future extensibility.
    - `bridge` and `registry` are accepted to keep the signature compatible
      with other engine factories; registry may be used to register the
      created logger if provided.
    """
    cfg = config or {}
    # allow passing a maxlen via config
    maxlen = cfg.get("maxlen") if isinstance(cfg, dict) else None
    logger = CStateLogger(maxlen=maxlen)
    # optional registration
    try:
        if registry is not None and hasattr(registry, "register"):
            try:
                registry.register("C_Layer_StateLogger", logger)
            except TypeError:
                try:
                    registry.register("C_Layer_StateLogger", logger)
                except Exception:
                    pass
    except Exception:
        pass
    return logger


def create_engine(config: dict | None = None, registry: object | None = None):
    """Backward-compatible alias used by bootstrap_register_all_engines."""
    return create_state_logger(config=config, registry=registry)


__all__ = [
    "Intent", "IntentKind", "IntentGenerator", "IntentPlanner",
    "PerceptionProvider", "CStateLogger", "CLayer", "create_state_logger", "create_engine",
]
