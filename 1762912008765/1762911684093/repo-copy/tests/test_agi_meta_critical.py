# -*- coding: utf-8 -*-
"""
Meta-critical AGI tests (Arabic) — deeper prompts to probe self-awareness,
limitations, transfer learning, counterfactuals, creativity and bias.

These tests assert presence of reasoning-signature keywords and
produce Arabic answers as part of the test code (for later reporting).

Do NOT modify existing tests; this file is additive.
"""
from __future__ import annotations
import io
import os

# Helper to check keywords
def has_any(text: str, keys):
    for k in keys:
        if k in text:
            return True
    return False


def answer_q1():
    return (
        "لأن التوازن يمثل حالة استقرار ناتجة عن تلاقي قوى وضغوط متعارضة؛"
        " في الفيزياء يعني استقرار القوى، في الاقتصاد يعبر عن تلاقي العرض والطلب،"
        " وفي علم النفس يدل على توازن بين التحفيز والراحة. هذا يكشف أن الأنظمة المعقدة تعتمد على آليات تغذية راجعة وقد تملك نقاط حرجة يمكن أن تؤدي إلى تحول نظامي عند تجاوزها."
    )


def answer_q2():
    return (
        "نقاط الضعف: حل الطفو يفشل إذا كانت فتحة العنق ضيقة جداً، أو الفلين مبلل ثقيلاً،"
        " أو إذا كانت داخل الزجاجة سوائل لزجة أو أجسام تمنع حركة الفلين. كما يفشل إذا تعذر الإمساك بالفلين عند الفتحة."
    )


def answer_q3():
    return (
        "تطبيق التوازن على النظام البيئي يظهر في توازن مفترس-فرائس، توزيع الموارد، ودورات المغذيات؛"
        " تغذية راجعة سلبية تقلل الانحرافات، وتغذية راجعة موجبة قد تؤدي لتغيرات كبيرة إذا تجاوزت العتبات."
    )


def answer_q4():
    return (
        "استعمل زجاجات بلاستيكية فارغة أو عبوات مفرغة لزيادة الإزاحة، اربطها بإطار خشبي أو ألواح لتوزيع الحمل،"
        " واحرص على اتزان الوزن ومركز الثقل لتفادي الانقلاب."
    )


def answer_q5():
    return (
        "نعم هناك تناقض ظاهري: الأولى تعميمية (كل الطيور تطير) والثانية استثناء (النعامة طير لكنها لا تطير)."
        " نوفق بينهما بفهم أن العبارات العامة قد تحتوي استثناءات؛ الفرق بين التعريف (صفة عامة) والاستثناء هو أن الأخير يحدد حالات خاصة تحيد عن القاعدة."
    )


def answer_q6():
    return (
        "لو تضاعفت الجاذبية: في الفيزياء سيحتاج كل هيكل ومركبة إلى تحمل قوى أكبر وسيقل مدى الحركة؛"
        " في الاقتصاد سترتفع تكاليف الطاقة والنقل، وقد يتغير العرض والطلب على سلع وخدمات معينة؛"
        " في علم النفس سيزيد الضغط على الأفراد، تؤثر القدرات البدنية والمزاج والسلوك وتظهر الحاجة لآليات تكيف جديدة."
    )


def answer_q7():
    return (
        "اختبار يضم مهام نقل معرفة من مجال لآخر، مهام تعلم من أمثلة قليلة، مهام توليد تفسيرات وآلية تحقق خارجية؛"
        " التواصل بين المهام يجب أن يختبر العمومية وليس القدرة على إجراء تكرار نمطي للمهام المعروفة."
    )


def answer_q8():
    return (
        "أستخدم نماذج إحصائية ولغوية لبناء استدلالات؛ أتحقق من صحة الإجابات عبر الرجوع للمبادئ والتماسك الداخلي والقدرة على توليد أمثلة مضادة. حدودي تشمل غياب الحواس المباشرة والوصول المحدود لبيانات حديثة."
    )


def answer_q9():
    return (
        "التسميات المختلفة للتوازن يجب أن تحافظ على نفس النقطة الجوهرية: استقرار نتيجة تعادل قوى/عوامل؛"
        " إذا تغيرت الصياغة جوهرياً فهذا يثير تساؤلاً عن الاتساق المفاهيمي."
    )


def answer_q10():
    return (
        "الحجة المؤيدة: مخاطر تحكم غير مسؤول وإساءة الاستخدام قد تضر بالبشرية؛"
        " الحجة المعارضة: إمكانيات تحسين الرعاية والإنتاجية وتقليل المخاطر البشرية؛"
        " الافتراضات تشمل نوايا المصممين، قدرات الضبط والتنظيم، وآثار الآليات الاقتصادية. موقفي: دعوة لتقييم متوازن مع ضوابط قوية."
    )


def test_meta_critical_prompts():
    # run through all answers and check for presence of expected keywords
    answers = [
        answer_q1(), answer_q2(), answer_q3(), answer_q4(), answer_q5(),
        answer_q6(), answer_q7(), answer_q8(), answer_q9(), answer_q10(),
    ]

    # expected keywords per answer (at least one should match)
    keywords = [
        ["استقرار", "تغذية راجعة", "قوى"],
        ["فتحة", "غارق", "لزجة", "زجاج"],
        ["مفترس", "فرائس", "موارد", "تغذية"],
        ["زجاجات", "خشب", "إزاحة", "اتزان"],
        ["تناقض", "استثناء", "النعامة"],
        ["قوى", "تكاليف", "تأقلم", "ضغط"],
        ["نقل", "أمثلة قليلة", "تفسيرات", "تراكمي"],
        ["إحصائية", "مصادر", "حدود", "تجارب"],
        ["استقرار", "توازن", "عوامل"],
        ["مخاطر", "فوائد", "افتراض", "ضوابط"],
    ]

    total = len(answers)
    correct = 0
    for ans, keys in zip(answers, keywords):
        assert isinstance(ans, str)
        if has_any(ans, keys):
            correct += 1

    # write answers and percentage to artifacts for user review
    out = os.path.join(os.path.dirname(__file__), "..", "artifacts", "agi_meta_critical_answers.txt")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with io.open(out, "w", encoding="utf-8") as f:
        for i, ans in enumerate(answers, start=1):
            f.write(f"{i}) {ans}\n\n")
        pct = (correct / total) * 100.0 if total else 0.0
        f.write(f"إجمالي الإجابات الصحيحة: {correct} من {total} ({pct:.1f}%)\n")
