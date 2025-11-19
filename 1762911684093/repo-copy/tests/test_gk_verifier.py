import os
import importlib
import contextlib
import sys
from types import SimpleNamespace

@contextlib.contextmanager
def env(**kw):
    old = {k: os.environ.get(k) for k in kw}
    try:
        for k, v in kw.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = str(v)
        yield
    finally:
        for k, v in old.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def import_fresh(module_name: str):
    if module_name in sys.modules:
        del sys.modules[module_name]
    importlib.invalidate_caches()
    return importlib.import_module(module_name)


def test_import_default_ok():
    with env(AGL_VERIFIER_EVIDENCE_LIMIT=None):
        mod = import_fresh("Core_Engines.GK_verifier")
        limit = getattr(mod, "_AGL_VERIFIER_EVIDENCE_LIMIT", None)
        assert limit is not None and isinstance(limit, int)


def test_env_override_changes_limit():
    with env(AGL_VERIFIER_EVIDENCE_LIMIT="7"):
        mod = import_fresh("Core_Engines.GK_verifier")
        limit = getattr(mod, "_AGL_VERIFIER_EVIDENCE_LIMIT", None)
        assert limit == 7


def test_scoring_and_check_basic():
    # use simple namespace objects so attributes can be attached
    with env(AGL_VERIFIER_EVIDENCE_LIMIT=None):
        mod = import_fresh("Core_Engines.GK_verifier")
        GKVerifier = getattr(mod, "GKVerifier")
        v = GKVerifier()

        facts = [
            SimpleNamespace(text="fact A", score=0.9),
            SimpleNamespace(text="fact B", score=0.6),
            SimpleNamespace(text="fact C", score=0.2),
            SimpleNamespace(text="fact D", score=0.8),
        ]
        out = v.score_and_check(facts)
        # should return a list of objects and attach computed_score
        assert isinstance(out, list)
        assert len(out) == len(facts)
        assert all(hasattr(e, "computed_score") for e in out)


def test_evidence_limit_applied():
    with env(AGL_VERIFIER_EVIDENCE_LIMIT="2"):
        mod = import_fresh("Core_Engines.GK_verifier")
        GKVerifier = getattr(mod, "GKVerifier")
        v = GKVerifier()

        facts = [
            SimpleNamespace(text="f1", score=0.95),
            SimpleNamespace(text="f2", score=0.90),
            SimpleNamespace(text="f3", score=0.85),
        ]
        out = v.score_and_check(facts)
        # should not score more than the configured limit
        assert len(out) <= 2
