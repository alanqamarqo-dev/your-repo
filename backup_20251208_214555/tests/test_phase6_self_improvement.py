import json
import os

from tools.analyze_qa_failures import main as analyze_main


def test_phase6_analyze_creates_patches(tmp_path, monkeypatch):
    # تجهيز ملف ذاكرة تجريبي
    mem_path = tmp_path / "memory.jsonl"
    rows = [
        {
            "id": "htn_causes",
            "question": "ما هي الأسباب الشائعة لارتفاع ضغط الدم؟",
            "answer": "جواب ناقص بدون ذكر الملح أو قلة النشاط.",
            "hits": ["السمنة"],
            "missing": ["الملح", "قلة النشاط"],
            "score": 0.4,
            "ts": 123.0,
        }
    ]
    with mem_path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    patches_path = tmp_path / "prompt_patches.json"

    # نوجّه السكربت ليستخدم مسارات مؤقتة
    monkeypatch.setenv("AGL_COLLECTIVE_MEMORY_PATH", str(mem_path))
    monkeypatch.setenv("AGL_PROMPT_PATCHES_PATH", str(patches_path))

    patches = analyze_main()

    assert patches_path.exists(), "ملف التصحيحات لم يتم إنشاؤه."
    assert isinstance(patches, dict) and patches, "لم يتم إنتاج أي باتش."

    # نتأكد أن الكلمات المفقودة ظهرت داخل الـ extra_instruction
    key = list(patches.keys())[0]
    extra = patches[key].get("extra_instruction", "")
    assert "الملح" in extra
    assert "قلة النشاط" in extra
