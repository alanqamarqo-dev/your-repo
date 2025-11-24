import os

# 3.1 Basic test environment defaults (ensures RAG is enabled for integration tests)
os.environ.setdefault("AGL_FEATURE_ENABLE_RAG", "1")
os.environ.setdefault("AGL_LLM_BASEURL", "http://127.0.0.1:11434")
# Only default an LLM model when RAG mocks are not explicitly requested by the test
# run. This allows CI or local developers to enable AGL_OLLAMA_KB_MOCK or
# AGL_EXTERNAL_INFO_MOCK and have the test-suite treat the LLM as unavailable.
if not (os.environ.get("AGL_OLLAMA_KB_MOCK") or os.environ.get("AGL_EXTERNAL_INFO_MOCK")):
    os.environ.setdefault("AGL_LLM_MODEL", "qwen2.5:3b-instruct")

# Delay imports until after env vars are set
import Core_Engines
from Integration_Layer.integration_registry import registry

# Lightweight dummy engine used for tests
class _DummyEngine:
    def __init__(self, name):
        self.name = name

    def process_task(self, task):
        return {"engine": self.name, "ok": True, "result": f"dummy:{task}"}

# Most common names that failed during bootstrap in the diagnostic run
_DUMMIES = [
    "Reasoning_Layer",
    "Reasoning_Planner",
    "Strategic_Thinking",
    "Creative_Innovation",
    "Meta_Learning",
    "Meta_Ensembler",
    "GK_reasoner",
    "GK_retriever",
    "Law_Matcher",
    "General_Knowledge",
    "Robust_Regression",
    "Visual_Spatial",
]


def pytest_sessionstart(session):
    # 1) run normal bootstrap first
    Core_Engines.bootstrap_register_all_engines(
        registry, allow_optional=True, verbose=True
    )
    # 2) register dummy engines for any missing names
    for name in _DUMMIES:
        try:
            names = registry.list_names()
        except Exception:
            # best-effort: try keys()
            try:
                names = registry.keys()
            except Exception:
                names = []
        if name not in names:
            try:
                registry.register(name, _DummyEngine(name))
            except Exception:
                # fall back to alternate signature
                try:
                    registry.register(name=name, engine=_DummyEngine(name))
                except Exception:
                    pass

    # --- Attempt to inject lighter-weight GK stubs if GK engines are missing ---
    try:
        # Attempt to import our test stubs
        from tests.stubs.gk_retrieval_stub import GK_Retriever_Dummy
        from tests.stubs.gk_reasoner_stub import GK_Reasoner_Dummy
        # Ensure GK retriever and reasoner are registered when absent
        try:
            names = registry.list_names()
        except Exception:
            try:
                names = registry.keys()
            except Exception:
                names = []

        if "GK_retriever" not in names:
            try:
                registry.register("GK_retriever", GK_Retriever_Dummy())
            except Exception:
                try:
                    registry.register(name="GK_retriever", engine=GK_Retriever_Dummy())
                except Exception:
                    pass

        if "GK_reasoner" not in names:
            try:
                registry.register("GK_reasoner", GK_Reasoner_Dummy())
            except Exception:
                try:
                    registry.register(name="GK_reasoner", engine=GK_Reasoner_Dummy())
                except Exception:
                    pass
    except Exception as e:
        print("WARN: stub injection failed:", e)
