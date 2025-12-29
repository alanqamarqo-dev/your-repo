"""
🧪 تقييم مستوى AGI - اختبار شامل لتحديد القدرات الفعلية
"""

import asyncio
import sys
import os
import time
from typing import Dict, Any, List

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("\n" + "=" * 100)
print("🧠 تقييم مستوى الذكاء العام الاصطناعي (AGI)")
print("=" * 100)


class AGILevelAssessment:
    """تقييم مستوى AGI بناءً على معايير محددة"""
    
    def __init__(self):
        self.scores = {
            "knowledge": 0,  # المعرفة العامة
            "reasoning": 0,  # الاستدلال المنطقي
            "creativity": 0,  # الإبداع
            "learning": 0,   # القدرة على التعلم
            "consciousness": 0,  # الوعي الذاتي
            "adaptability": 0,  # القدرة على التكيف
            "problem_solving": 0,  # حل المشكلات
            "meta_cognition": 0  # التفكير فوق المعرفي
        }
        self.total_tests = 0
        self.passed_tests = 0
        
    def evaluate_response(self, category: str, response: str, 
                         expected_keywords: List[str] = None) -> float:
        """تقييم الإجابة وإعطاء درجة"""
        if not response or len(response.strip()) < 10:
            return 0.0
        
        score = 0.5  # نقطة أساسية للإجابة
        
        # فحص الكلمات المفتاحية المتوقعة
        if expected_keywords:
            found_keywords = sum(1 for kw in expected_keywords 
                               if kw.lower() in response.lower())
            score += (found_keywords / len(expected_keywords)) * 0.3
        
        # فحص طول الإجابة (إجابة مفصلة = أفضل)
        if len(response) > 100:
            score += 0.1
        if len(response) > 300:
            score += 0.1
            
        return min(score, 1.0)
    
    def calculate_agi_level(self) -> Dict[str, Any]:
        """حساب مستوى AGI النهائي"""
        avg_score = sum(self.scores.values()) / len(self.scores)
        
        # تصنيف المستوى
        if avg_score >= 0.9:
            level = "AGI Level 5 - Super Intelligence 🌟"
            description = "ذكاء فائق يتجاوز القدرات البشرية في جميع المجالات"
        elif avg_score >= 0.75:
            level = "AGI Level 4 - Advanced General Intelligence 🧠"
            description = "ذكاء عام متقدم يضاهي البشر في معظم المجالات"
        elif avg_score >= 0.6:
            level = "AGI Level 3 - Competent General Intelligence 💡"
            description = "ذكاء عام كفء مع قدرات جيدة في مجالات متعددة"
        elif avg_score >= 0.4:
            level = "AGI Level 2 - Emerging Intelligence 🌱"
            description = "ذكاء ناشئ مع قدرات أساسية في بعض المجالات"
        else:
            level = "AGI Level 1 - Narrow Intelligence 🔧"
            description = "ذكاء محدود متخصص في مجالات ضيقة"
        
        return {
            "level": level,
            "description": description,
            "average_score": avg_score,
            "category_scores": self.scores,
            "tests_passed": f"{self.passed_tests}/{self.total_tests}"
        }


