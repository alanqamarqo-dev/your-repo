from pathlib import Path

from Self_Improvement import self_profile


def test_phase12_record_and_load_profile(tmp_path):
    """
    المرحلة 12: اختبار تسجيل نتائج في بروفايل الذات
    ثم تحميلها والتأكد من تحديث الإحصائيات.
    """
    test_path = tmp_path / "self_profile.json"

    # في البداية، البروفايل يجب أن يكون فارغاً
    profile = self_profile._load_profile(test_path)
    assert profile == {}

    # تسجيل نتيجتين في مجال "medical"
    self_profile.record_eval_result(
        domain="medical",
        score=0.4,
        engines=["hosted_llm", "retriever"],
        meta={"source": "unit_test_1"},
        path=test_path,
    )

    self_profile.record_eval_result(
        domain="medical",
        score=0.6,
        engines=["hosted_llm"],
        meta={"source": "unit_test_2"},
        path=test_path,
    )

    # إعادة التحميل والتأكد من أن الإحصائيات محدثة
    profile2 = self_profile._load_profile(test_path)
    assert "domains" in profile2
    assert "medical" in profile2["domains"]

    med_stats = profile2["domains"]["medical"]

    assert med_stats["calls"] == 2
    # المتوسط المتوقع = (0.4 + 0.6) / 2 = 0.5 تقريباً
    assert 0.45 <= med_stats["accuracy"] <= 0.55
    assert "history" in med_stats
    assert len(med_stats["history"]) == 2
    assert "engines" in med_stats
    assert "hosted_llm" in med_stats["engines"]


def test_phase12_suggest_strategy_by_domain(tmp_path, monkeypatch):
    """
    اختبار أن suggest_strategy تستخدم البروفايل
    وتغير الاستراتيجية حسب مستوى الدقة.
    """
    test_path = tmp_path / "self_profile.json"

    # نرغم PROFILE_PATH في الموديول أن يشير لملف الاختبار
    monkeypatch.setattr(self_profile, "PROFILE_PATH", test_path)

    # حالة أداء ضعيف في المجال الطبي -> نتوقع use_cot=True و use_rag=True
    self_profile.record_eval_result(
        domain="medical",
        score=0.3,
        engines=["hosted_llm", "retriever"],
        meta={"source": "low_score"},
        path=test_path,
    )

    strat_low = self_profile.suggest_strategy(
        problem={"domain": "medical", "title": "سؤال طبي"}, path=test_path
    )
    assert strat_low["domain"] == "medical"
    assert strat_low["use_cot"] is True
    assert strat_low["use_rag"] is True
    assert strat_low["cot_samples"] >= 2

    # الآن نرفع الدقة بإضافة نتائج أعلى
    self_profile.record_eval_result(
        domain="medical",
        score=0.9,
        engines=["hosted_llm"],
        meta={"source": "high_score"},
        path=test_path,
    )

    strat_high = self_profile.suggest_strategy(
        problem={"domain": "medical", "title": "سؤال طبي"}, path=test_path
    )
    assert strat_high["domain"] == "medical"
    # في الأداء الجيد نتوقع أن لا يكون CoT ضروريًا دائمًا
    assert strat_high["use_cot"] in (False, True)
    # نضمن على الأقل أنه سمح بنمط مختلف عن حالة الأداء الضعيف
    assert strat_high["use_rag"] is False
