import os
from pathlib import Path

from Self_Improvement.strategic_memory import StrategicMemory
from Self_Improvement.Knowledge_Graph import agl_pipeline


def test_phase10_memory_record_and_recall(tmp_path, monkeypatch):
    """ اختبار أساسي: - استخدام ملف ذاكرة مؤقت. - تسجيل نتيجتين في نفس الدومين (طبي). - استرجاع ذاكرة مرتبطة والتحقق من وجودها. """
    mem_path = tmp_path / "strategic_memory_test.jsonl"

    # نستخدم نسخة مخصّصة عبر monkeypatch للـ default()
    def _fake_default():
        return StrategicMemory(path=mem_path)

    monkeypatch.setattr("Self_Improvement.strategic_memory.StrategicMemory.default", staticmethod(_fake_default))

    sm = StrategicMemory.default()
    sm.record_outcome(
        title="ما هي أعراض الإنفلونزا؟",
        task_type="qa_single",
        score=0.8,
        success=True,
        meta={"test_case": "flu"},
        strategy={"use_deep_cot": False},
    )
    sm.record_outcome(
        title="اشرح ارتفاع ضغط الدم من حيث: التعريف، الأسباب، المضاعفات، طرق الوقاية.",
        task_type="qa_multi",
        score=0.7,
        success=True,
        meta={"test_case": "htn"},
        strategy={"use_deep_cot": True},
    )

    # استرجاع
    domain = sm.infer_domain("qa_single", "اشرح ارتفاع ضغط الدم من حيث: التعريف، الأسباب، المضاعفات، طرق الوقاية.")
    related = sm.recall_relevant(
        title="اشرح ارتفاع ضغط الدم من حيث: التعريف، الأسباب، المضاعفات، طرق الوقاية.",
        domain=domain,
        task_type="qa_multi",
        k=5,
    )
    assert len(related) >= 1
    titles = [it.task_title for it in related]
    assert any("ضغط الدم" in t or "الإنفلونزا" in t or "أعراض" in t for t in titles)


def test_phase10_agl_pipeline_uses_strategic_memory(tmp_path, monkeypatch):
    """ اختبار تكامل: - تشغيل agl_pipeline في وضع FAST_MODE. - التأكد أن: * provenance.runtime_context يحتوي على strategy.domain. * ملف الذاكرة تمت الكتابة إليه. """
    os.environ["AGL_FAST_MODE"] = "1"
    mem_path = tmp_path / "strategic_memory_test2.jsonl"

    def _fake_default():
        return StrategicMemory(path=mem_path)

    monkeypatch.setattr("Self_Improvement.strategic_memory.StrategicMemory.default", staticmethod(_fake_default))

    q = "ما هي أضرار استخدام المضادات الحيوية بدون وصفة طبية؟"
    result = agl_pipeline(q)
    prov = result.get("provenance") or {}
    ctx = prov.get("runtime_context") or {}
    strategy = ctx.get("strategy") or {}
    assert strategy
    # لسؤال طبي نتوقع دومين medical
    assert strategy["domain"].startswith("medical")
    # تأكد أن الملف تم إنشاؤه فعلاً
    assert mem_path.exists()
    content = mem_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(content) >= 1