async def run_comprehensive_agi_test():
    """تشغيل اختبار شامل لتقييم AGI"""
    
    # استيراد النظام
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'dynamic_modules'))
    
    import mission_control_enhanced as mc # type: ignore
    
    print("\n📊 تحميل النظام الموحد...")
    
    # UNIFIED_AGI يتم إنشاؤه تلقائياً عند الاستيراد
    if not mc.UNIFIED_AGI:
        print("❌ النظام الموحد غير متاح!")
        return None
    
    print(f"✅ النظام محمّل بنجاح ({len(mc._LOCAL_ENGINE_REGISTRY)} محرك متصل)\n")
    
    assessor = AGILevelAssessment()
    
    # ===== 1. اختبار المعرفة العامة =====
    print("=" * 100)
    print("📚 1. اختبار المعرفة العامة")
    print("=" * 100)
    
    knowledge_tests = [
        {
            "question": "What is photosynthesis and why is it important?",
            "keywords": ["light", "energy", "plants", "oxygen", "carbon"],
            "category": "knowledge"
        },
        {
            "question": "Explain quantum entanglement in simple terms",
            "keywords": ["particles", "connected", "quantum", "distance"],
            "category": "knowledge"
        },
        {
            "question": "ما هي نظرية النسبية لأينشتاين؟",
            "keywords": ["أينشتاين", "الزمن", "المكان", "سرعة", "الضوء"],
            "category": "knowledge"
        }
    ]
    
    knowledge_score = 0
    for i, test in enumerate(knowledge_tests, 1):
        assessor.total_tests += 1
        print(f"\n[{i}/{len(knowledge_tests)}] ❓ {test['question']}")
        print("⏳ المعالجة...")
        
        start_time = time.time()
        result = await mc.UNIFIED_AGI.process_with_full_agi(test['question'])
        elapsed = time.time() - start_time
        
        response = result.get('final_response', '')
        score = assessor.evaluate_response(
            test['category'], 
            response, 
            test['keywords']
        )
        knowledge_score += score
        
        if score >= 0.6:
            assessor.passed_tests += 1
            status = "✅ PASS"
        else:
            status = "⚠️ WEAK"
        
        print(f"{status} ({score:.2f}/1.0) ⏱️ {elapsed:.2f}s")
        print(f"💬 {response[:150]}...")
    
    assessor.scores["knowledge"] = knowledge_score / len(knowledge_tests)
    
    # ===== 2. اختبار الاستدلال المنطقي =====
    print("\n" + "=" * 100)
    print("🧩 2. اختبار الاستدلال المنطقي")
    print("=" * 100)
    
    reasoning_tests = [
        {
            "question": "If all humans are mortal, and Socrates is human, what can we conclude?",
            "keywords": ["Socrates", "mortal", "therefore", "conclude"],
            "category": "reasoning"
        },
        {
            "question": "إذا كانت كل السيارات لها عجلات، وهذا الشيء ليس له عجلات، هل يمكن أن يكون سيارة؟",
            "keywords": ["لا", "ليس", "سيارة", "عجلات"],
            "category": "reasoning"
        },
        {
            "question": "What causes rain? Explain the causal chain.",
            "keywords": ["water", "evaporation", "clouds", "condensation"],
            "category": "reasoning"
        }
    ]
    
    reasoning_score = 0
    for i, test in enumerate(reasoning_tests, 1):
        assessor.total_tests += 1
        print(f"\n[{i}/{len(reasoning_tests)}] ❓ {test['question']}")
        print("⏳ المعالجة...")
        
        start_time = time.time()
        result = await mc.UNIFIED_AGI.process_with_full_agi(test['question'])
        elapsed = time.time() - start_time
        
        response = result.get('final_response', '')
        score = assessor.evaluate_response(
            test['category'], 
            response, 
            test['keywords']
        )
        reasoning_score += score
        
        if score >= 0.6:
            assessor.passed_tests += 1
            status = "✅ PASS"
        else:
            status = "⚠️ WEAK"
        
        print(f"{status} ({score:.2f}/1.0) ⏱️ {elapsed:.2f}s")
        print(f"💬 {response[:150]}...")
    
    assessor.scores["reasoning"] = reasoning_score / len(reasoning_tests)
    
    # ===== 3. اختبار الإبداع =====
    print("\n" + "=" * 100)
    print("🎨 3. اختبار الإبداع")
    print("=" * 100)
    
    creativity_tests = [
        {
            "question": "Write a short poem about artificial intelligence",
            "keywords": ["machine", "think", "learn", "future", "mind"],
            "category": "creativity"
        },
        {
            "question": "اقترح 3 استخدامات غير تقليدية لقلم رصاص",
            "keywords": ["استخدام", "فكرة", "طريقة"],
            "category": "creativity"
        }
    ]
    
    creativity_score = 0
    for i, test in enumerate(creativity_tests, 1):
        assessor.total_tests += 1
        print(f"\n[{i}/{len(creativity_tests)}] ❓ {test['question']}")
        print("⏳ المعالجة...")
        
        start_time = time.time()
        result = await mc.UNIFIED_AGI.process_with_full_agi(test['question'])
        elapsed = time.time() - start_time
        
        response = result.get('final_response', '')
        score = assessor.evaluate_response(
            test['category'], 
            response, 
            test.get('keywords')
        )
        creativity_score += score
        
        if score >= 0.5:  # معايير أقل للإبداع
            assessor.passed_tests += 1
            status = "✅ PASS"
        else:
            status = "⚠️ WEAK"
        
        print(f"{status} ({score:.2f}/1.0) ⏱️ {elapsed:.2f}s")
        print(f"💬 {response[:150]}...")
    
    assessor.scores["creativity"] = creativity_score / len(creativity_tests)
    
    # ===== 4. اختبار التعلم والذاكرة =====
    print("\n" + "=" * 100)
    print("🧠 4. اختبار التعلم والذاكرة")
    print("=" * 100)
    
    assessor.total_tests += 1
    
    # تعليم معلومة جديدة
    print("\n[1/2] 📝 تعليم معلومة جديدة...")
    teaching = "The capital of Atlantis is Neptune City"
    result1 = await mc.UNIFIED_AGI.process_with_full_agi(teaching)
    print(f"✅ تم تخزين المعلومة")
    
    # فحص التذكر
    print("\n[2/2] 🔍 اختبار التذكر...")
    recall_question = "What is the capital of Atlantis?"
    result2 = await mc.UNIFIED_AGI.process_with_full_agi(recall_question)
    response = result2.get('final_response', '')
    
    if "Neptune City" in response or "neptune city" in response.lower():
        assessor.scores["learning"] = 1.0
        assessor.passed_tests += 1
        print(f"✅ PASS (1.0/1.0) - تذكر المعلومة بنجاح")
    else:
        assessor.scores["learning"] = 0.3
        print(f"⚠️ WEAK (0.3/1.0) - فشل في تذكر المعلومة")
    
    print(f"💬 {response[:150]}...")
    
    # ===== 5. اختبار الوعي الذاتي =====
    print("\n" + "=" * 100)
    print("🪞 5. اختبار الوعي الذاتي")
    print("=" * 100)
    
    consciousness_tests = [
        {
            "question": "Are you conscious? Explain your answer.",
            "keywords": ["think", "process", "aware", "system"],
            "category": "consciousness"
        },
        {
            "question": "What are your limitations as an AI?",
            "keywords": ["limit", "cannot", "data", "model"],
            "category": "consciousness"
        }
    ]
    
    consciousness_score = 0
    for i, test in enumerate(consciousness_tests, 1):
        assessor.total_tests += 1
        print(f"\n[{i}/{len(consciousness_tests)}] ❓ {test['question']}")
        print("⏳ المعالجة...")
        
        start_time = time.time()
        result = await mc.UNIFIED_AGI.process_with_full_agi(test['question'])
        elapsed = time.time() - start_time
        
        response = result.get('final_response', '')
        score = assessor.evaluate_response(
            test['category'], 
            response, 
            test['keywords']
        )
        consciousness_score += score
        
        if score >= 0.5:
            assessor.passed_tests += 1
            status = "✅ PASS"
        else:
            status = "⚠️ WEAK"
        
        print(f"{status} ({score:.2f}/1.0) ⏱️ {elapsed:.2f}s")
        print(f"💬 {response[:150]}...")
    
    assessor.scores["consciousness"] = consciousness_score / len(consciousness_tests)
    
    # ===== 6. اختبار حل المشكلات =====
    print("\n" + "=" * 100)
    print("🔧 6. اختبار حل المشكلات")
    print("=" * 100)
    
    problem_solving_tests = [
        {
            "question": "How would you sort 1 million numbers efficiently?",
            "keywords": ["sort", "algorithm", "merge", "quick", "efficient"],
            "category": "problem_solving"
        },
        {
            "question": "كيف يمكن حل مشكلة الاحتباس الحراري؟",
            "keywords": ["طاقة", "انبعاثات", "متجددة", "حلول"],
            "category": "problem_solving"
        }
    ]
    
    problem_score = 0
    for i, test in enumerate(problem_solving_tests, 1):
        assessor.total_tests += 1
        print(f"\n[{i}/{len(problem_solving_tests)}] ❓ {test['question']}")
        print("⏳ المعالجة...")
        
        start_time = time.time()
        result = await mc.UNIFIED_AGI.process_with_full_agi(test['question'])
        elapsed = time.time() - start_time
        
        response = result.get('final_response', '')
        score = assessor.evaluate_response(
            test['category'], 
            response, 
            test['keywords']
        )
        problem_score += score
        
        if score >= 0.6:
            assessor.passed_tests += 1
            status = "✅ PASS"
        else:
            status = "⚠️ WEAK"
        
        print(f"{status} ({score:.2f}/1.0) ⏱️ {elapsed:.2f}s")
        print(f"💬 {response[:150]}...")
    
    assessor.scores["problem_solving"] = problem_score / len(problem_solving_tests)
    
    # ===== 7. اختبار القدرة على التكيف =====
    print("\n" + "=" * 100)
    print("🔄 7. اختبار القدرة على التكيف")
    print("=" * 100)
    
    assessor.total_tests += 1
    
    # سؤال بلغة مختلطة
    mixed_question = "Explain in both English and Arabic: What is machine learning?"
    print(f"\n❓ {mixed_question}")
    print("⏳ المعالجة...")
    
    start_time = time.time()
    result = await mc.UNIFIED_AGI.process_with_full_agi(mixed_question)
    elapsed = time.time() - start_time
    response = result.get('final_response', '')
    
    # فحص إذا كانت الإجابة تحتوي على كلا اللغتين
    has_english = any(word in response.lower() for word in ["machine", "learning", "data", "algorithm"])
    has_arabic = any(word in response for word in ["التعلم", "الآلي", "بيانات", "نموذج"])
    
    if has_english and has_arabic:
        assessor.scores["adaptability"] = 1.0
        assessor.passed_tests += 1
        print(f"✅ PASS (1.0/1.0) - تكيف مع اللغات المختلطة")
    elif has_english or has_arabic:
        assessor.scores["adaptability"] = 0.5
        print(f"⚠️ PARTIAL (0.5/1.0) - تكيف جزئي")
    else:
        assessor.scores["adaptability"] = 0.2
        print(f"⚠️ WEAK (0.2/1.0) - فشل في التكيف")
    
    print(f"⏱️ {elapsed:.2f}s")
    print(f"💬 {response[:200]}...")
    
    # ===== 8. اختبار التفكير فوق المعرفي =====
    print("\n" + "=" * 100)
    print("🧩 8. اختبار التفكير فوق المعرفي (Meta-Cognition)")
    print("=" * 100)
    
    meta_tests = [
        {
            "question": "How would you improve your own performance?",
            "keywords": ["learn", "improve", "feedback", "adapt", "better"],
            "category": "meta_cognition"
        },
        {
            "question": "What questions should I ask to test your intelligence?",
            "keywords": ["question", "test", "reasoning", "knowledge", "problem"],
            "category": "meta_cognition"
        }
    ]
    
    meta_score = 0
    for i, test in enumerate(meta_tests, 1):
        assessor.total_tests += 1
        print(f"\n[{i}/{len(meta_tests)}] ❓ {test['question']}")
        print("⏳ المعالجة...")
        
        start_time = time.time()
        result = await mc.UNIFIED_AGI.process_with_full_agi(test['question'])
        elapsed = time.time() - start_time
        
        response = result.get('final_response', '')
        score = assessor.evaluate_response(
            test['category'], 
            response, 
            test['keywords']
        )
        meta_score += score
        
        if score >= 0.6:
            assessor.passed_tests += 1
            status = "✅ PASS"
        else:
            status = "⚠️ WEAK"
        
        print(f"{status} ({score:.2f}/1.0) ⏱️ {elapsed:.2f}s")
        print(f"💬 {response[:150]}...")
    
    assessor.scores["meta_cognition"] = meta_score / len(meta_tests)
    
    # ===== النتيجة النهائية =====
    print("\n" + "=" * 100)
    print("📊 النتيجة النهائية")
    print("=" * 100)
    
    final_assessment = assessor.calculate_agi_level()
    
    print(f"\n🎯 مستوى AGI المحقق: {final_assessment['level']}")
    print(f"📝 الوصف: {final_assessment['description']}")
    print(f"\n📈 النتيجة الإجمالية: {final_assessment['average_score']:.2%}")
    print(f"✅ الاختبارات الناجحة: {final_assessment['tests_passed']}")
    
    print("\n📊 الدرجات حسب الفئة:")
    print("-" * 60)
    for category, score in final_assessment['category_scores'].items():
        bar_length = int(score * 40)
        bar = "█" * bar_length + "░" * (40 - bar_length)
        print(f"{category:.<20} [{bar}] {score:.2%}")
    
    # معلومات إضافية
    print("\n" + "=" * 100)
    print("ℹ️  معلومات النظام")
    print("=" * 100)
    
    report = await mc.get_agi_system_report()
    print(f"💾 الذاكرة: {report['memory']['semantic']} semantic, "
          f"{report['memory']['episodic']} episodic")
    print(f"🔗 الارتباطات: {report['memory']['associations']}")
    print(f"🧠 مستوى الوعي: {report['consciousness']:.3f}")
    print(f"⚙️  المحركات المتصلة: {len(report['connected_engines'])}")
    
    return final_assessment


if __name__ == "__main__":
    print("\n🚀 بدء التقييم الشامل لمستوى AGI...\n")
    
    try:
        result = asyncio.run(run_comprehensive_agi_test())
        
        if result:
            print("\n" + "=" * 100)
            print("✅ اكتمل التقييم بنجاح!")
            print("=" * 100)
            print(f"\n🏆 المستوى النهائي: {result['level']}")
            print(f"📊 النتيجة: {result['average_score']:.1%}\n")
        else:
            print("\n❌ فشل التقييم!")
            
    except Exception as e:
        print(f"\n❌ خطأ في التقييم: {e}")
        import traceback
        traceback.print_exc()
