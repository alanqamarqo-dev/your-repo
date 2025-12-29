# -*- coding: utf-8 -*-
"""
Run a practical, automated pass of the C-AGI Test (heuristic evaluation).

This script:
 - builds a set of prompts (as described by the user)
 - calls `solve_universal` from `agl_universal` to run all engines
 - collects the formatted/returned answer and applies simple keyword checks
 - prints each question followed by the system's answer (Arabic allowed)
 - prints PASS/FAIL per item and a final % score

Note: Evaluation is heuristic (keyword-based) and intended as an automated smoke-test.
Human review is recommended for creative / nuanced items.
"""
import os
import sys
import json
from typing import Any, Dict, List

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
# Load agl_universal from repository root explicitly to avoid shadowing by scripts/agl_universal.py
import importlib.util
agl_path = os.path.join(ROOT, 'agl_universal.py')
spec = importlib.util.spec_from_file_location('project_agl_universal', agl_path)
agl_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(agl_mod)
solve_universal = getattr(agl_mod, 'solve_universal')
build_answer_context = getattr(agl_mod, 'build_answer_context')
DEFAULT_UNIVERSAL_SYSTEM_PROMPT = getattr(agl_mod, 'DEFAULT_UNIVERSAL_SYSTEM_PROMPT')

# import rag_answer from repo Integration_Layer
sys.path.insert(0, ROOT)
from Integration_Layer.rag_wrapper import rag_answer


def call_system(question: str, context: str | None = None) -> Dict[str, Any]:
    problem = {"mode": "qa", "language": "ar", "question": question, "context": context}
    bundle = solve_universal(problem, domains_needed=("language", "analysis", "knowledge"), fanout_all=True)

    # Build context and call rag formatter (best-effort)
    ctx = build_answer_context(problem=problem, collab_result=bundle.get("cie_result", {}), health_snapshot=bundle.get("health"))
    try:
        formatted = rag_answer(question=question, context=ctx, system_prompt=DEFAULT_UNIVERSAL_SYSTEM_PROMPT)
    except TypeError:
        try:
            formatted = rag_answer(question, ctx)
        except Exception as exc:
            formatted = {"_error": "rag_failed", "exc": str(exc)}

    return {"bundle": bundle, "formatted": formatted}


def check_contains_any(text: str, keywords: List[str]) -> bool:
    txt = (text or "").lower()
    for k in keywords:
        if k.lower() in txt:
            return True
    return False


