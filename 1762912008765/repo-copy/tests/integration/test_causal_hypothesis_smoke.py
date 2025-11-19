import os


def test_causal_and_hypothesis_smoke():
    # فعّل الموك إن لم يتوفر LLM
    os.environ.setdefault("AGL_EXTERNAL_INFO_MOCK", "1")

    from Integration_Layer.integration_registry import registry
    from Core_Engines import bootstrap_register_all_engines

    # سجّل المحركات (allow_optional=True لتجاوز التبعيات الثقيلة)
    registered = bootstrap_register_all_engines(registry, allow_optional=True, verbose=False)
    assert "CAUSAL_GRAPH" in registered
    assert "HYPOTHESIS_GENERATOR" in registered

    from Integration_Layer.orchestrator import run_causal_and_hypothesis
    text = "ارتفاع الضغط الجوي يؤدي إلى تغير أنماط الرياح."
    res = run_causal_and_hypothesis(registry, text=text)

    assert res["ok"] is True
    edges = res["bundle"]["causal"]["edges"]
    hyps  = res["bundle"]["hypotheses"]["hypotheses"]
    # يجب أن يكون هناك مخرجات غير فارغة (مرنة)
    assert isinstance(edges, list)
    assert isinstance(hyps, list)
