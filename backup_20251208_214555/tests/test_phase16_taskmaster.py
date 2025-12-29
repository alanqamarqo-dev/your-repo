import os
from pathlib import Path
from datetime import datetime

from Self_Improvement.taskmaster import (
    start_long_term_project,
    run_taskmaster_tick,
    load_long_term_configs,
    LONG_TERM_PROJECTS_PATH,
)
from Self_Improvement.projects import ProjectStore


def test_phase16_start_long_term_project_creates_config(tmp_path, monkeypatch):
    artifacts_dir = tmp_path / "artifacts"
    monkeypatch.setenv("AGL_ARTIFACTS_DIR", str(artifacts_dir))

    # reload module after env change
    import importlib
    from Self_Improvement import taskmaster as tm
    importlib.reload(tm)

    store = ProjectStore()
    cfg = tm.start_long_term_project(
        goal="إعداد بحث عن تهريب الأدوية في مأرب",
        horizon_days=10,
        daily_task_budget=2,
        store=store,
    )
    assert cfg.project_id
    assert cfg.goal.startswith("إعداد بحث")
    assert tm.LONG_TERM_PROJECTS_PATH.exists()

    cfgs = tm.load_long_term_configs()
    assert len(cfgs) == 1
    loaded = cfgs[0]
    assert loaded.project_id == cfg.project_id
    assert loaded.daily_task_budget == 2
    assert loaded.active is True


def test_phase16_run_taskmaster_tick_calls_executive(tmp_path, monkeypatch):
    artifacts_dir = tmp_path / "artifacts"
    monkeypatch.setenv("AGL_ARTIFACTS_DIR", str(artifacts_dir))

    import importlib
    from Self_Improvement import taskmaster as tm
    importlib.reload(tm)

    # use real project store
    store = ProjectStore()
    cfg = tm.start_long_term_project(
        goal="مشروع اختبار طويل الأمد",
        horizon_days=3,
        daily_task_budget=1,
        store=store,
    )

    now = datetime.utcnow()

    calls = {"count": 0}

    def fake_run_executive_once(max_tasks=1):
        calls["count"] += 1
        return 0

    monkeypatch.setattr(tm, "run_executive_once", fake_run_executive_once)

    ticks = tm.run_taskmaster_tick(store=store, max_projects=1, now=now)
    assert ticks == 1
    assert calls["count"] == 1

    cfgs = tm.load_long_term_configs()
    assert len(cfgs) == 1
    updated = cfgs[0]
    assert updated.total_ticks == 1
    assert updated.last_tick_ts is not None

    # running again with same now should not tick
    calls["count"] = 0
    ticks2 = tm.run_taskmaster_tick(store=store, max_projects=1, now=now)
    assert ticks2 == 0
    assert calls["count"] == 0