def main():
    tests: List[Dict[str, Any]] = []

    # 1. Abstract reasoning and logic
    tests.append({
        "id": "logic_1",
        "title": "إذا كان A ⇒ B، و B ⇒ C، لكن ¬C، فماذا تستنتج عن A؟",
        "prompt": "إذا كان A ⇒ B، و B ⇒ C، ولكن نعلم أن C خاطئ (¬C). ماذا نستنتج عن A؟ اشرح منطقيًا.",
        "keywords": ["a", "لا يمكن", "غير", "خطأ", "مستنتج", "not", "false"],
    })

    tests.append({
        "id": "logic_2",
        "title": "مفارقة الكذابين",
        "prompt": "حل مفارقة الكذابين: 'هذه الجملة خاطئة' - هل هي صحيحة أم خاطئة؟ فسر بالتفصيل.",
        "keywords": ["مفارقة", "تناقض", "paradox", "self", "ذاتي", "لا يمكن"],
    })

    tests.append({
        "id": "logic_3",
        "title": "تفكير مضاد للواقع - جاذبية",
        "prompt": "ماذا لو كانت الجاذبية تتناسب عكسيًا مع مكعب المسافة وليس مربعها؟ ناقش الآثار الفيزيائية والنتائج المتوقعة.",
        "keywords": ["مكعب", "عكسياً", "مدارات", "مختلف", "قوة", "inverse", "cube"],
    })

    # 2. Emotional / social intelligence (3 mini tests)
    tests.append({
        "id": "emo_1",
        "title": "كشف السخرية",
        "prompt": "حدد إن كانت الجملة التالية ساخرة: 'نعم، لأن كل شيء هنا يسير بشكل ممتاز' (قيل بعد فشل واضح). فسّر السبب.",
        "keywords": ["سخرية", "ساخر", "سخر", "irony", "سخرية"],
    })

    tests.append({
        "id": "emo_2",
        "title": "فهم المشاعر المختلطة",
        "prompt": "اقرأ: 'أنا سعيد لأن المشروع انتهى، لكن قلق بشأن النتائج.' ما المشاعر المتعاقبة؟ فسّر.",
        "keywords": ["سعيد", "قلق", "مزيج", "مختلط", "mixed", "emotions"],
    })

    tests.append({
        "id": "emo_3",
        "title": "حل نزاع بسيط",
        "prompt": "طريقة مقترحة لحل نزاع بين زميلين اختلفا حول تخصيص الميزانية؟ قدم خطوات عملية.",
        "keywords": ["الاستماع", "التعاطف", "تفاوض", "حل وسط", "mediate", "حل"],
    })

    # 3. Creativity
    tests.append({
        "id": "cre_1",
        "title": "قصة بها 3 مفارقات",
        "prompt": "اكتب قصة قصيرة باللغة العربية تحتوي على 3 مفارقات واضحة ومتناقضة.",
        "keywords": ["مفارقة", "مفارقات", "paradox"],
    })

    tests.append({
        "id": "cre_2",
        "title": "اختراع يحل مشكلتين غير مرتبطتين",
        "prompt": "اختر مشكلتين غير مرتبطتين (مثلاً: تلوث الهواء، ونقص المياه) واصنع اختراعًا عمليًا يحل كلاهما.",
        "keywords": ["حل", "مياه", "تلوث", "innov", "اختراع", "اختراع"],
    })

    tests.append({
        "id": "cre_3",
        "title": "نكتة ثقافية",
        "prompt": "اكتب نكتة قصيرة تعتمد على فهم ثقافي عربي مع محاولة الحفاظ على الذوق العام.",
        "keywords": ["نكتة", "مضحك", "نكت"],
    })

    # 4. Learning & adaptation
    tests.append({
        "id": "learn_1",
        "title": "تعلم لغة جديدة من 10 أمثلة",
        "prompt": "تعلم قواعد بسيطة من هذه الأمثلة (10 جمل) واكتب 3 قواعد مستنتجة.\nمثال: (نفرض لغة مصطنعة مع 10 جمل).\n1) 'bla maz' -> ... (ابتكر أمثلة بسيطة)",
        "keywords": ["قواعد", "قواعد مستنتجة", "grammar", "استنتاج"],
    })

    tests.append({
        "id": "learn_2",
        "title": "نقل المعرفة بين مجالات",
        "prompt": "كيف يمكن تطبيق مفهوم من الفيزياء (مثل الحفظ الطاقي) على قرار اقتصادي؟ اشرح نموذجًا واحدًا.",
        "keywords": ["نقل", "تطبيق", "اقتصاد", "فيزياء", "حفظ", "الطاقة"],
    })

    # 5. Wisdom / decision
    tests.append({
        "id": "wise_1",
        "title": "معضلة الترولي متعددة الأبعاد",
        "prompt": "معضلة ترولي مع احتمالات ومخاطر بعيدة المدى - كيف تتخذ القرار؟ قدّم مبدأ مُسَاعِدًا.",
        "keywords": ["مبدأ", "أخلاق", "فائدة", "نتيجة", "utilitarian", "deont"],
    })

    # 6. Self-awareness
    tests.append({
        "id": "self_1",
        "title": "حدود المعرفة والتحيّز",
        "prompt": "صف حدود معرفتك الحالية وكيف تكتشف تحيّزات التفكير لديك وتقترح طريقة للتقليل منها.",
        "keywords": ["حدود", "تحيّز", "تحيز", "استراتيج", "تعلم ذاتي"],
    })

    # 7. Multidisciplinary integration
    tests.append({
        "id": "multi_1",
        "title": "حل استدامة متعدد التخصصات",
        "prompt": "استخدم مفاهيم من البيولوجيا الجزيئية، نظرية المعلومات، الاقتصاد السلوكي، والفلسفة الوجودية لحل مشكلة استدامة عالمية واحدة.",
        "keywords": ["بيولوجيا", "نظرية المعلومات", "اقتصاد", "فلسفة", "استدامة"],
    })

    # 8. Physical/mathematical
    tests.append({
        "id": "phys_1",
        "title": "استنباط قانون فيزيائي من ملاحظات",
        "prompt": "أعط ملاحظات تجريبية بسيطة (مثلاً: تسارع يتناسب مع القوة)، واطلب استنتاج قانون. اشرح خطوات الاستنتاج.",
        "keywords": ["قانون", "قوة", "تسارع", "استنتاج", "معادلة", "برهان"],
    })

    # Run tests
    results = []
    passed = 0

    for t in tests:
        print("\n=== Test: {} - {} ===".format(t["id"], t["title"]))
        resp = call_system(t["prompt"])
        formatted = resp.get("formatted")
        # formatted may be dict or string
        if isinstance(formatted, dict):
            formatted_text = json.dumps(formatted, ensure_ascii=False)
        else:
            formatted_text = str(formatted)

        print(formatted_text)

        ok = check_contains_any(formatted_text, t.get("keywords", []))
        results.append({"id": t["id"], "title": t["title"], "ok": ok, "answer": formatted_text})
        status = "PASS" if ok else "FAIL"
        print(f"Result: {status}")
        if ok:
            passed += 1

    total = len(tests)
    pct = (passed / total) * 100.0

    print("\n===== SUMMARY =====")
    print(f"Passed {passed} of {total} tests ({pct:.1f}%)")

    # Save detailed artifact
    os.makedirs("artifacts", exist_ok=True)
    out_path = os.path.join("artifacts", "cagi_run_output.json")
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump({"results": results, "passed": passed, "total": total, "pct": pct}, fh, ensure_ascii=False, indent=2)

    print(f"Detailed results written to {out_path}")


if __name__ == "__main__":
    main()
