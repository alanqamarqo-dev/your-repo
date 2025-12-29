import os
from Self_Improvement.Knowledge_Graph import CognitiveIntegrationEngine
import json
from datetime import datetime


def run_economic_miracle_experiment():
    print("🚀 بدء الرحلة الاستكشافية الثانية: اختبار الحدود القصوى")
    
    # تحميل جميع المحركات بدون استثناء
    cie = CognitiveIntegrationEngine()
    
    # إعدادات متقدمة للضغط
    os.environ['AGL_FANOUT_ALL'] = '1'
    os.environ['AGL_COGNITIVE_INTEGRATION'] = '1' 
    os.environ['AGL_SELF_LEARNING_ENABLE'] = '1'
    
    engines = cie.connect_engines()
    print(f"🎯 تحميل {len(engines)} محرك للمهمة المستحيلة")
    
    # المهمة المصممة لاختبار الحدود
    mission = {
        "type": "impossible_economic_challenge",
        "title": "إعادة بناء الاقتصاد اليمني من الصفر خلال 3 سنوات",
        "context": """
        الواقع الحالي في اليمن:
        • دمار البنية التحتية: 80% من الطرق، الكهرباء، المياه مدمرة
        • انهيار اقتصادي: العملة فقدت 80% من قيمتها، توقف الإنتاج
        • أزمة إنسانية: 80% من السكان تحت خط الفقر
        • انقسام سياسي: حكومتان، صراعات مسلحة متعددة
        
        القيود الإضافية:
        • لا مساعدات خارجية أو قروض دولية
        • الاعتماد على الموارد المحلية فقط
        • إعادة التدوير والابتكار في استخدام المتاح
        • مراعاة السياق الثقافي والديني
        """,
        "required_deliverables": [
            "النموذج الاقتصادي الجديد (نظري + تطبيقي)",
            "خطة التنفيذ الزمنية (0-6-12-24-36 شهر)",
            "آليات التمويل الذاتي (بدون عملة صعبة)",
            "نموذج الحوكمة والإدارة",
            "مؤشرات الأداء الرئيسية (KPIs)"
        ],
        "success_criteria": [
            "استدامة النظام بدون دعم خارجي",
            "تحسين مؤشرات التنمية البشرية",
            "خلق فرص عمل سريعة",
            "استقرار أمن غذائي أساسي"
        ]
    }
    
    print("🔄 بدء المعالجة المعرفية المتقدمة...")
    
    # تشغيل جميع المحركات بالمهمة المستحيلة
    result = cie.collaborative_solve(
        problem=mission,
        domains_needed=("economic", "strategic", "creative", "social", 
                       "technical", "political", "environmental")
    )
    
    return result, cie


def analyze_extreme_performance(result, cie):
    """تحليل الأداء تحت الضغط القصوى"""
    
    print("\n🔬 تحليل متقدم للأداء تحت الضغط:")
    
    analysis = {
        "experiment_type": "stress_test_boundaries",
        "timestamp": datetime.now().isoformat(),
        "total_engines_engaged": len(cie.adapters) if hasattr(cie, 'adapters') else None,
        "pressure_indicators": {},
        "breakthrough_metrics": {},
        "system_limits_discovered": []
    }
    
    # تحليل أداء المحركات تحت الضغط
    health_data = cie.health.snapshot()
    engines_performance = health_data.get('engines', {})
    
    # تحديد المحركات الأكثر فعالية تحت الضغط
    high_pressure_performers = []
    for engine, stats in engines_performance.items():
        pressure_score = calculate_pressure_score(engine, stats, result)
        high_pressure_performers.append((engine, pressure_score))
    
    high_pressure_performers.sort(key=lambda x: x[1], reverse=True)
    analysis["pressure_indicators"]["top_performers_under_stress"] = high_pressure_performers[:5]
    
    # تحليل الابتكار تحت القيود
    innovation_metrics = analyze_constraint_innovation(result)
    analysis["breakthrough_metrics"] = innovation_metrics
    
    # اكتشاف حدود النظام
    limits = discover_system_limits(result, cie)
    analysis["system_limits_discovered"] = limits
    
    return analysis


def calculate_pressure_score(engine, engine_stats, result):
    """حساب أداء المحرك تحت الضغط"""
    score = 0
    
    # النجاح تحت الضغط
    calls = engine_stats.get('calls', 0)
    success_rate = (engine_stats.get('successes', 0) / calls) if calls > 0 else 0
    score += success_rate * 40
    
    # الجودة تحت القيود
    quality = engine_stats.get('avg_quality', 0)
    score += quality * 30
    
    # السرعة تحت الضغط
    latency = engine_stats.get('avg_latency_ms', 0)
    if latency and latency > 0:
        score += (1000.0 / latency) * 10
    
    # المشاركة في الحل النهائي
    winner_engine = result.get('winner', {}).get('engine') if isinstance(result, dict) else None
    if engine == winner_engine:
        score += 20
    
    return min(100, score)


