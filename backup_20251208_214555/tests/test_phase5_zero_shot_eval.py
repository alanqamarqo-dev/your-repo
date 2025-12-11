# tests/test_phase5_zero_shot_eval.py

import os
import json
from pathlib import Path

from tools import zero_shot_qa_eval


def test_phase5_zero_shot_eval_fast_mode(monkeypatch):
    """
    اختبار المرحلة الخامسة:
    - تفعيل FAST_MODE
    - تشغيل سكربت البنشمارك
    - التأكد أن:
      * ملف النتائج تم إنشاؤه
      * فيه نتائج لكل الأسئلة
      * المتوسط الكلي >= 0.5 (هنا متوقع ~0.92 في FAST_MODE)
    """

    # تفعيل وضع الاختبارات السريع داخل هذا الاختبار فقط
    monkeypatch.setenv("AGL_FAST_MODE", "1")

    # تشغيل البنشمارك (سيطبع في stdout وهذا عادي)
    zero_shot_qa_eval.main()

    # التحقق من وجود ملف النتائج
    out_path = Path(zero_shot_qa_eval.OUT_PATH)
    assert out_path.exists(), f"ملف النتائج غير موجود: {out_path}"

    # تحميل النتائج
    data = json.loads(out_path.read_text(encoding="utf-8"))

    # تأكد أن الحقول الأساسية موجودة
    assert "overall_avg_score" in data, "لا يوجد overall_avg_score في ملف النتائج."
    assert "results" in data, "لا يوجد حقل results في ملف النتائج."

    overall = data["overall_avg_score"]
    results = data["results"]

    # لازم يكون عندنا على الأقل 5 أسئلة (الخمس الطبية الأساسية)
    assert len(results) >= 5, f"عدد النتائج أقل من المتوقع: {len(results)}."

    # في FAST_MODE نتوقع أداء عالي؛ نخلي العتبة 0.5 كحد أدنى
    assert overall >= 0.5, f"متوسط الأداء أقل من الحد الأدنى المتوقع في FAST_MODE: {overall}"
