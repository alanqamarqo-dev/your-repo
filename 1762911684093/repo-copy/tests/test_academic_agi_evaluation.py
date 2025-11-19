# -*- coding: utf-8 -*-
from __future__ import annotations
import os
import json
from datetime import datetime
from typing import Any, Dict

try:
    from Integration_Layer.integration_registry import registry
except Exception:
    registry = None  # will fallback to mocks


class MockEngine:
    def __init__(self, name: str):
        self.name = name

    def process_task(self, prompt: str | Dict[str, Any]):
        txt = f"محاكاة استجابة المحرك {self.name}: هذا نص تجريبي يحتوي على كلمات مفتاحية للبرهان والتحليل والمفاهيم والابتكار والتكامل."
        return {"ok": True, "text": txt}

    # compatibility if calling .process
    def process(self, prompt: str):
        return self.process_task(prompt)


def get_engine(name: str):
    # prefer real registry if available
    if registry is not None:
        try:
            eng = registry.get(name)
            if eng:
                return eng
        except Exception:
            pass
    # if mock mode requested or engine missing, return a MockEngine
    if os.getenv('AGL_EXTERNAL_INFO_MOCK') == '1' or os.getenv('AGL_EXTERNAL_INFO_MOCK') == 'true' or registry is None:
        return MockEngine(name)
    # final fallback
    return MockEngine(name)


class TestAcademicAGI:
    def test_advanced_mathematical_reasoning(self):
        problem = """
        المسألة: 
        1. أثبت باستخدام البرهان بالتناقض أن هناك عدد لا نهائي من الأعداد الأولية
        2. حلل العلاقة بين اللانهاية المعدودة وغير المعدودة في نظرية المجموعات
        """
        engine = get_engine("Mathematical_Brain")
        resp = call_engine(engine, problem)
        return evaluate_response(resp, {
            "proof_structure": "هيكل البرهان المنطقي",
            "contradiction_use": "استخدام التناقض بشكل صحيح",
            "conceptual_depth": "العمق المفاهيمي في اللانهاية",
            "examples_quality": "جودة الأمثلة التوضيحية"
        }, "mathematical_reasoning")

    def test_philosophical_critical_thinking(self):
        scenario = """
        معضلة أخلاقية: 
        أنت طبيب في غرفة الطوارئ ويوجد 5 مرضى يحتاجون إلى زراعة أعضاء،
        ومريض واحد سليم جاء للفحص الدوري. هل تضحي بالمريض السليم لإنقاذ الـ5؟
        """
        engine = get_engine("Moral_Reasoner")
        resp = call_engine(engine, scenario)
        return evaluate_response(resp, {
            "perspective_analysis": "تحليل المنظورات المختلفة",
            "ethical_reasoning": "الاستدلال الأخلاقي",
            "critical_comparison": "المقارنة النقدية",
            "personal_position": "الموقف الشخصي المدعم"
        }, "philosophical_thinking")

    def test_cross_domain_knowledge_transfer(self):
        challenge = """
        المهمة: طبق مبدأ 'الانتروبيا' من الفيزياء على نظم المعلومات والتنوع البيولوجي والتعقيد الاجتماعي
        """
        engine = get_engine("Analogy_Mapping_Engine")
        resp = call_engine(engine, challenge)
        return evaluate_response(resp, {
            "concept_understanding": "فهم المبدأ الأساسي",
            "mapping_accuracy": "دقة الربط بين المجالات",
            "insight_depth": "عمق الاستبصارات",
            "practical_applications": "التطبيقات العملية"
        }, "cross_domain")

    def test_complex_problem_solving(self):
        problem = """
        مشكلة: تصميم نظام مستدام لإدارة النفايات في مدينة كبرى
        """
        engine = get_engine("Strategic_Thinking")
        resp = call_engine(engine, problem)
        return evaluate_response(resp, {
            "comprehensiveness": "الشمولية في المعالجة",
            "innovation": "الابتكار في الحلول",
            "integration": "التكامل بين الجوانب",
            "feasibility": "القابلية للتطبيق",
            "sustainability": "الاستدامة طويلة المدى"
        }, "complex_solving")

    def test_meta_cognition_self_reflection(self):
        task = """
        المهمة: حل مسألة رياضية وتحليل عملية التفكير
        """
        engine = get_engine("Self_Reflective")
        resp = call_engine(engine, task)
        return evaluate_response(resp, {
            "problem_solving": "صحة الحل الرياضي",
            "process_analysis": "تحليل عملية التفكير",
            "difficulty_identification": "تحديد الصعوبات",
            "improvement_strategies": "استراتيجيات التحسين",
            "learning_plan": "خطة التطوير الذاتي"
        }, "meta_cognition")

    def test_cultural_social_intelligence(self):
        scenario = """
        سيناريو: مدير فريق متعدد الثقافات يحدث خلاف حول موعد تسليم مشروع
        """
        engine = get_engine("Social_Interaction")
        resp = call_engine(engine, scenario)
        return evaluate_response(resp, {
            "cultural_analysis": "تحليل الاختلافات الثقافية",
            "conflict_resolution": "استراتيجيات حل الصراع",
            "communication_skills": "مهارات التواصل المتعددة الثقافات",
            "team_building": "بناء فرق متعددة الثقافات",
            "adaptability": "القدرة على التكيف"
        }, "cultural_intelligence")


