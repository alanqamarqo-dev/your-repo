import pytest


def test_agl_bootstrap_registry():
    from AGL import AGL

    agl = AGL(config={
        "enable_self_improvement": True,
        "enable_quantum_neural_core": False,
        "enable_advanced_exponential_algebra": False,
        "enable_emergency_experts": True,
    })

    # التأكد من تسجيل الخدمات الأساسية
    for k in ("communication_bus", "task_orchestrator", "output_formatter"):
        assert agl.integration_registry.has(k), f"Missing service: {k}"

    # التأكد من خدمات إضافية (factories should exist)
    for k in ("domain_router", "retriever", "rag", "intent_recognizer"):
        assert agl.integration_registry.has(k), f"Missing factory/service: {k}"

    # التأكد من محرك بصري
    v = agl.core_engines.get("visual_spatial")
    assert v is not None

    # تجربة resolve (سيؤدي إلى إنشاء فوري من factory)
    router = agl.integration_registry.resolve("domain_router")
    assert router is not None

    # self-improvement registrations
    assert agl.integration_registry.has("experience_memory")
    assert agl.integration_registry.has("self_learning")

    # safety core
    assert agl.integration_registry.has("emergency_protocols")
    assert agl.integration_registry.has("control_layers")
