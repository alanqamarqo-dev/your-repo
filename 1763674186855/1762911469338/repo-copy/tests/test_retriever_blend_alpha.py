import importlib, os, sys
sys.path.insert(0, r'D:\AGL\repo-copy')

def reload_and_get_alpha():
    # ensure fresh import-time read
    if 'Core_Engines.GK_retriever' in sys.modules:
        del sys.modules['Core_Engines.GK_retriever']
    mod = importlib.import_module('Core_Engines.GK_retriever')
    return getattr(mod, '_AGL_RETRIEVER_BLEND_ALPHA', None)


def test_default_blend_alpha_is_zero():
    # default should be 0.0 unless env var set
    os.environ.pop('AGL_RETRIEVER_BLEND_ALPHA', None)
    a = reload_and_get_alpha()
    assert float(a) == 0.0


def test_env_override_blend_alpha():
    os.environ['AGL_RETRIEVER_BLEND_ALPHA'] = '0.6'
    a = reload_and_get_alpha()
    assert abs(float(a) - 0.6) < 1e-6
    os.environ.pop('AGL_RETRIEVER_BLEND_ALPHA', None)
