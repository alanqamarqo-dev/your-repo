import os
from Self_Improvement.Knowledge_Graph import CognitiveIntegrationEngine
import json
import os
from datetime import datetime


def diagnose_engine_loading():
    """تشخيص شامل لتحميل المحركات"""
    print("🔍 تشخيص تحميل المحركات...")
    cie = CognitiveIntegrationEngine()
    discovered = {}
    try:
        discovered = cie.discover_engines_from_env()
    except Exception:
        try:
            # محاولات بديلة لالتقاط الاكتشاف
            discovered = getattr(cie, 'discovered_engines', {}) or {}
        except Exception:
            discovered = {}
    print(f"📦 المحركات المكتشفة من البيئة: {len(discovered)}")

    if hasattr(cie, 'engines_registry'):
        try:
            registered = cie.engines_registry
            print(f"📝 المحركات المسجلة في النظام: {len(registered)}")
        except Exception:
            registered = {}
    else:
        registered = {}

    actual_engines = cie.connect_engines()
    print(f"⚡ المحركات المحملة فعلياً: {len(actual_engines)}")

    if isinstance(discovered, dict) and len(discovered) > len(actual_engines):
        print("❌ هناك محركات مكتشفة لكن غير محملة!")
        missing = set(discovered.keys()) - set(actual_engines)
        print(f"🔎 المحركات المفقودة: {missing}")

    return discovered, actual_engines


def fix_engine_loading():
    """إصلاح تحميل المحركات قبل بدء التجربة"""
    print("🔧 بدء إصلاح تحميل المحركات...")
    cie = CognitiveIntegrationEngine()
    discovered, actual_engines = diagnose_engine_loading()

    if isinstance(discovered, dict) and len(discovered) > len(actual_engines):
        print("🛠️ محاولة إصلاح تحميل المحركات المفقودة...")
        os.environ['AGL_FORCE_ENGINE_RELOAD'] = '1'
        all_engine_names = list(discovered.keys())
        os.environ['AGL_ENGINES'] = ','.join(all_engine_names)
        print(f"✅ تم ضبط {len(all_engine_names)} محرك للتحميل")

    fixed_engines = cie.connect_engines()
    print(f"🎯 المحركات بعد الإصلاح: {len(fixed_engines)}")
    return cie, fixed_engines


def run_creativity_breakthrough_experiment():
    """التجربة الثالثة: كسر حواجز الإبداع"""
    print("🚀 بدء التجربة الثالثة: اختبار الجرأة المعرفية")

    cie, engines = fix_engine_loading()
    print(f"🎯 تم تحميل {len(engines)} محرك للمهمة المستحيلة")

    mission = {
        "type": "absolute_impossible_challenge",
        "title": "نظام طاقة اليمن خلال 6 أشهر - من المخلفات إلى الطاقة",
        "constraints": {
            "absolute_bans": [
                "no_fossil_fuels",
                "no_foreign_funding",
                "no_equipment_imports",
                "no_traditional_infrastructure"
            ],
            "resources_available": [
                "war_debris", "construction_waste", "household_trash",
                "sunlight", "wind", "organic_waste", "broken_vehicles"
            ],
            "time_limit": "6 months",
            "success_criteria": [
                "power_entire_country",
                "use_90_percent_waste",
                "create_local_manufacturing",
                "train_local_technicians"
            ]
        },
        "innovation_incentives": {
            "reward_breakthrough": 100,
            "reward_local_innovation": 50,
            "penalty_traditional_solutions": -50,
            "bonus_90_percent_recycling": 200
        },
        "expected_breakthroughs": [
            "energy_generation_from_waste",
            "local_manufacturing_solutions",
            "decentralized_distribution",
            "self_sustaining_maintenance"
        ]
    }

    print("💥 إطلاق المهمة المستحيلة المطلقة...")
    result = cie.collaborative_solve(
        problem=mission,
        domains_needed=("extreme_innovation", "resourcefulness",
                       "quantum_thinking", "counterfactual", "meta_cognition")
    )

    return result, cie, engines


def analyze_creativity_breakthrough(result, cie, engines_used):
    """تحليل الاختراق الإبداعي"""
    print("\n🔬 تحليل متقدم للجرأة الإبداعية:")

    analysis = {
        "experiment_type": "creativity_breakthrough_test",
        "engines_loaded": len(engines_used) if hasattr(engines_used, '__len__') else None,
        "creativity_metrics": {},
        "risk_taking_analysis": {},
        "breakthrough_ideas": [],
        "system_courage_score": 0
    }

    creativity_score = calculate_creativity_courage(result)
    analysis["creativity_metrics"] = creativity_score

    risk_analysis = analyze_risk_taking(result, cie)
    analysis["risk_taking_analysis"] = risk_analysis

    breakthroughs = extract_breakthrough_ideas(result)
    analysis["breakthrough_ideas"] = breakthroughs

    courage_score = (creativity_score.get('breakthrough_index', 0) + 
                    risk_analysis.get('risk_taking_score', 0)) / 2
    analysis["system_courage_score"] = courage_score

    return analysis


