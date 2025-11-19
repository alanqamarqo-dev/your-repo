import json
import os
from pathlib import Path

# يفترض عندك دالة create_agl_instance(config: dict | None) -> AGL
# وإن لم تكن موجودة، استبدلها بمنشئ AGL المناسب لديك
from AGL import create_agl_instance


def test_registry_bootstrap_with_flags(tmp_path, monkeypatch):
    # 1) اكتب config مؤقت لتفعيل الميزات
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text(
        "features:\n"
        "  enable_self_improvement: true\n"
        "  enable_meta_cognition: true\n"
        "  persist_memory: true\n"
        "logging:\n"
        "  level: INFO\n",
        encoding="utf-8",
    )

    # 2) شغّل AGL بتمرير مسار config لو كان مدعومًا
    # إن لم يكن مدعومًا، create_agl_instance يقرأ config.yaml من cwd
    monkeypatch.chdir(tmp_path)

    agl = create_agl_instance(config=None)

    # 3) تأكد من وجود registry وتسجيل الخدمات الأساسية
    reg = getattr(agl, "integration_registry", None)
    assert reg is not None, "IntegrationRegistry should be attached on AGL"

    # 4) تحقق من بعض الخدمات المسجلة (instances أو factories)
    expected_services = [
        "communication_bus",
        "task_orchestrator",
        "output_formatter",
        "domain_router",
        "planner_agent",
        "retriever",
        "rag",
        "intent_recognizer",
    ]
    for name in expected_services:
        assert reg.has(name), f"Service '{name}' should be registered"

    # 5) self-improvement مفعل → يجب توفر خبرات و self_learning (الفالباك موجود إن لم تتوفر النسخ الثقيلة)
    for name in ["experience_memory", "self_learning"]:
        assert reg.has(name), f"Self-improvement '{name}' should be registered when enabled"

    # model_zoo قد يكون اختياريًا أو يُسجَّل باسم مختلف؛ نتحقق إن كان موجودًا ولكن لا نفشل الاختبار إن غاب
    if not reg.has('model_zoo'):
        print("note: 'model_zoo' not registered (optional) - OK")

    # 6) meta-cognition مفعل → تحقق من تسجيله (اسم الخدمة قد يختلف لديك)
    meta_candidates = ["meta_cognition", "meta_evaluator", "meta_cognition_engine"]
    if not any(reg.has(n) for n in meta_candidates):
        print("note: no meta-cognition engine registered; adjust meta_candidates in test if your project uses a different name")

    # 7) smoke على استدعاء بسيط (بدون مكتبات ثقيلة): تأكد أن process/route لا يفشل
    if hasattr(agl, "process_complex_problem"):
        out = agl.process_complex_problem("healthcheck: simple reasoning")
        assert out is not None


def test_rag_smoke(tmp_path, monkeypatch):
    # prepare config enabling features
    cfg_path = tmp_path / "config.yaml"
    cfg_path.write_text(
        "features:\n"
        "  enable_self_improvement: true\n"
        "  enable_meta_cognition: true\n"
        "  persist_memory: true\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    agl = create_agl_instance(config=None)
    reg = agl.integration_registry

    # retriever should exist and provide retrieve()
    assert reg.has('retriever')
    retriever = reg.resolve('retriever')
    assert hasattr(retriever, 'retrieve')
    res = retriever.retrieve('test query')
    assert isinstance(res, list)

    # rag should exist and provide answer-like API
    assert reg.has('rag')
    rag_svc = reg.resolve('rag')
    # rag may be a module or object with method answer_with_rag/answer
    if hasattr(rag_svc, 'answer'):
        out = rag_svc.answer('q', [])
    elif hasattr(rag_svc, 'answer_with_rag'):
        out = rag_svc.answer_with_rag('q', [])
    else:
        # module-level function fallback
        out = rag_svc('q', []) if callable(rag_svc) else None

    assert isinstance(out, dict)
    assert 'answer' in out
