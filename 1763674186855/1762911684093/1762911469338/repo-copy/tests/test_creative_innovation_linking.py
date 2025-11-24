# -*- coding: utf-8 -*-
from Core_Engines.Creative_Innovation import CreativeInnovationEngine


def test_concept_blending_and_refine():
    eng = CreativeInnovationEngine()
    blended = eng.combine_concepts(["دراجات كهربائية", "طرق ذكية"], method="blending")
    assert "⟂" in blended["concept"]

    idea = "مشاركة دراجات كهربائية بإشارات طرق ذكية"
    refined = eng.refine(idea, {"budget": 2000, "timeline_days": 30, "sustainability": True})
    txt = refined["improved_idea"]
    assert "منخفضة التكلفة" in txt
    assert "30 يومًا" in txt
    assert "إعادة التدوير" in txt or "الانبعاثات" in txt