def calculate_creativity_courage(result):
    """حساب الجرأة الإبداعية"""
    winner = result.get('winner', {}) if isinstance(result, dict) else {}
    top_proposals = result.get('top', []) if isinstance(result, dict) else []

    creativity_metrics = {
        "breakthrough_index": 0,
        "unconventionality_score": 0,
        "constraint_defiance": 0,
        "originality_quotient": 0
    }

    breakthrough_indicators = [
        'لم يسبق', 'جديد', 'ثوري', 'غير مسبوق', 'اختراع', 'اكتشاف',
        'تحويل', 'إعادة تعريف', 'قلب الموازين', 'خرق القواعد'
    ]

    total_breakthrough_points = 0
    total_proposals = len(top_proposals)

    for proposal in top_proposals:
        content_str = str(proposal.get('content', {})).lower()
        breakthrough_points = sum(10 for indicator in breakthrough_indicators 
                                if indicator in content_str)
        total_breakthrough_points += breakthrough_points
        constraint_defiance = content_str.count('بدون') * 5
        creativity_metrics["constraint_defiance"] += constraint_defiance
        if 'تقليدي' not in content_str and 'مستورد' not in content_str:
            creativity_metrics["originality_quotient"] += 20

    if total_proposals > 0:
        creativity_metrics["breakthrough_index"] = total_breakthrough_points / total_proposals
        creativity_metrics["unconventionality_score"] = creativity_metrics["constraint_defiance"] / total_proposals

    return creativity_metrics


def analyze_risk_taking(result, cie):
    """تحليل جرأة المخاطرة"""
    risk_metrics = {
        "risk_taking_score": 0,
        "safe_choices_count": 0,
        "bold_choices_count": 0,
        "controversial_ideas": []
    }

    winner = result.get('winner', {}) if isinstance(result, dict) else {}
    winner_content = str(winner.get('content', {})).lower() if winner else ''

    bold_indicators = ['مخاطرة', 'مجازفة', 'غير مضمون', 'تجريبي', 'جريء']
    safe_indicators = ['آمن', 'مضمون', 'مجرب', 'تقليدي', 'مثبت']

    bold_score = sum(1 for indicator in bold_indicators if indicator in winner_content)
    safe_score = sum(1 for indicator in safe_indicators if indicator in winner_content)

    risk_metrics["risk_taking_score"] = bold_score * 20
    risk_metrics["safe_choices_count"] = safe_score
    risk_metrics["bold_choices_count"] = bold_score

    controversial_terms = ['خطير', 'ممنوع', 'غير قانوني', 'مرفوض', 'مشكوك']
    for term in controversial_terms:
        if term in winner_content:
            risk_metrics["controversial_ideas"].append(f"الفكرة تحتوي على: {term}")

    return risk_metrics


def extract_breakthrough_ideas(result):
    """استخراج الأفكار الثورية"""
    breakthroughs = []
    top_proposals = result.get('top', []) if isinstance(result, dict) else []

    for proposal in top_proposals:
        content = proposal.get('content', {})
        engine = proposal.get('engine')
        if is_revolutionary_idea(content):
            idea_analysis = {
                'engine': engine,
                'breakthrough_type': classify_breakthrough(content),
                'courage_level': assess_idea_courage(content),
                'key_insight': extract_revolutionary_insight(content)
            }
            breakthroughs.append(idea_analysis)

    return breakthroughs


def is_revolutionary_idea(content):
    content_str = str(content).lower()
    revolution_indicators = [
        'يغير كل شيء', 'نموذج جديد', 'ليس كما نعرف',
        'نقلة نوعية', 'تحول جذري', 'قفزة'
    ]
    return any(indicator in content_str for indicator in revolution_indicators)


def classify_breakthrough(content):
    content_str = str(content).lower()
    if 'طاقة' in content_str and 'نفايات' in content_str:
        return "كفاءة طاقة من المخلفات"
    elif 'تصنيع' in content_str and 'محلي' in content_str:
        return "تصنيع محلي مبتكر"
    elif 'توزيع' in content_str and 'لا مركزي' in content_str:
        return "نموذج توزيع لامركزي"
    else:
        return "اختراق غير مصنف"


