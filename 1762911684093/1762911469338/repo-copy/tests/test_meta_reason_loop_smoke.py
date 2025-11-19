import os
import pytest


def test_meta_self_improve_smoke():
    # تفعيل الموك عند غياب مزود LLM
    os.environ.setdefault("AGL_EXTERNAL_INFO_MOCK", "1")

    from Core_Engines import bootstrap_register_all_engines
    # استورد registry الذي أضفتَه كسينجلتون في Integration_Layer
    from Integration_Layer.integration_registry import registry

    registered = bootstrap_register_all_engines(registry, allow_optional=True, verbose=False)
    assert "Meta_Learning" in registered and "AdvancedMetaReasoner" in registered

    from Core_Engines.orchestrator import run_meta_self_improve
    text = "إذا زادت درجة الحرارة فقد يزداد الضغط، وهذا يؤدي إلى تمدد الغاز."
    out = run_meta_self_improve(registry, text)
    assert out.get("ok") is True
    assert isinstance(out.get("meta", {}).get("ranked_hypotheses", []), list)
    assert "plan" in out.get("amr", {})
