# tests/test_phase11_executive_agent.py
import os
from pathlib import Path

from Self_Improvement import Knowledge_Graph


def test_executive_runs_highest_priority(monkeypatch, tmp_path):
    """
    المرحلة 11: التأكد من أن العقل التنفيذي:
    - يقرأ الطابور من ملف JSONL مؤقت
    - يختار أعلى أولوية (pending)
    - يستدعي agl_pipeline
    - يحدّث حالة المهمة إلى done ويكتب result_summary
    """

    # نوجّه الطابور إلى ملف مؤقت للاختبار فقط
    queue_path = tmp_path / "task_queue.jsonl"
    monkeypatch.setenv("AGL_TASK_QUEUE_PATH", str(queue_path))

    # إعادة استيراد الموديول بعد ضبط متغير البيئة
    from Self_Improvement import executive_agent

    # نستخدم agl_pipeline مزيف لتسريع الاختبار والتحكم بالنتيجة
    calls = {}

    def fake_agl_pipeline(question: str):
        calls["last_question"] = question
        return {"answer": f"ANSWER_FOR: {question}"}

    monkeypatch.setattr(Knowledge_Graph, "agl_pipeline", fake_agl_pipeline)

    # نتأكد من عدم وجود طابور سابق
    if queue_path.exists():
        queue_path.unlink()

    # نضيف مهمتين: واحدة أولوية منخفضة، وأخرى عالية
    executive_agent.enqueue_task(
        project_id="proj1",
        task_id="t_low",
        description="مهمة منخفضة الأولوية",
        priority=0.2,
        path=queue_path,
    )
    executive_agent.enqueue_task(
        project_id="proj1",
        task_id="t_high",
        description="مهمة عالية الأولوية",
        priority=0.9,
        path=queue_path,
    )

    # تشغيل دورة تنفيذية واحدة
    executed = executive_agent.run_executive_once(
        max_tasks=1,
        queue_path=queue_path,
    )

    assert executed == 1

    # قراءة الطابور بعد التنفيذ
    tasks = executive_agent.load_task_queue(queue_path)

    # نتأكد أن المهمة ذات الأولوية العالية أصبحت done
    high = next(t for t in tasks if t.task_id == "t_high")
    low = next(t for t in tasks if t.task_id == "t_low")

    assert high.status == "done"
    assert low.status == "pending"
    assert high.result_summary is not None
    assert high.result_summary.startswith("ANSWER_FOR:")

    # نتأكد أن السؤال المرسل لـ agl_pipeline يحتوي على رقم المشروع
    assert "proj1" in calls["last_question"]


def test_executive_no_pending_tasks(monkeypatch, tmp_path):
    """
    إذا لم توجد مهام pending يجب أن ترجع run_executive_once صفرًا
    ولا تغيّر شيء.
    """
    queue_path = tmp_path / "task_queue.jsonl"
    monkeypatch.setenv("AGL_TASK_QUEUE_PATH", str(queue_path))

    from Self_Improvement import executive_agent

    # إنشاء طابور يحوي مهام منتهية فقط
    tasks = [
        executive_agent.TaskItem(
            project_id="proj1",
            task_id="done1",
            description="منتهية",
            priority=0.5,
            status="done",
            result_summary="ok",
        )
    ]
    executive_agent.save_task_queue(tasks, queue_path)

    executed = executive_agent.run_executive_once(
        max_tasks=1,
        queue_path=queue_path,
    )

    assert executed == 0

    # نتحقق أن الحالة لم تتغير
    tasks_after = executive_agent.load_task_queue(queue_path)
    assert tasks_after[0].status == "done"
