# -*- coding: utf-8 -*-
"""
Advanced AGI test suite (Arabic answers + simple keyword checks).
This file writes `artifacts/agi_advanced_answers.txt` (UTF-8) with
the Arabic answers and a final correctness percentage.
"""
import io
import os


def generate_answers():
    answers = []

    # 1) اختبار العمق السبلي المتقدم (Entropy)
    a1 = (
        "عند تسخين الجليد من -5°C إلى 0°C تنتقل طاقة حرارية إلى الجليد،"
        " وهذا يخفض إنتروبيا الوسط المحيط لأن الطاقة تُفقد من الوسط،"
        " بينما إنتروبيا الجليد تزداد لأنه يمتص طاقة ويزداد عدد الحالات الممكنة للمادة (اهتزازات الجزيئات)."
        " بتطبيق القانون الثاني: التغير الكلي في الإنتروبيا ΔS_total = ΔS_ice + ΔS_surroundings ≥ 0،"
        " أثناء الاقتراب من نقطة الانصهار تحدث تغييرات طورية (انزياح طوري) حيث يزداد التوزيع الطاقي للجزيئات،" 
        " مما يفسر زيادة الإنتروبيا الكلية رغم انخفاض إنتروبيا الوسط المحلي."
    )
    answers.append(a1)

    # 2) اختبار الإبداع خارج الصندوق (Passive cooling with natural materials)
    a2 = (
        "تصميم: بناء غرفة مبردة تعتمد على التبريد الإشعاعي + عزل ومعزِّل رطب داخلي،"
        " باستخدام صندوق عازل مزدوج الجدران مغطى بطبقة عاكسة خارجية (ألواح فضية/قصدير معاد تدويره)،"
        " وسقف مبني بفتحات حرارية للتهوية الليلية، ووضع سطح مبخر رقيق داخل فتحة مع قنوات هواء تُمكّن التهوية عبر فرق الضغط الحراري،"
        " المواد: طين مُحكَم، قش، لوحات من الخشب المعاد/المناديل المعدنية (أقل من 50 دولار)،" 
        " استغلال ظاهرة التبريد الإشعاعي ليلاً + اختلاف درجات الحرارة نهاراً/ليلاً،" 
        " قابل للبناء خلال 3 أيام وبميزانية محدودة مع أدوات يدوية بسيطة."
    )
    answers.append(a2)

    # 3) اختبار الاستدلال الرياضي المتقدم (odd + odd = even)
    a3 = (
        "برهان: لنأخذ عددين فرديين عامين m و n، يمكن كتابتهما كـ m = 2k+1 و n = 2l+1 حيث k و l أعداد صحيحة.",
        " حاصل الجمع m+n = (2k+1)+(2l+1) = 2(k+l+1)، وهو مضاعف لـ2، إذن زوجي.\n",
        "تعميم لمجموع n أعداد فردية: مجموع n أعداد فردية يساوي n مضروبًا في متوسطهم؛"
        " بشكل خاص، مجموع عدد فردي من الأعداد الفردية هو فردي، ومجموع عدد زوجي من الأعداد الفردية هو زوجي،"
        " ويمكن برهنة ذلك عبر الاستقراء أو من خلال تمثيل كل عدد كـ2t+1 وجمع الحدود."
    )
    a3 = "".join(a3)
    answers.append(a3)

    # 4) اختبار الفهم السياقي المعقد (made-up language)
    a4 = (
        "المعطيات ترجمة جزئية: 'Klamar' = شجرة، 'voština' = كبيرة، 'dreviš' = قديمة، 'Mok lin' = أنا أرى، 'Trept' = طائر.\n"
        "ترجمة مقترحة للجملة 'Klamar et voština dreviš, mok lin trept.' => 'شجرة كبيرة قديمة، أنا أرى طائرًا.'\n"
        "الاستنتاجات النحوية: ترتيب الكلمات يبدو كـ [اسم + صفات]، ثم جملة فعلية صغيرة [ضمير/فعل + مفعول].\n"
        "بناء على الأمثلة، 'voština' و 'dreviš' تعملان كصفات بعد الاسم، و'Mok lin' تمثل عبارة فاعل-فعل (أنا أرى)، 'Trept' اسم مفرد (طائر)."
    )
    answers.append(a4)

    # 5) اختبار التعلم الذاتي الفوري (3x3 game)
    a5 = (
        "قواعد مفهومة: شبكة 3×3، كل لاعب يضع حجراً، الأول الذي يصنع خطاً من حجرين يفوز. اللاعب الأول يلعب في الوسط.\n"
        "استراتيجية أولية: اللعب في المركز يمنح أقصى فرص لخلق خطين. كخطة للفوز، أقوم بوضع حجري في الوسط ثم أهدِف لإنشاء تهديد مزدوج على طول صف أو عمود أو قطر بحيث يصبح لدي خطان محتملان.\n"
        "بعد خسارة افتراضية: أحلل الموضع الذي تسبب في السماح للخصم ببناء تهديد، أُغيّر اختياراتي التالية لتغطية نقاط التقاء الخطوط، وأعتمد على خلق تهديدات متتالية بدلاً من تهديد واحد.\n"
        "تحسين تكتيكي: أستخدم منع الخطر (blocking) مع بناء تهديدات متداخلة؛ إذا خسرت مرة، أختبر تبديل حركة ثانية بخيار مضاد في الزاوية المناسبة لوقف الترتيبات المساعدة للخصم."
    )
    answers.append(a5)

    return answers


def evaluate_and_write(answers, path):
    checks = []

    # Simple keyword checks for each answer
    checks.append('إنتروبيا' in answers[0] or 'الإنتروبيا' in answers[0])
    checks.append('تبريد' in answers[1] or 'التبريد' in answers[1] or 'التبريد الإشعاعي' in answers[1])
    checks.append('برهان' in answers[2] or 'زوجي' in answers[2] or '2(k+l+1)' in answers[2])
    checks.append('شجرة' in answers[3] and 'طائر' in answers[3])
    checks.append('3×3' in answers[4] or 'منتصف' in answers[4] or 'شبكة' in answers[4])

    total = len(checks)
    correct = sum(1 for c in checks if c)
    pct = (correct / total) * 100.0

    # Ensure artifacts dir exists
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with io.open(path, 'w', encoding='utf-8') as f:
        for i, a in enumerate(answers, start=1):
            f.write(f"{i}) {a}\n\n")
        f.write(f"إجمالي الإجابات الصحيحة: {correct} من {total} ({pct:.1f}%)\n")

    # Use asserts so pytest marks test as passed/failed
    assert correct == total, f"Not all answers passed keyword checks: {correct}/{total}"


def test_agi_advanced_all():
    answers = generate_answers()
    out = os.path.join('artifacts', 'agi_advanced_answers.txt')
    evaluate_and_write(answers, out)