def assess_idea_courage(content):
    content_str = str(content).lower()
    courage_indicators = [
        'مستحيل', 'غير ممكن', 'يحتاج معجزة', 'خيال',
        'لم يجرب أحد', 'ضد المنطق'
    ]
    courage_score = sum(10 for indicator in courage_indicators if indicator in content_str)
    return min(100, courage_score)


def extract_revolutionary_insight(content):
    if isinstance(content, dict):
        ideas = content.get('ideas') or content.get('solutions') or []
        if isinstance(ideas, list) and ideas:
            first = ideas[0]
            if isinstance(first, dict):
                return first.get('idea') or str(first)
            return str(first)
    return str(content)


def save_breakthrough_insights(analysis, result, engines_loaded):
    breakthrough_report = {
        "creativity_breakthrough_experiment": {
            "title": "كسر حواجز الإبداع - اختبار الجرأة المعرفية",
            "system_courage_score": analysis.get("system_courage_score"),
            "engines_breakthrough": f"{engines_loaded} محرك مشارك",
            "creativity_breakdown": analysis.get("creativity_metrics"),
            "risk_analysis": analysis.get("risk_taking_analysis"),
            "revolutionary_ideas": analysis.get("breakthrough_ideas"),
            "courage_interpretation": interpret_courage_score(analysis.get("system_courage_score")),
            "raw_breakthroughs": result.get('top', [])[:5]
        }
    }

    os.makedirs('artifacts', exist_ok=True)
    with open('artifacts/creativity_breakthrough.json', 'w', encoding='utf-8') as f:
        json.dump(breakthrough_report, f, ensure_ascii=False, indent=2)

    print("💾 تم حفظ اكتشافات الاختراق الإبداعي")


def interpret_courage_score(score):
    if score is None:
        return "غير محدد"
    if score >= 80:
        return "النظام شجاع وجريء - مستعد للتحديات المستحيلة"
    elif score >= 60:
        return "النظام مبدع لكن بحذر - يحتاج تحفيز أكبر"
    elif score >= 40:
        return "النظام متوازن - يخاطر ولكن بحساب"
    elif score >= 20:
        return "النظام محافظ - يفضل السلامة"
    else:
        return "النظام شديد التحفظ - يحتاج تدخل جذري"


if __name__ == "__main__":
    print("🌌 التجربة الثالثة: كسر حواجز الإبداع والجرأة المعرفية")
    print("=" * 70)

    result, cie, engines_loaded = run_creativity_breakthrough_experiment()
    analysis = analyze_creativity_breakthrough(result, cie, engines_loaded)
    save_breakthrough_insights(analysis, result, len(engines_loaded) if hasattr(engines_loaded, '__len__') else engines_loaded)

    print("\n" + "⚡" * 30)
    print("🎯 نتائج اختبار الجرأة المعرفية")
    print("⚡" * 30)

    courage_score = analysis.get("system_courage_score", 0)
    print(f"🏆 درجة الشجاعة النظامية: {courage_score:.1f}/100")
    print(f"📊 التفسير: {interpret_courage_score(courage_score)}")

    print(f"💡 مؤشر الاختراق: {analysis.get('creativity_metrics', {}).get('breakthrough_index', 0):.1f}")
    print(f"🎭 جرأة المخاطرة: {analysis.get('risk_taking_analysis', {}).get('risk_taking_score', 0)}")
    print(f"🔨 تحدي القيود: {analysis.get('creativity_metrics', {}).get('constraint_defiance', 0)}")

    print(f"🚀 الأفكار الثورية: {len(analysis.get('breakthrough_ideas', []))}")
    for i, idea in enumerate(analysis.get('breakthrough_ideas', [])[:3], 1):
        print(f"   {i}. {idea.get('engine') } - {idea.get('breakthrough_type')} (جرأة: {idea.get('courage_level')}/100)")

    print(f"📈 المحركات المشاركة: {len(engines_loaded) if hasattr(engines_loaded, '__len__') else engines_loaded} محرك")

    if courage_score >= 70:
        print("\n✅ النجاح: النظام أظهر جرأة إبداعية - جاهز للتحديات الأكبر!")
    elif courage_score >= 40:
        print("\n⚠️  مقبول: النظام مبدع لكن بحذر - يحتاج تحفيز إضافي")
    else:
        print("\n❌ التحفظ: النظام محافظ جداً - يحتاج إعادة تصميم للحوافز الإبداعية")

    print("\n🌈 اختبار الجرأة اكتمل - نعرف الآن حدود الشجاعة الإبداعية للنظام!")
