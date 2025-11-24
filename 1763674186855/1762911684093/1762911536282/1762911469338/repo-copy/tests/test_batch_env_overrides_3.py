import importlib
import os
import sys

def reload_with_env(mod_name, env_map):
    old = {k: os.environ.get(k) for k in env_map}
    try:
        for k, v in env_map.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = str(v)
        if mod_name in sys.modules:
            del sys.modules[mod_name]
        m = importlib.import_module(mod_name)
        importlib.reload(m)
        return m
    finally:
        for k, v in old.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def test_intent_top_n_override():
    m = reload_with_env("Core_Consciousness.Intent_Generator", {"AGL_INTENT_TOP_N": None})
    assert getattr(m, "_AGL_INTENT_TOP_N", None) in (3, getattr(m, "_DEFAULT", 3))
    m2 = reload_with_env("Core_Consciousness.Intent_Generator", {"AGL_INTENT_TOP_N": "7"})
    assert getattr(m2, "_AGL_INTENT_TOP_N", None) == 7


def test_social_ctx_chars_override():
    m = reload_with_env("Core_Engines.Social_Interaction", {"AGL_SOCIAL_CTX_CHARS": None})
    assert getattr(m, "_AGL_SOCIAL_CTX_CHARS", None) in (200, getattr(m, "_DEFAULT", 200))
    m2 = reload_with_env("Core_Engines.Social_Interaction", {"AGL_SOCIAL_CTX_CHARS": "180"})
    assert getattr(m2, "_AGL_SOCIAL_CTX_CHARS", None) == 180


def test_planner_max_steps_override():
    m = reload_with_env("Core_Engines.Reasoning_Planner", {"AGL_PLANNER_MAX_STEPS": None})
    assert getattr(m, "_AGL_PLANNER_MAX_STEPS", None) in (8, getattr(m, "_DEFAULT", 8))
    m2 = reload_with_env("Core_Engines.Reasoning_Planner", {"AGL_PLANNER_MAX_STEPS": "10"})
    assert getattr(m2, "_AGL_PLANNER_MAX_STEPS", None) == 10
