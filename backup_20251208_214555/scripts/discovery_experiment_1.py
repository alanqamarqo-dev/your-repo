from Self_Improvement.Knowledge_Graph import CognitiveIntegrationEngine, KnowledgeNetwork
import json
from datetime import datetime


def run_education_system_experiment():
    print("🎯 بدء التجربة الاستكشافية: نظام التعليم المستقبلي لليمن")
    
    # تهيئة المحرك المعرفي
    cie = CognitiveIntegrationEngine()
    engines = cie.connect_engines()
    print(f"✅ المحركات الجاهزة: {len(engines)} محرك")
    
    # المهمة الاستكشافية
    task = {
        "type": "complex_strategic_design",
        "title": "تصميم نظام تعليمي مستقبلي لليمن 2030",
        "description": """
        المطلوب: تصميم نظام تعليمي متكامل لليمن يحقق:
        1️⃣ الجمع بين الأصالة الإسلامية والحداثة التقنية
        2️⃣ مراعاة الظروف الصعبة (حرب، فقر، بنية تحتية محدودة)
        3️⃣ إعداد جيل قادر على إعادة بناء اليمن
        4️⃣ استغلال التقنية لتخطي العقبات الجغرافية
        
        نريد رؤية استراتيجية متكاملة تشمل:
        - المناهج الدراسية
        - نظام التدريس
        - البنية التحتية
        - التمويل المستدام
        - مؤشرات قياس النجاح
        """,
        "constraints": [
            "ميزانية واقعية",
            "مراعاة الثقافة اليمنية", 
            "قابلية التنفيذ في المناطق النائية",
            "الاستدامة طويلة المدى"
        ],
        "expected_output": "استراتيجية متكاملة مع خطة تنفيذ مرحلية"
    }
    
    print("📝 بدء المعالجة المعرفية المتكاملة...")
    
    # تشغيل المحركات المعرفية
    result = cie.collaborative_solve(
        problem=task,
        domains_needed=("strategic", "social", "creative", "analytic", "policy")
    )
    
    return result, cie


def analyze_discovery_results(result, cie):
    """تحليل نتائج الاكتشاف"""
    print("\n🔍 تحليل النتائج الاستكشافية:")
    
    analysis = {
        "experiment_timestamp": datetime.now().isoformat(),
        "engines_used": len(cie.adapters) if hasattr(cie, 'adapters') else None,
        "winner_engine": result.get('winner', {}).get('engine') if isinstance(result, dict) else None,
        "top_proposals": [],
        "interaction_patterns": {},
        "innovation_metrics": {}
    }
    
    # تحليل الاقتراحات العليا
    for i, proposal in enumerate((result.get('top', []) if isinstance(result, dict) else [])[:3]):
        analysis["top_proposals"].append({
            "rank": i+1,
            "engine": proposal.get('engine'),
            "content_type": str(type(proposal.get('content'))),
            "key_ideas": extract_key_ideas(proposal)
        })
    
    # تحليل أنماط التفاعل
    if hasattr(cie, 'health'):
        try:
            health_data = cie.health.snapshot()
            analysis["interaction_patterns"] = {
                "most_active_engines": sorted(
                    health_data['engines'].items(), 
                    key=lambda x: x[1]['calls'], 
                    reverse=True
                )[:5]
            }
        except Exception:
            analysis["interaction_patterns"] = {}
    
    # تقييم الابتكار
    analysis["innovation_metrics"] = {
        "diversity_of_solutions": len(set(p.get('engine') for p in (result.get('top', []) if isinstance(result, dict) else []))),
        "content_richness": assess_content_richness(result),
        "strategic_depth": assess_strategic_depth(result)
    }
    
    return analysis


def extract_key_ideas(proposal):
    """استخراج الأفكار الرئيسية من الاقتراح"""
    content = proposal.get('content', {}) if isinstance(proposal, dict) else {}
    ideas = []
    
    if isinstance(content, dict):
        # البحث في الهياكل المختلفة للأفكار
        for key in ['ideas', 'solutions', 'strategies', 'plan']:
            if key in content:
                ideas.extend(content[key] if isinstance(content[key], list) else [content[key]])
    
    return ideas[:3]  # أول 3 أفكار فقط


