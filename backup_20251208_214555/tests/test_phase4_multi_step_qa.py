import os
import pytest

from Self_Improvement.Knowledge_Graph import agl_pipeline, infer_task_type


@pytest.mark.phase4
def test_infer_task_type_multi():
    q = "اشرح ارتفاع ضغط الدم من حيث: التعريف، الأسباب، المضاعفات، طرق الوقاية."
    t = infer_task_type(q)
    assert t == "qa_multi"


@pytest.mark.phase4
def test_multi_step_qa_pipeline_runs():
    # إعداد المتغيرات البيئية الأساسية (لو تحتاجها لتحميل المحركات)
    os.environ.setdefault("AGL_ENGINES", "hosted_llm,planner,timeline,deliberation,motivation")
    os.environ.setdefault("AGL_ENGINE_TIMEOUT", "120")
    os.environ.setdefault("AGL_GENERATIVE_LINK", "0")

    question = "اشرح ارتفاع ضغط الدم من حيث: التعريف، الأسباب، المضاعفات، طرق الوقاية."

    result = agl_pipeline(question)

    # يجب أن يحتوي على answer
    assert "answer" in result
    answer = result["answer"]
    assert isinstance(answer, str)
    assert len(answer) > 50  # على الأقل نص معقول الطول

    # نتأكد أن الجواب فيه أكثر من نقطة (1. 2. ...)
    assert "1." in answer or "١." in answer

    # ونتأكد أن المرحلة موسومة كـ qa_multi
    assert result.get("task_type") == "qa_multi"


if __name__ == "__main__":
    pytest.main(["-q", __file__])