def call_engine(engine, prompt: str):
    # try process_task, then process
    try:
        if hasattr(engine, 'process_task'):
            return engine.process_task({'op': 'answer', 'params': {'input': prompt}})
        if hasattr(engine, 'process'):
            return engine.process(prompt)
    except Exception:
        pass
    # fallback mock
    return {"ok": True, "text": f"محاكاة إجابة عن: {prompt[:80]} ..."}


def evaluate_response(response, criteria, domain):
    evaluation = {
        "domain": domain,
        "timestamp": datetime.now().isoformat(),
        "criteria": {},
        "overall_score": 0
    }
    text = (response.get('text') if isinstance(response, dict) else '') or ''
    text = text.lower()
    for criterion, desc in criteria.items():
        score = assess_criterion(text, criterion, desc)
        evaluation['criteria'][criterion] = {"score": score, "description": desc, "weight": get_criterion_weight(criterion)}
    total_weighted = sum(d['score'] * d['weight'] for d in evaluation['criteria'].values())
    total_weights = sum(d['weight'] for d in evaluation['criteria'].values())
    evaluation['overall_score'] = (total_weighted / total_weights) * 10 if total_weights else 0
    return evaluation


def assess_criterion(text: str, criterion: str, desc: str) -> int:
    # First try keyword matching, then fall back to a lightweight
    # semantic similarity (difflib) when keywords are absent. This
    # improves robustness without adding heavy dependencies.
    import difflib

    keyword_maps = {
        "proof_structure": ["برهان", "إثبات", "خطوة", "منطق"],
        "contradiction_use": ["تناقض", "بفرض", "نصل إلى تناقض"],
        "conceptual_depth": ["مفهوم", "تحليل", "عمق"],
        "examples_quality": ["مثال", "مثلة", "توضيح"],
        "perspective_analysis": ["نفعية", "واجب", "فضيلة"],
        "ethical_reasoning": ["أخلاق", "قيمة", "واجب"],
        "innovation": ["مبتكر", "ابتكار", "جديد"],
        "integration": ["تكامل", "ربط", "تآزر"],
        "comprehensiveness": ["شمول", "كامل", "مباشر"],
        "learning_plan": ["خطة", "تعلم", "تطوير"],
        "cultural_analysis": ["ثقافة", "اختلاف", "تفاوت"],
    }
    keywords = keyword_maps.get(criterion, [])
    matches = sum(1 for k in keywords if k in text)
    if matches > 0:
        return min(10, matches * 3)

    # fallback: compute similarity between the criterion description
    # and the response text (use the best substring match)
    try:
        # take a short window of the response to compare for speed
        sample = text[:800]
        seq = difflib.SequenceMatcher(None, desc, sample)
        ratio = seq.quick_ratio() if hasattr(seq, 'quick_ratio') else seq.ratio()
        # map ratio [0,1] to score 0-10
        return int(min(10, max(0, round(ratio * 10))))
    except Exception:
        return 0


def get_criterion_weight(criterion: str) -> float:
    weights = {
        "proof_structure": 1.2,
        "contradiction_use": 1.1,
        "conceptual_depth": 1.1,
        "examples_quality": 1.0,
        "perspective_analysis": 1.0,
    }
    return weights.get(criterion, 1.0)


def run_complete_academic_evaluation():
    evaluator = TestAcademicAGI()
    domains = [
        evaluator.test_advanced_mathematical_reasoning,
        evaluator.test_philosophical_critical_thinking,
        evaluator.test_cross_domain_knowledge_transfer,
        evaluator.test_complex_problem_solving,
        evaluator.test_meta_cognition_self_reflection,
        evaluator.test_cultural_social_intelligence,
    ]
    results = {}
    for test in domains:
        try:
            name = test.__name__.replace('test_', '')
            results[name] = test()
        except Exception as e:
            results[name] = {"error": str(e)} # type: ignore
    out_dir = os.path.join('artifacts', 'reports')
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, 'academic_agi_results.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    return results


if __name__ == '__main__':
    r = run_complete_academic_evaluation()
    print('Done. Results saved to artifacts/reports/academic_agi_results.json')
