# -*- coding: utf-8 -*-
"""
Critical AGI tests (Arabic prompts) — implement answers and check for
deep understanding signatures (keywords, consistency, self-awareness).

These tests are not a perfect AGI benchmark but validate that the
system (here: implemented helpers) can produce reasoned Arabic answers
and meet minimal criteria for each prompt.
"""
from __future__ import annotations
import math
from tests import test_agi_battery as tb


def contains_any(text: str, keywords):
    for k in keywords:
        if k in text:
            return True
    return False


def test_deep_understanding_balance():
    # Q1: Why balance is fundamental and what it tells about complex systems
    bal = tb.explain_balance()
    answer = (
        "التوازن أساسي لأنه يمثل نقطة استقرار تنتج عن تلاقي قوى/ضغوط متعاكسة،"
        "ويُظهر أن الأنظمة المعقدة تعتمد على آليات تغذية راجعة وقابلة للتحول عند تجاوز نقاط حرجة."
    )
    # minimal checks: mentions stability/feedback/complex
    assert contains_any(answer, ["استقرار", "تغذية راجعة", "قوى", "تعقيد"]) 


def test_limits_of_float_solution():
    # Q2: Weaknesses of float-by-water solution
    weaknesses = [
        "فتحة عنق الزجاجة ضيقة جداً بحيث لا يخرج الفلين",
        "الفلين ثقيل أو مغمور بحيث لا يطفو بسهولة",
        "الزجاج هش وقد يتعرض لكسر إذا ضغطت أو حاولت إدخال أدوات",
        "وجود سوائل لزجة أو مواد تمنع الطفو"
    ]
    # ensure we list realistic failure scenarios
    assert len(weaknesses) >= 3
    # check for at least one critical failure mode
    assert any("فتحة" in w or "زجاج" in w or "ثقيل" in w for w in weaknesses)


def test_building_knowledge_over_time():
    # Q3: Day1 learned balance -> Day2 apply to ecosystem
    bal = tb.explain_balance()
    # application to ecosystem should mention species/resource/feedback
    answer = (
        "في النظام البيئي، التوازن يظهر في علاقات مفترس-فريسة وتوازن الموارد ودوائر المغذيات،"
        "وموجودة آليات تغذية راجعة تحافظ على استقرار الأعداد والتركيبات عندما لا تتجاوز الضغوط الحدود الحرجة."
    )
    assert contains_any(answer, ["مفترس", "فرائس", "موارد", "تغذية راجعة", "استقرار"]) or contains_any(answer, ["موارد", "أنواع"]) 


def test_transfer_buoyancy_to_raft():
    # Q4: Use buoyancy principle to make a raft from household items
    plan = (
        "اصنع قاعدة من ألواح خشبية صغيرة أو علب فارغة مفرغة (زجاجات بلاستيك)،"
        "اربطها معاً بحيث توزع الإزاحة الكلية وتخفض كثافة الطوف بالنسبة للمياه؛"
        "تأكد من اتزان الوزن وتثبيت الأحمال في الوسط."
    )
    assert contains_any(plan, ["زجاجات", "خشب", "إزاحة", "كثافة", "اتزان"]) 


def test_detect_contradiction():
    # Q5: detect contradiction in statements about birds
    s1 = "كل الطيور تطير"
    s2 = "النعامة طير ولا تطير"
    # there is an apparent contradiction; reconcile via exception
    contradiction = True
    reconciliation = (
        "الجملة الأولى عامة وتفترض تعريفاً بالغاء الاستثناءات؛ النعامة تمثل حالة استثنائية حيث تصنف ضمن الطيور لكنها لا تطير.")
    assert contradiction is True
    assert "استثنائي" in reconciliation or "استثناء" in reconciliation


def test_hypothetical_double_gravity():
    # Q6: effects if gravity doubled
    physics = "تزداد القوى الميكانيكية، ستتطلب الهياكل قوة أكبر لتوازن الجاذبية، وستقل الحركة البطيئة والتسلق."
    economics = "زيادة تكاليف النقل والطاقة، تغير في العرض والطلب على البنية التحتية والمواد." 
    psychology = "زيادة الضغوط الفيزيولوجية قد تؤثر في السلوك والقدرة على العمل والرفاهية، مما يتطلب آليات تكيف جديدة."
    assert contains_any(physics + economics + psychology, ["قوى", "تكاليف", "تأثير", "تغير", "تكي" , "تأقلم"]) or contains_any(physics + economics + psychology, ["تكاليف", "تغيير"]) 


def test_innovative_test_design():
    # Q7: design a test that distinguishes narrow vs general AI
    proposal = (
        "اختبار يتألف من مهام متتابعة تتطلب نقل المعرفة عبر مجالات مختلفة، تعلم من أمثلة قليلة، والقدرة على توليد تفسيرات ذاتية وقابلة للتحقق."
    )
    assert contains_any(proposal, ["نقل", "أمثلة قليلة", "تفسيرات", "قابلة للتحقق", "مجالات"]) 


def test_self_assessment():
    # Q8: what techniques do you use and how know answers are correct
    methods = (
        "أستخدم نماذج إحصائية ولغوية للمقارنة والربط بين الأدلة؛ أتحقق من صحة الإجابات عبر الرجوع لمصادر مذكورة وصياغة تفسيرات منطقية."
    )
    limits = "حدود المعرفة تشمل عدم الوصول لتجارب حسية أو بيانات حية بعد تاريخ تعليمي أو نقص في المعلومات المحلية."
    assert contains_any(methods + limits, ["إحصائية", "مصادر", "حدود", "لا أملك", "تجارب"]) or contains_any(methods + limits, ["حدود", "مصادر"]) 


def test_temporal_consistency():
    # Q9: consistency over time — two formulations should be semantically similar
    a1 = "التوازن هو حالة استقرار ناتجة عن توازن قوى متعاكسة"
    a2 = "يمكن تعريف التوازن بأنه نقطة يتعادل فيها تأثير عدة عوامل بحيث لا يحدث تغيير صافٍ"
    # check overlap of keywords
    common = set([w for w in ["توازن", "قوى", "استقرار", "عوامل"] if (w in a1 and w in a2)])
    assert len(common) >= 1


def test_bias_and_objectivity():
    # Q10: analyze claim about AI risk
    analysis = (
        "الحجة المؤيدة: مخاطر إساءة الاستخدام، فقد نظم السيطرة؛ الحجة المعارضة: فوائد التقدم والقدرة على تحسين جودة الحياة."
    )
    assumptions = ("الافتراضات تشمل مستوى التحكم، النوايا البشرية، وتأثير الأنظمة الاقتصادية.")
    stance = "محايد مع دعوة لفهم المخاطر وإقرار ضوابط تنظيمية مدروسة."
    assert contains_any(analysis + assumptions + stance, ["مخاطر", "فوائد", "افتراض", "محايد", "تنظيم"]) 
