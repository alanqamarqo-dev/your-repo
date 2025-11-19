import importlib
import os
import sys


def _reload_module_with_env(module_name: str, env: dict):
    # stash old values
    old = {k: os.environ.get(k) for k in env}
    try:
        # set env overrides
        for k, v in env.items():
            os.environ[k] = str(v)
        # ensure a fresh import picks up module-level env reads
        if module_name in sys.modules:
            del sys.modules[module_name]
        m = importlib.import_module(module_name)
        importlib.reload(m)
        return m
    finally:
        # restore environment
        for k, v in old.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def test_advanced_metareasoner_defaults_and_override():
    m = _reload_module_with_env('Core_Engines.AdvancedMetaReasoner', {})
    # default should match conservative behavior in repo
    assert getattr(m, '_AGL_ADV_META_EXAMPLES_LIMIT', None) == 5

    m2 = _reload_module_with_env('Core_Engines.AdvancedMetaReasoner', {'AGL_ADV_META_EXAMPLES_LIMIT': '7'})
    assert getattr(m2, '_AGL_ADV_META_EXAMPLES_LIMIT', None) == 7


def test_perception_loop_defaults_and_override():
    m = _reload_module_with_env('Core_Consciousness.Perception_Loop', {})
    assert getattr(m, '_AGL_PERCEPTION_EVENTS_LIMIT', None) == 20

    m2 = _reload_module_with_env('Core_Consciousness.Perception_Loop', {'AGL_PERCEPTION_EVENTS_LIMIT': '8'})
    assert getattr(m2, '_AGL_PERCEPTION_EVENTS_LIMIT', None) == 8


def test_visual_spatial_defaults_and_override():
    m = _reload_module_with_env('Core_Engines.Visual_Spatial', {})
    assert getattr(m, '_AGL_VISUAL_SPATIAL_OBJECTS_LIMIT', None) == 2
    assert getattr(m, '_AGL_VISUAL_SPATIAL_DEFAULT_DIM', None) == 5

    m2 = _reload_module_with_env('Core_Engines.Visual_Spatial', {'AGL_VISUAL_SPATIAL_OBJECTS_LIMIT': '4', 'AGL_VISUAL_SPATIAL_DEFAULT_DIM': '7'})
    assert getattr(m2, '_AGL_VISUAL_SPATIAL_OBJECTS_LIMIT', None) == 4
    assert getattr(m2, '_AGL_VISUAL_SPATIAL_DEFAULT_DIM', None) == 7
