import os


def test_unified_cognitive_bus_smoke():
    # Ensure mock LLMs are used for CI-friendly deterministic runs
    os.environ["AGL_FEATURE_ENABLE_RAG"] = "1"
    os.environ["AGL_OLLAMA_KB_MOCK"] = "1"
    os.environ["AGL_EXTERNAL_INFO_MOCK"] = "1"

    from Integration_Layer.integration_registry import registry
    from Core_Engines import bootstrap_register_all_engines

    # Ensure a fresh registry instance so test is hermetic when run repeatedly
    from Integration_Layer import integration_registry as _ir
    _ir._internal_registry = _ir.IntegrationRegistry()

    # Register engines (allow_optional to skip heavy deps)
    registered = bootstrap_register_all_engines(registry, allow_optional=True, verbose=False)

    # Basic required engines for the cognitive bus
    assert "CAUSAL_GRAPH" in registered
    assert "HYPOTHESIS_GENERATOR" in registered

    from Integration_Layer.orchestrator import run_causal_and_hypothesis

    text = "ارتفاع الضغط الجوي يؤدي إلى تغير أنماط الرياح."
    res = run_causal_and_hypothesis(registry, text=text)

    assert res["ok"] is True
    edges = res["bundle"]["causal"]["edges"]
    hyps = res["bundle"]["hypotheses"]["hypotheses"]

    assert isinstance(edges, list)
    assert isinstance(hyps, list)
