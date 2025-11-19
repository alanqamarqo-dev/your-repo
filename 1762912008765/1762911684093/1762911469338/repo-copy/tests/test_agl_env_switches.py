import os, importlib, contextlib, sys

@contextlib.contextmanager
def env(**kw):
    old = {k: os.environ.get(k) for k in kw}
    try:
        for k,v in kw.items():
            if v is None and k in os.environ: os.environ.pop(k)
            elif v is not None: os.environ[k] = str(v)
        yield
    finally:
        for k,v in old.items():
            if v is None and k in os.environ: os.environ.pop(k)
            elif v is not None: os.environ[k] = v


def test_retriever_k_defaults_stable():
    with env(AGL_RETRIEVER_K=None):
        importlib.invalidate_caches()
        # ensure a fresh import (pytest runs in single process so modules may be cached)
        if 'tools.evaluate_rag' in sys.modules:
            del sys.modules['tools.evaluate_rag']
        mod = importlib.import_module('tools.evaluate_rag')
        # module exposes _AGL_RETRIEVER_K as the configured default
        assert getattr(mod, '_AGL_RETRIEVER_K', None) == 5


def test_retriever_k_env_changes_behavior():
    with env(AGL_RETRIEVER_K="11"):
        importlib.invalidate_caches()
        if 'tools.evaluate_rag' in sys.modules:
            del sys.modules['tools.evaluate_rag']
        mod = importlib.import_module('tools.evaluate_rag')
        assert getattr(mod, '_AGL_RETRIEVER_K', None) == 11
