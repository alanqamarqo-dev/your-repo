import os
import types
import importlib

import pytest


@pytest.fixture(autouse=True)
def env_enabler(monkeypatch):
    # نفعّل RAG ونوقف أي مزوّد خارجي حقيقي
    monkeypatch.setenv("AGL_FEATURE_ENABLE_RAG", "1")
    monkeypatch.delenv("AGL_OLLAMA_KB_MOCK", raising=False)
    monkeypatch.delenv("AGL_EXTERNAL_INFO_MOCK", raising=False)
    # نجبر المزود ليكون غير متاح حتى يتجه المسار لـ mock-engine داخل الاختبار
    monkeypatch.delenv("AGL_LLM_BASEURL", raising=False)
    monkeypatch.delenv("AGL_LLM_MODEL", raising=False)
    yield


def test_rag_answer_uses_hybrid_composer(monkeypatch):
    """
    يثبت أن rag_wrapper.rag_answer يستدعي Integration_Layer.Hybrid_Composer.build_prompt_context
    عبر مراقبة (monkeypatch) للدالة واستدعائها مرة واحدة على الأقل.
    """

    # 1) نعدّ module وهمي لـ Integration_Layer.Hybrid_Composer
    fake_comp_module = types.SimpleNamespace()
    call_log = {"called": 0, "args": None, "kwargs": None}

    def fake_build_prompt_context(story, questions):
        call_log["called"] += 1
        call_log["args"] = (story, questions)
        call_log["kwargs"] = {}
        # نعيد system + user بشكل بسيط
        return [
            {"role": "system", "content": f"[SYS] {story or ''}".strip()},
            {"role": "user",   "content": f"[USR] {questions[0] if questions else ''}".strip()}
        ]

    fake_comp_module.build_prompt_context = fake_build_prompt_context

    # 2) نحقن المسار: Integration_Layer.Hybrid_Composer
    monkeypatch.setitem(
        importlib.sys.modules,
        "Integration_Layer.Hybrid_Composer",
        fake_comp_module
    )

    # 3) الآن نستورد rag_wrapper بعد الحقن
    #    مهم: لو كان مستورداً مسبقاً في جلسة pytest، أعِد تحميله لضمان استخدام الـ fake
    if "Integration_Layer.rag_wrapper" in importlib.sys.modules:
        importlib.reload(importlib.import_module("Integration_Layer.rag_wrapper"))
    rag_wrapper = importlib.import_module("Integration_Layer.rag_wrapper")

    # 4) ننفذ rag_answer
    result = rag_wrapper.rag_answer(
        query="اشرح مفهوم التماثل ديناميكياً",
        context="نص قصة/سياق مختصر"
    )

    # 5) تحقق: تم استدعاء الـ composer مرة واحدة على الأقل
    assert call_log["called"] >= 1, "Hybrid_Composer.build_prompt_context لم يُستدعَ."
    # تحقق: النتيجة تعيد هيكل متوقع (محرك محدد حتى لو كان noop/mock)
    assert isinstance(result, dict)
    assert "answer" in result and "engine" in result
    # جواب قد يكون فارغاً إذا لم يوجد مزود حقيقي ولم تكن mock flags مفعلة؛
    # هدف الاختبار هنا هو التحقق من استدعاء الـcomposer، لا محتوى LLM.