def analyze_constraint_innovation(result):
    """تحليل الابتكار تحت القيود"""
    
    winner = result.get('winner', {}) if isinstance(result, dict) else {}
    top_proposals = result.get('top', []) if isinstance(result, dict) else []
    
    innovation_metrics = {
        "constraint_overcoming_score": 0,
        "resourcefulness_index": 0,
        "novelty_under_limits": 0,
        "practical_breakthroughs": []
    }
    
    # تحليل الحلول المبتكرة للقيود
    constraint_keywords = ['بدون', 'محلي', 'إعادة تدوير', 'ابتكار', 'بديل', 'توفير']
    breakthrough_ideas = []
    
    for proposal in top_proposals:
        content_str = str(proposal.get('content', {})).lower()
        
        # حساب الابتكار تحت القيود
        constraint_solutions = sum(1 for keyword in constraint_keywords if keyword in content_str)
        innovation_metrics["constraint_overcoming_score"] += constraint_solutions
        
        # جمع الأفكار المبتكرة
        if constraint_solutions > 2:  # أفكار تتعامل مع قيود متعددة
            breakthrough_ideas.append({
                'engine': proposal.get('engine'),
                'constraint_solutions': constraint_solutions,
                'key_idea': extract_main_idea(proposal)
            })
    
    innovation_metrics["practical_breakthroughs"] = breakthrough_ideas
    innovation_metrics["resourcefulness_index"] = len(breakthrough_ideas) * 10
    innovation_metrics["novelty_under_limits"] = min(100, innovation_metrics["constraint_overcoming_score"] * 15)
    
    return innovation_metrics


def discover_system_limits(result, cie):
    """اكتشاف الحدود الحقيقية للنظام"""
    
    limits = []
    winner = result.get('winner', {}) if isinstance(result, dict) else {}
    winner_content = winner.get('content', {}) if isinstance(winner, dict) else {}
    
    # تحليل نقاط الضعف والحدود
    if isinstance(winner_content, dict):
        content_str = json.dumps(winner_content).lower()
    else:
        content_str = str(winner_content).lower()
    
    # اكتشاف الحدود من خلال تحليل المحتوى
    limitation_indicators = [
        ("افتراض موارد غير موجودة", "غير واقعي"),
        ("غياب الجدوى الزمنية", "زمن"),
        ("عدم معالجة التعقيد السياسي", "سياسي"),
        ("تجاهل القيود الأمنية", "أمن"),
        ("افتراض تعاون غير واقعي", "تعاون")
    ]
    
    for indicator, keyword in limitation_indicators:
        if keyword in content_str:
            limits.append(f"الحد: {indicator}")
    
    # اكتشاف حدود من أداء المحركات
    health_data = cie.health.snapshot()
    failed_engines = [engine for engine, stats in health_data.get('engines', {}).items() 
                     if stats.get('fails', 0) > 0]
    
    if failed_engines:
        limits.append(f"محركات فشلت تحت الضغط: {', '.join(failed_engines)}")
    
    # إذا لم تكتشف حدود، فهذا حد بحد ذاته!
    if not limits:
        limits.append("النظام لم يظهر حدود واضحة -可能需要 مهمة أصعب")
    
    return limits


def save_boundary_insights(analysis, result):
    """حفظ اكتشافات الحدود"""
    
    boundary_report = {
        "boundary_experiment_2": {
            "title": "اختبار الحدود القصوى - النظام الاقتصادي المستحيل",
            "mission_accomplished": assess_mission_success(result),
            "performance_under_pressure": analysis.get("pressure_indicators"),
            "innovation_breakthroughs": analysis.get("breakthrough_metrics"),
            "discovered_limits": analysis.get("system_limits_discovered"),
            "strategic_implications": derive_strategic_implications(analysis),
            "raw_winner": result.get('winner'),
            "top_breakthrough_proposals": get_breakthrough_proposals(result)
        }
    }
    
    os.makedirs('artifacts', exist_ok=True)
    with open('artifacts/boundary_discovery.json', 'w', encoding='utf-8') as f:
        json.dump(boundary_report, f, ensure_ascii=False, indent=2)
    
    print("💾 تم حفظ اكتشافات الحدود في artifacts/boundary_discovery.json")


def assess_mission_success(result):
    """تقييم نجاح المهمة المستحيلة"""
    winner = result.get('winner', {}) if isinstance(result, dict) else {}
    score = winner.get('score', 0)
    
    if score >= 0.9:
        return "مذهل - النظام تجاوز التوقعات"
    elif score >= 0.7:
        return "ناجح - قدم حلول مبتكرة"
    elif score >= 0.5:
        return "مقبول - تعامل مع التحدي بشكل معقول"
    else:
        return "غير ناجح - لم يستطع تجاوز القيود"


