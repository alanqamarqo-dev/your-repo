import os, time
from pathlib import Path


def test_state_logger_bridge_and_metrics(tmp_path, monkeypatch):
    # تفعيل الميزات
    monkeypatch.setenv("AGL_C_LAYER_SNAPSHOTS", "1")
    monkeypatch.setenv("AGL_C_LAYER_BRIDGE_WRITE", "1")
    monkeypatch.setenv("AGL_SANITIZE_SNAPSHOTS", "1")
    monkeypatch.setenv("AGL_SNAPSHOT_ASYNC", "1")
    monkeypatch.setenv("AGL_SNAPSHOT_QUEUE_MAX", "8")
    monkeypatch.setenv("AGL_SNAPSHOT_RETENTION_DAYS", "0")  # تعطيل الحذف في الاختبار
    monkeypatch.setenv("AGL_SNAPSHOT_COMPRESS_OLD", "0")
    monkeypatch.setenv("AGL_SNAPSHOT_ROTATE_STRATEGY", "count")

    # إعادة توجيه artifacts إلى tmp
    monkeypatch.setenv("AGL_ARTIFACTS_DIR", str(tmp_path))

    # استيراد
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # repo-copy
    from Core_Memory.bridge_singleton import get_bridge
    from Core.C_Layer.state_logger import StateLogger

    bridge = get_bridge()
    s = StateLogger()
    before_count = len(bridge.ltm)

    # نكتب عدة لقطات (مع تنظيف تلقائي للحسّاس)
    for i in range(20):
        s.snapshot({"i": i, "token": "SECRET"}, tags={"scenario": "test"})

    # انتظر تفريغ خيط الكتابة غير المتزامن
    time.sleep(1.5)

    after_count = len(bridge.ltm)
    assert after_count > before_count, "لم تُدفع اللقطات إلى الذاكرة LTM"

    # تأكد أن snapshot files كُتبت
    snaps_dir = Path(tmp_path, "state", "snapshots")
    assert snaps_dir.exists()
    assert any(p.suffix in [".json", ".jsonl", ".gz"] for p in snaps_dir.iterdir())

    # تأكد من وجود metrics
    metrics = Path(tmp_path, "state", "metrics.jsonl")
    assert metrics.exists()
    with metrics.open("r", encoding="utf-8") as f:
        content = f.read()
    assert '"snapshots_written"' in content
