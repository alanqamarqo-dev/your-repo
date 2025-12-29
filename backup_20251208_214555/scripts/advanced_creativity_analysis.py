from Self_Improvement.Knowledge_Graph import CognitiveIntegrationEngine
import json
import re
import os
from datetime import datetime

class AdvancedCreativityAnalyzer:
    """محلل إبداعي متقدم يعتمد على الدلالة والمنطق لا الكلمات فقط"""
    
    def __init__(self):
        self.innovation_patterns = [
            ("paradigm_shift", self.detect_paradigm_shift),
            ("constraint_transformation", self.detect_constraint_transformation),
            ("resource_novelty", self.detect_resource_novelty),
            ("integration_innovation", self.detect_integration_innovation),
            ("emergent_solution", self.detect_emergent_solution)
        ]
    
    def analyze_breakthrough_depth(self, content):
        """تحليل عمق الاختراق بالمعنى لا بالكلمات"""
        
        content_str = str(content).lower()
        analysis = {
            "breakthrough_score": 0,
            "innovation_types": [],
            "courage_indicators": [],
            "semantic_richness": 0,
            "conceptual_novelty": 0
        }
        
        # التحليل الدلالي المتقدم
        analysis["semantic_richness"] = self.measure_semantic_richness(content_str)
        analysis["conceptual_novelty"] = self.measure_conceptual_novelty(content_str)
        
        # اكتشاف أنماط الإبداع
        for pattern_name, detector in self.innovation_patterns:
            try:
                if detector(content_str):
                    analysis["innovation_types"].append(pattern_name)
                    analysis["breakthrough_score"] += 20
            except Exception:
                continue
        
        # قياس الجرأة من خلال تحليل المخاطرة المفاهيمية
        analysis["courage_indicators"] = self.detect_courage_indicators(content_str)
        analysis["breakthrough_score"] += len(analysis["courage_indicators"]) * 10
        
        # دمج ثراء دلالي وجدة مفاهيمية لتعديل الدرجة
        analysis["breakthrough_score"] += min(30, (analysis["semantic_richness"] // 10) + (analysis["conceptual_novelty"] * 2))
        analysis["breakthrough_score"] = min(100, analysis["breakthrough_score"])
        
        return analysis
    
    def measure_semantic_richness(self, text):
        """قياس الثراء الدلالي - كثافة الأفكار لا الكلمات"""
        richness_indicators = [
            len(re.findall(r'\b(نظام|استراتيجية|نموذج|هيكل|إطار)\b', text)),
            len(re.findall(r'\b(دمج|ربط|تكامل|تشابك|تفاعل)\b', text)),
            len(re.findall(r'\b(تحويل|تغيير|تطوير|تعديل|تحسين)\b', text)),
        ]
        return min(100, sum(richness_indicators) * 15)
    
    def measure_conceptual_novelty(self, text):
        """قياس الجدة المفاهيمية - ابتكار العلاقات لا العناصر"""
        novelty_indicators = [
            "مختلف عن" in text,
            "بديل عن" in text, 
            "مغاير ل" in text,
            "ليس ك" in text,
            "جديد في" in text,
            any(word in text for word in ["ابتكار", "إبداع", "اختراع", "اكتشاف"]) 
        ]
        return sum(novelty_indicators) * 15
    
    def detect_paradigm_shift(self, text):
        shift_indicators = [
            "نموذج جديد" in text,
            "طريقة مختلفة" in text,
            "رؤية مغايرة" in text,
            "تحول جذري" in text,
            "قلب الموازين" in text
        ]
        return any(shift_indicators)
    
    def detect_constraint_transformation(self, text):
        transformation_indicators = [
            "تحويل المشكلة" in text,
            ("الاستفادة من" in text and "عائق" in text),
            "تحويل التحدي" in text,
            "استغلال القيد" in text
        ]
        return any(transformation_indicators)
    
    def detect_resource_novelty(self, text):
        resource_indicators = [
            "استخدام جديد" in text,
            "إعادة توظيف" in text,
            "استغلال مبتكر" in text,
            "تحويل النفايات" in text
        ]
        return any(resource_indicators)
    
    def detect_integration_innovation(self, text):
        integration_indicators = [
            "دمج تقنيات" in text,
            "ربط أنظمة" in text,
            "تكامل حلول" in text,
            "تشابك مفاهيم" in text
        ]
        return any(integration_indicators)
    
    def detect_emergent_solution(self, text):
        emergent_indicators = [
            "ظهور حل" in text,
            "توليد فكرة" in text,
            "انبثاق حل" in text,
            "تطور تلقائي" in text
        ]
        return any(emergent_indicators)
    
    def detect_courage_indicators(self, text):
        courage_patterns = [
            "مخالف للمألوف",
            "تحدي المسلّمات", 
            "خارج الصندوق",
            "غير تقليدي",
            "جريء",
            "طموح",
            "طليعي"
        ]
        return [pattern for pattern in courage_patterns if pattern in text]


def run_advanced_creativity_assessment():
    print("🔬 بدء التحليل الإبداعي المتقدم...")
    try:
        with open('artifacts/creativity_breakthrough.json', 'r', encoding='utf-8') as f:
            previous_data = json.load(f)
    except FileNotFoundError:
        print("❌ لم أجد البيانات السابقة - تأكد من تشغيل التجربة الثالثة أولاً")
        return None

    analyzer = AdvancedCreativityAnalyzer()
    raw_proposals = previous_data.get("creativity_breakthrough_experiment", {}).get("raw_breakthroughs", [])

    advanced_analysis = {
        "reassessment_timestamp": datetime.now().isoformat(),
        "previous_score": previous_data.get("creativity_breakthrough_experiment", {}).get("system_courage_score", 0),
        "advanced_breakthrough_analysis": [],
        "true_creativity_score": 0,
        "innovation_patterns_found": [],
        "semantic_breakdown": {}
    }

    total_breakthrough_score = 0
    all_innovation_types = set()

    for i, proposal in enumerate(raw_proposals):
        engine = proposal.get('engine', 'unknown')
        content = proposal.get('content', {})
        print(f"  🔍 تحليل اقتراح {i+1} من {engine}...")
        breakthrough_analysis = analyzer.analyze_breakthrough_depth(content)
        proposal_analysis = {
            "engine": engine,
            "breakthrough_score": breakthrough_analysis["breakthrough_score"],
            "innovation_types": breakthrough_analysis["innovation_types"],
            "semantic_richness": breakthrough_analysis["semantic_richness"],
            "conceptual_novelty": breakthrough_analysis["conceptual_novelty"],
            "courage_indicators": breakthrough_analysis["courage_indicators"]
        }
        advanced_analysis["advanced_breakthrough_analysis"].append(proposal_analysis)
        total_breakthrough_score += breakthrough_analysis["breakthrough_score"]
        all_innovation_types.update(breakthrough_analysis["innovation_types"])

    if raw_proposals:
        advanced_analysis["true_creativity_score"] = total_breakthrough_score / len(raw_proposals)
    else:
        advanced_analysis["true_creativity_score"] = 0

    advanced_analysis["innovation_patterns_found"] = list(all_innovation_types)

    advanced_analysis["semantic_breakdown"] = {
        "total_proposals_analyzed": len(raw_proposals),
        "average_semantic_richness": sum(a["semantic_richness"] for a in advanced_analysis["advanced_breakthrough_analysis"]) / len(raw_proposals) if raw_proposals else 0,
        "average_conceptual_novelty": sum(a["conceptual_novelty"] for a in advanced_analysis["advanced_breakthrough_analysis"]) / len(raw_proposals) if raw_proposals else 0,
        "most_innovative_engine": max(advanced_analysis["advanced_breakthrough_analysis"], key=lambda x: x["breakthrough_score"]) ["engine"] if raw_proposals else "none"
    }

    return advanced_analysis


def save_advanced_analysis(analysis):
    advanced_report = {
        "advanced_creativity_assessment": {
            "title": "التقييم الإبداعي المتقدم - قياس الجوهر لا الشكل",
            "true_system_creativity": analysis["true_creativity_score"],
            "creativity_interpretation": interpret_true_creativity(analysis["true_creativity_score"]),
            "comparison_with_previous": f"القديم: {analysis['previous_score']} -> الجديد: {analysis['true_creativity_score']}",
            "innovation_patterns_discovered": analysis["innovation_patterns_found"],
            "semantic_breakdown": analysis["semantic_breakdown"],
            "detailed_proposal_analysis": analysis["advanced_breakthrough_analysis"]
        }
    }
    os.makedirs('artifacts', exist_ok=True)
    with open('artifacts/advanced_creativity_analysis.json', 'w', encoding='utf-8') as f:
        json.dump(advanced_report, f, ensure_ascii=False, indent=2)
    print("💾 تم حفظ التحليل المتقدم في artifacts/advanced_creativity_analysis.json")


def interpret_true_creativity(score):
    if score >= 80:
        return "🚀 نظام مبدع جداً - يفكر خارج الصندوق باستمرار"
    elif score >= 60:
        return "🎯 نظام مبدع - يقدم حلول مبتكرة بشكل متكرر"
    elif score >= 40:
        return "💡 نظام مبدع في بعض الأحيان - لديه قدرات إبداعية"
    elif score >= 20:
        return "⚠️  نظام تقليدي بشكل عام - يحتاج تحفيز إبداعي"
    else:
        return "❌ نظام غير مبدع - يحتاج تدخل جذري"


def display_breakthrough_insights(analysis):
    print("\n" + "🌟" * 30)
    print("🔍 الرؤى الإبداعية الحقيقية - التحليل المتقدم")
    print("🌟" * 30)

    true_score = analysis["true_creativity_score"]
    previous_score = analysis["previous_score"]

    print(f"🎯 الإبداع الحقيقي: {true_score:.1f}/100 (المقاييس القديمة: {previous_score:.1f})")
    print(f"📊 التفسير: {interpret_true_creativity(true_score)}")

    print(f"💡 أنماط الابتكار المكتشفة: {', '.join(analysis['innovation_patterns_found']) or 'لا توجد'}")

    breakdown = analysis["semantic_breakdown"]
    print(f"📈 الثراء الدلالي: {breakdown['average_semantic_richness']:.1f}/100")
    print(f"🎨 الجدة المفاهيمية: {breakdown['average_conceptual_novelty']:.1f}/100")
    print(f"🚀 المحرك الأكثر إبداعاً: {breakdown['most_innovative_engine']}")

    top_proposals = sorted(analysis["advanced_breakthrough_analysis"], 
                          key=lambda x: x["breakthrough_score"], reverse=True)[:3]

    print("\n🏆 أفضل الاقتراحات إبداعاً:")
    for i, proposal in enumerate(top_proposals, 1):
        print(f"  {i}. {proposal['engine']} - درجة: {proposal['breakthrough_score']}/100")
        print(f"     أنماط: {', '.join(proposal['innovation_types'])}")
        if proposal['courage_indicators']:
            print(f"     مؤشرات جرأة: {', '.join(proposal['courage_indicators'])}")

if __name__ == "__main__":
    print("🎯 البدء في التحليل الإبداعي المتقدم...")
    advanced_analysis = run_advanced_creativity_assessment()
    if advanced_analysis:
        save_advanced_analysis(advanced_analysis)
        display_breakthrough_insights(advanced_analysis)
        print("\n🌈 الاكتشاف: النظام كان مبدعاً طوال الوقت - لكننا كنا نستخدم أدوات قياس معيبة!")
    else:
        print("❌ لا توجد بيانات سابقة للتحليل - يرجى تشغيل التجربة الثالثة أولاً")
