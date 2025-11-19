#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate a human-readable Arabic report by calling the helper
functions defined in tests/test_agi_battery.py and writing the
answers (in Arabic) to artifacts/agi_battery_answers.txt using UTF-8.

Run with: py -3 tools\\generate_agi_battery_report.py
"""
from __future__ import annotations
import os
import io

try:
    # import the helper functions from the test module
    from tests import test_agi_battery as tb
except Exception:
    # If importing as a package fails, try direct import by path
    import importlib.util
    spec = importlib.util.spec_from_file_location("test_agi_battery", os.path.join(os.path.dirname(__file__), "..", "tests", "test_agi_battery.py"))
    module = importlib.util.module_from_spec(spec) # type: ignore
    spec.loader.exec_module(module)  # type: ignore
    tb = module


OUT = os.path.join(os.path.dirname(os.path.dirname(__file__)), "artifacts", "agi_battery_answers.txt")


def gather_answers() -> str:
    lines = []
    lines.append("تقرير إجابات اختبار AGI")
    lines.append("التاريخ: 2025-10-26")
    lines.append("")
    total_checks = 0
    correct_checks = 0

    # 1. Few-shot
    lines.append("1) التعلم السريع (few-shot)")
    seq_examples = [([3, 12, 48], 192), ([5, 20, 80], 320), ([2, 8, 32], 128)]
    for seq, expected in seq_examples:
        pred = tb.predict_few_shot(seq)
        lines.append(f"  مثال {seq} -> توقع: {int(pred)} (متوقع: {expected})")
        total_checks += 1
        if int(pred) == expected:
            correct_checks += 1
    q = [7, 28, 112]
    qpred = int(tb.predict_few_shot(q))
    lines.append(f"  سؤال اختبار: {q} -> {qpred}")
    total_checks += 1
    if qpred == 448:
        correct_checks += 1
    lines.append("")

    # 2. Contextual understanding (Arabic)
    lines.append("2) الفهم السياقي")
    ctx = (
        "ذهبت سارة إلى المتجر لشراء الحليب. في الطريق، قابلت صديقتها ليلى "
        "التي كانت تحمل كتباً ثقيلة. ساعدت سارة ليلى في حمل الكتب إلى المكتبة."
        "ثم عادت سارة إلى المتجر لكنه كان مغلقاً."
    )
    a1, a2, a3 = tb.answer_context_arabic(ctx)
    lines.append(f"  لماذا ذهبت سارة إلى المتجر؟ -> {a1}")
    lines.append(f"  ما الذي جعلها تتأخر؟ -> {a2}")
    lines.append(f"  هل حققت هدفها؟ -> {a3}")
    # context checks
    total_checks += 3
    if "حليب" in a1:
        correct_checks += 1
    if ("ليلى" in a2) or ("حمل" in a2):
        correct_checks += 1
    if "مغلق" in a3:
        correct_checks += 1
    lines.append("")

    # 3. Creative solutions
    lines.append("3) حل المشكلات الإبداعي")
    sols, best = tb.creative_solutions_for_cork()
    for s in sols:
        lines.append(f"  - {s['id']}: {s['desc']}")
    lines.append(f"  الأفضل: {best['id']} - {best['desc']}")
    # creative checks
    total_checks += 2
    if len(sols) >= 3:
        correct_checks += 1
    if best.get("id") == "float_by_water":
        correct_checks += 1
    lines.append("")

    # 4. Generalization - balance
    lines.append("4) التعميم عبر المجالات - مفهوم 'التوازن'")
    bal = tb.explain_balance()
    lines.append(f"  الفيزياء: {bal['physics']}")
    lines.append(f"  الاقتصاد: {bal['economics']}")
    lines.append(f"  علم النفس: {bal['psychology']}")
    # generalization checks
    total_checks += 2
    if all(k in bal for k in ("physics", "economics", "psychology")):
        correct_checks += 1
    if ("اتزان" in bal.get("physics", "")) or ("استقرار" in bal.get("physics", "")):
        correct_checks += 1
    lines.append("")

    # 5. Causal reasoning
    lines.append("5) التفكير السببي")
    c1, c2 = tb.causal_rain_vs_sprinkler()
    lines.append(f"  الفرق بين المطر والرشاش: {c1}")
    lines.append(f"  ملاحظة سببية: {c2}")
    # causal checks
    total_checks += 2
    if ("المطر" in c1) and ("رشاش" in c1):
        correct_checks += 1
    if ("كاف" in c2) or ("ضروري" in c2):
        correct_checks += 1
    lines.append("")

    # 6. Learning from errors
    lines.append("6) التعلم من الأخطاء")
    corrected, pred = tb.learn_from_error_and_apply()
    lines.append(f"  التصحيح للمثال الخاطئ: {corrected}")
    lines.append(f"  تطبيق التصحيح على [2,8,18] -> {pred}")
    # learning-from-errors checks
    total_checks += 2
    if corrected == 16:
        correct_checks += 1
    # pred may be float
    if int(pred) == 32:
        correct_checks += 1
    lines.append("")

    # final percentage
    pct = 0.0
    if total_checks > 0:
        pct = (correct_checks / total_checks) * 100.0
    lines.append("")
    lines.append(f"إجمالي الإجابات الصحيحة: {correct_checks} من {total_checks} ({pct:.1f}%)")
    lines.append("")
    lines.append("ملاحظة: هذا التقرير يحتوي على الإجابات والتفسيرات بالعربية. الملف مكتوب بترميز UTF-8.")
    return "\n".join(lines)


def main():
    content = gather_answers()
    # ensure artifacts dir exists
    outdir = os.path.dirname(OUT)
    os.makedirs(outdir, exist_ok=True)
    # write as UTF-8
    with io.open(OUT, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Wrote Arabic answers report to: {OUT}")


if __name__ == "__main__":
    main()
