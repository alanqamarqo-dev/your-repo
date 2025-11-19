import os


def test_self_learning_event_logging(tmp_path, monkeypatch):
    # تفعيل التسجيل إلى مجلد مؤقّت
    logdir = tmp_path / "run"
    monkeypatch.setenv("AGL_SELF_LEARNING_ENABLE", "1")
    monkeypatch.setenv("AGL_SELF_LEARNING_MODE", "offline")
    monkeypatch.setenv("AGL_SELF_LEARNING_LOGDIR", str(logdir))

    # import بعد تفعيل المتغيرات لضمان كتابة module_loaded
    from Self_Improvement import Self_Improvement_Engine as SIE
    # reload to ensure module-level logger picks up the monkeypatched env
    import importlib
    importlib.reload(SIE)
    mgr = SIE.SelfLearningManager()

    # توليد أحداث
    mgr.record("unit/demo", 0.5, note="pytest")
    mgr.improve({"q": "demo", "expect": ["ok"]})

    # التحقق من وجود الملف ومحتواه
    fp = logdir / "events.jsonl"
    assert fp.exists(), "events.jsonl not created"

    lines = fp.read_text(encoding="utf-8").strip().splitlines()
    assert any('"module_loaded"' in ln for ln in lines)
    assert any('"record"' in ln for ln in lines)
    assert any('"improve"' in ln for ln in lines)

    # تشغيل دورة تدريب قصيرة باستخدام الواجهة المُوسعة إن وُجدت
    try:
        res = mgr.run_training_epoch()
    except Exception:
        res = None

    # إذا كانت الخاصية مفعّلة فنتوقع نتيجة OK ووجود ملفات ناتجة
    if os.getenv("AGL_SELF_LEARNING_ENABLE", "0") == "1":
        assert res is not None and res.get("ok") is True

        from pathlib import Path
        import json

        runs = Path("artifacts") / "self_runs"
        assert runs.exists() and any(runs.iterdir()), "no snapshot written"

        lc = Path("artifacts") / "learning_curve.json"
        assert lc.exists(), "learning_curve.json missing"
        with lc.open("r", encoding="utf-8") as f:
            curve = json.load(f)
        assert isinstance(curve, list) and len(curve) >= 1
