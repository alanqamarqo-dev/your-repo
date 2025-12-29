import os
import json

from Self_Improvement.projects import (
    create_project,
    add_task,
    run_next_task,
    PROJECTS_DIR,
    ProjectStore,
)


def test_phase8_project_lifecycle(tmp_path, monkeypatch):
    # نجعل الـ projects تُخزن في مجلد مؤقت للاختبار
    monkeypatch.setattr("Self_Improvement.projects.PROJECTS_DIR", str(tmp_path))

    project_id = "drug_smuggling_research"
    goal = "إدارة مشروع بحث تهريب الأدوية"

    # 1) إنشاء مشروع
    project = create_project(project_id, goal)
    assert project.id == project_id
    assert project.goal == goal
    assert project.tasks == []

    # 2) إضافة مهمتين
    project = add_task(project_id, "t1", "جمع المحاور الرئيسية للبحث")
    project = add_task(project_id, "t2", "صياغة مشكلة البحث وأسئلته")

    assert len(project.tasks) == 2
    assert project.tasks[0].status == "pending"
    assert project.tasks[1].status == "pending"

    # 3) تشغيل run_next_task مرتين
    project = run_next_task(project_id)
    assert project.tasks[0].status == "done"
    assert project.tasks[1].status == "pending"

    project = run_next_task(project_id)
    assert project.tasks[0].status == "done"
    assert project.tasks[1].status == "done"

    # 4) التأكد من أن المشروع محفوظ فعليًا في ملف JSON
    store = ProjectStore()
    loaded = store.load(project_id)
    assert loaded is not None
    assert len(loaded.tasks) == 2
    assert all(t.status == "done" for t in loaded.tasks)
    assert len(loaded.history) >= 2