def assess_content_richness(result):
    """تقييم ثراء المحتوى"""
    top_proposals = result.get('top', []) if isinstance(result, dict) else []
    unique_engines = len(set(p.get('engine') for p in top_proposals))
    total_ideas = sum(len(extract_key_ideas(p)) for p in top_proposals)
    
    return {
        "unique_engines": unique_engines,
        "total_ideas": total_ideas,
        "richness_score": min(10, unique_engines * 2 + total_ideas)
    }


def assess_strategic_depth(result):
    """تقييم العمق الاستراتيجي"""
    winner = result.get('winner', {}) if isinstance(result, dict) else {}
    content = winner.get('content', {}) if isinstance(winner, dict) else {}
    
    depth_indicators = [
        'long_term' in str(content),
        'phased' in str(content), 
        'sustainable' in str(content),
        'metrics' in str(content),
        'implementation' in str(content)
    ]
    
    return {
        "strategic_indicators": sum(depth_indicators),
        "depth_score": sum(depth_indicators) * 2
    }


def save_discovery_insights(analysis, result):
    """حفظ الرؤى الاستكشافية"""
    
    insights = {
        "experiment_1": {
            "title": "نظام التعليم المستقبلي لليمن",
            "analysis": analysis,
            "raw_winner": result.get('winner') if isinstance(result, dict) else None,
            "top_3_proposals": (result.get('top', []) if isinstance(result, dict) else [])[:3],
            "key_discoveries": extract_key_discoveries(analysis, result)
        }
    }
    
    # حفظ في ملف الاكتشافات
    import os
    os.makedirs('artifacts', exist_ok=True)
    with open('artifacts/discovery_insights.json', 'w', encoding='utf-8') as f:
        json.dump(insights, f, ensure_ascii=False, indent=2)
    
    print("💾 تم حفظ الرؤى الاستكشافية في artifacts/discovery_insights.json")


def extract_key_discoveries(analysis, result):
    """استخراج الاكتشافات الرئيسية"""
    discoveries = []
    
    # اكتشاف أنماط التفاعل
    interaction_patterns = analysis.get('interaction_patterns', {})
    most_active = interaction_patterns.get('most_active_engines', [])
    
    if most_active:
        try:
            discoveries.append(f"المحرك الأكثر نشاطاً: {most_active[0][0]} ({most_active[0][1]['calls']} استدعاء)")
        except Exception:
            pass
    
    # اكتشاف التنوع
    diversity = analysis['innovation_metrics']['diversity_of_solutions'] if 'innovation_metrics' in analysis else None
    if diversity is not None:
        discoveries.append(f"تنوع الحلول: {diversity} محرك مختلف قدموا حلولاً")
    
    # اكتشاف الابتكار
    richness = analysis.get('innovation_metrics', {}).get('content_richness', {}).get('richness_score')
    if richness is not None:
        discoveries.append(f"مستوى الثراء الفكري: {richness}/10")
    
    # اكتشاف الفائز
    winner = analysis.get('winner_engine')
    if winner:
        discoveries.append(f"المحرك الفائز: {winner} - يظهر تفوق في هذا النوع من المهام")
    
    return discoveries


if __name__ == "__main__":
    print("🌍 بدء الرحلة الاستكشافية لنظام AGI...")
    
    # تشغيل التجربة
    result, cie = run_education_system_experiment()
    
    # تحليل النتائج
    analysis = analyze_discovery_results(result, cie)
    
    # حفظ الرؤى
    save_discovery_insights(analysis, result)
    
    # عرض الملخص
    print("\n" + "="*50)
    print("🎉 الملخص الاستكشافي:")
    print("="*50)
    
    for discovery in analysis.get('key_discoveries', []):
        print(f"🔍 {discovery}")
    
    print(f"\n📊 تقييم الابتكار: {analysis.get('innovation_metrics', {}).get('content_richness', {}).get('richness_score', 'N/A')}/10")
    print(f"🏆 المحرك الفائز: {analysis.get('winner_engine', 'غير محدد')}")
    print(f"🔄 تفاعل المحركات: {analysis.get('innovation_metrics', {}).get('diversity_of_solutions', 'N/A')} محرك مختلف")
    
    print("\n✨ الرحلة الاستكشافية الأولى اكتملت!")
