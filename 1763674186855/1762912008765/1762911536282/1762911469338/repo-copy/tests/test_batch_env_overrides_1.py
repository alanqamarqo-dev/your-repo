import importlib, os, sys, contextlib

@contextlib.contextmanager
def env(**kw):
    old = {k: os.environ.get(k) for k in kw}
    try:
        for k,v in kw.items():
            if v is None: os.environ.pop(k, None)
            else: os.environ[k] = str(v)
        yield
    finally:
        for k,v in old.items():
            if v is None: os.environ.pop(k, None)
            else: os.environ[k] = v


def _reload(modname):
    if modname in sys.modules: del sys.modules[modname]
    return importlib.import_module(modname)


def test_general_knowledge_env_knobs():
    with env(AGL_GENERAL_KNOWLEDGE_CTX_CHARS="77", AGL_GENERAL_KNOWLEDGE_MAX_CHARS="555", AGL_GENERAL_KNOWLEDGE_TOPK="4"):
        m = _reload("Core_Engines.General_Knowledge")
        assert getattr(m, "_AGL_GENERAL_KNOWLEDGE_CTX_CHARS") == 77
        assert getattr(m, "_AGL_GENERAL_KNOWLEDGE_MAX_CHARS") == 555
        assert getattr(m, "_AGL_GENERAL_KNOWLEDGE_TOPK") == 4


def test_hypothesis_gen_topn():
    with env(AGL_HYPOTHESIS_TOP_N="9"):
        m = _reload("Core_Engines.Hypothesis_Generator")
        assert getattr(m, "_AGL_HYPOTHESIS_TOP_N") == 9


def test_meta_extra_chars():
    with env(AGL_META_EXTRA_CHARS="1111"):
        m = _reload("Integration_Layer.meta_orchestrator")
        assert getattr(m, "_AGL_META_EXTRA_CHARS") == 1111


def test_orchestrator_limit():
    with env(AGL_ORCHESTRATOR_LIMIT="33"):
        m = _reload("Core_Engines.orchestrator")
        assert getattr(m, "_AGL_ORCHESTRATOR_LIMIT") == 33


def test_gk_reasoner_preview_chars():
    with env(AGL_GK_SUBJECT_PREVIEW_CHARS="42"):
        m = _reload("Core_Engines.GK_reasoner")
        assert getattr(m, "_AGL_GK_SUBJECT_PREVIEW_CHARS") == 42
