# tests/test_phase4_multi_step_qa.py

import pytest
from Self_Improvement.Knowledge_Graph import agl_pipeline

QUESTION = "اشرح ارتفاع ضغط الدم من حيث: التعريف، الأسباب، المضاعفات، طرق الوقاية."


def test_phase4_multi_step_task_type():
    """يتأكد أن النظام يتعرّف على السؤال كسؤال متعدد المحاور (qa_multi)."""
    result = agl_pipeline(QUESTION)

    assert isinstance(result, dict)
    # في بعض الإصدارات قد لا يرجع task_type في القاموس الخارجي، فنتحمل الاحتمالين
    task_type = result.get("task_type") or result.get("provenance", {}).get("task_type")
    assert task_type == "qa_multi"


def test_phase4_multi_step_has_sub_answers():
    """يتأكد من وجود خطوات فرعية sub_answers وأكثر من خطوة واحدة."""
    result = agl_pipeline(QUESTION)

    sub_answers = result.get("sub_answers")
    assert isinstance(sub_answers, list), "من المتوقع أن يكون sub_answers قائمة."
    assert len(sub_answers) >= 2, "من المتوقع وجود خطوتين فرعيتين على الأقل."

    # تأكد أن كل عنصر يحتوي على step و answer غير فارغين
    for item in sub_answers:
        assert "step" in item
        assert isinstance(item["step"], str)
        assert item["step"].strip() != ""

        assert "answer" in item
        assert isinstance(item["answer"], str)
        assert item["answer"].strip() != ""


def test_phase4_multi_step_final_answer_shape():
    """يتأكد من أن answer النهائي مركّب ويحتوي على ترقيم للخطوات."""
    result = agl_pipeline(QUESTION)

    final_answer = result.get("answer")
    assert isinstance(final_answer, str)

    # يجب أن يحتوي على الحد الأدنى من الشكل المتوقع: 1. / 2. / 3. ...
    assert "1." in final_answer or "١." in final_answer
    assert "2." in final_answer or "٢." in final_answer

    # provenance خاص بالمحرك الجديد
    prov = result.get("provenance", {})
    assert prov.get("engine") == "multi_step_qa_v1"
    steps = prov.get("steps")
    assert isinstance(steps, list)
    assert len(steps) >= 2

# هذا الاختبار لا يهتم بصحّة المحتوى الطبي، فقط بالشكل والـ provenance