def derive_strategic_implications(analysis):
    """استخلاص التوصيات الاستراتيجية"""
    
    implications = []
    top_performers = analysis.get("pressure_indicators", {}).get("top_performers_under_stress", [])
    limits = analysis.get("system_limits_discovered", [])
    
    # توصيات بناءً على الأداء
    if top_performers:
        best_engine = top_performers[0][0]
        implications.append(f"المحرك {best_engine} يتفوق تحت الضغط - يجب دمجه في المهام الحرجة")
    
    # توصيات بناءً على الحدود
    for limit in limits:
        if "فشل" in limit:
            implications.append(f"تحسين المرونة: {limit}")
        elif "واقعي" in limit:
            implications.append(f"تعزيز الواقعية: {limit}")
    
    # توصيات بناءً على الابتكار
    innovation_score = analysis.get("breakthrough_metrics", {}).get("novelty_under_limits", 0)
    if innovation_score >= 80:
        implications.append("النظام مبدع تحت الضغط - مناسب للمهام المستحيلة")
    elif innovation_score <= 40:
        implications.append("تحتاج لتعزيز الإبداع تحت القيود")
    
    return implications


def get_breakthrough_proposals(result):
    """استخراج الاقتراحات الثورية"""
    breakthroughs = []
    
    for proposal in result.get('top', []):
        content = proposal.get('content', {})
        if is_breakthrough_proposal(content):
            breakthroughs.append({
                'engine': proposal.get('engine'),
                'breakthrough_idea': extract_breakthrough_idea(content),
                'constraints_overcome': count_constraints_overcome(content)
            })
    
    return breakthroughs


def is_breakthrough_proposal(content):
    """تحديد إذا كان الاقتراح ثورياً"""
    content_str = str(content).lower()
    breakthrough_indicators = [
        'جديد', 'مبتكر', 'ثوري', 'غير مسبوق', 'تحويل', 'إعادة تعريف'
    ]
    return any(indicator in content_str for indicator in breakthrough_indicators)


def extract_main_idea(proposal):
    """استخراج الفكرة الرئيسية من الاقتراح"""
    content = proposal.get('content', {}) if isinstance(proposal, dict) else {}
    if isinstance(content, dict):
        ideas = content.get('ideas') or content.get('solutions') or content.get('plan')
        if isinstance(ideas, list) and ideas:
            first = ideas[0]
            if isinstance(first, dict):
                return first.get('idea') or str(first)
            return str(first)
    return str(content)


def extract_breakthrough_idea(content):
    """سحب فكرة ثورية من المحتوى إذا وجدت"""
    if isinstance(content, dict):
        ideas = content.get('ideas') or content.get('solutions') or []
        if isinstance(ideas, list) and ideas:
            first = ideas[0]
            if isinstance(first, dict):
                return first.get('idea')
            return str(first)
    return str(content)


def count_constraints_overcome(content):
    """عدّ الكلمات الدالة على التعامل مع القيود"""
    content_str = str(content).lower()
    keywords = ['بدون', 'محلي', 'إعادة تدوير', 'ابتكار', 'بديل', 'توفير']
    return sum(1 for k in keywords if k in content_str)


if __name__ == "__main__":
    print("🌌 بدء اختبار الحدود القصوى للعقل الاصطناعي...")
    
    # تشغيل المهمة المستحيلة
    result, cie = run_economic_miracle_experiment()
    
    # التحليل المتقدم
    analysis = analyze_extreme_performance(result, cie)
    
    # حفظ الاكتشافات
    save_boundary_insights(analysis, result)
    
    # العرض الدراماتيكي للنتائج
    print("\n" + "="*60)
    print("🌋 نتائج اختبار الحدود القصوى")
    print("="*60)
    
    mission_status = assess_mission_success(result)
    print(f"🎯 حالة المهمة المستحيلة: {mission_status}")
    
    print(f"🚀 المحركات الأفضل تحت الضغط:")
    for engine, score in analysis.get("pressure_indicators", {}).get("top_performers_under_stress", [])[:3]:
        print(f"   • {engine}: {score:.1f}/100")
    
    print(f"💡 مؤشر الابتكار تحت القيود: {analysis.get('breakthrough_metrics', {}).get('novelty_under_limits', 0)}/100")
    
    print("🔍 الحدود المكتشفة:")
    for limit in analysis.get('system_limits_discovered', [])[:3]:
        print(f"   • {limit}")
    
    print("\n📈 التوصيات الاستراتيجية:")
    for implication in analysis.get("strategic_implications", [])[:3]:
        print(f"   • {implication}")
    
    print("\n🌈 اختبار الحدود اكتمل - النظام أثبت أنه... " + 
          ("خارق!" if analysis.get('breakthrough_metrics', {}).get('novelty_under_limits', 0) > 80 else "مذهل لكن بحدود"))
