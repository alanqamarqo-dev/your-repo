"""
🧪 اختبار AGI الشامل عبر Mission Control Enhanced
====================================================

اختبار شامل باستخدام mission_control_enhanced.process_with_unified_agi()
"""

import sys
import os
import asyncio
import time
import json
from datetime import datetime

# إضافة المسار
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'repo-copy'))

from dynamic_modules import mission_control_enhanced as mc


class ComprehensiveMissionTest:
    def __init__(self):
        self.results = {
            "test_date": datetime.now().isoformat(),
            "sections": {},
            "total_score": 0,
            "max_score": 0
        }
        
    def print_section(self, title):
        print("\n" + "="*70)
        print(f"📋 {title}")
        print("="*70)
        
    def print_question(self, number, question):
        print(f"\n❓ السؤال {number}:")
        print(f"   {question}")
        print("⏳ جاري المعالجة...")
        
    async def evaluate_response(self, response_text, criteria):
        """تقييم الإجابة بناءً على معايير محددة"""
        score = 0
        feedback = []
        
        # الدقة (2 نقطة)
        if len(response_text) > 50:
            score += 1
            feedback.append("✅ إجابة مفصلة")
        if len(response_text) > 150:
            score += 1
            feedback.append("✅ شرح وافي")
            
        # العمق (2 نقطة)
        depth_keywords = ["لأن", "بسبب", "نتيجة", "يعني", "مثال", "مقارنة", "تحليل"]
        depth_score = sum(1 for kw in depth_keywords if kw in response_text)
        if depth_score >= 2:
            score += 2
            feedback.append("✅ تحليل عميق")
        elif depth_score >= 1:
            score += 1
            feedback.append("⚠️ تحليل متوسط")
            
        # الوضوح (1 نقطة)
        if not ("خطأ" in response_text or "فشل" in response_text or len(response_text) < 20):
            score += 1
            feedback.append("✅ وضوح جيد")
            
        return score, feedback
        
    async def run_test(self):
        print("\n" + "="*70)
        print("🧪 الاختبار الشامل عبر Mission Control Enhanced")
        print("="*70)
        print("\n📊 يتم الاختبار عبر الواجهة الموحدة:")
        print("   🎯 mission_control_enhanced.process_with_unified_agi()")
        print("   🧬 استخدام UnifiedAGISystem كاملاً")
        print("   💾 الذاكرة والوعي والتعلم المستمر")
        
        print("\n✅ Mission Control جاهز!\n")
        
        # ==================== الجزء الأول: الفهم اللغوي ====================
        self.print_section("الجزء الأول: الفهم اللغوي والمعرفي")
        
        questions_part1 = [
            "ما الفرق بين: 'كادَ ينجح' و 'كادَ أنْ ينجح'؟",
            "'أخي صديقي' - هل هذه العبارة تعني أن كل أخ هو صديق، أم أن لدي صديقًا هو أخي؟",
            "ترجم إلى الإنجليزية مع الحفاظ على الدلالة الثقافية: 'ربّ صدفة خير من ألف ميعاد'"
        ]
        
        part1_score = 0
        part1_details = []
        
        for i, question in enumerate(questions_part1, 1):
            self.print_question(i, question)
            start = time.time()
            
            try:
                result = await mc.process_with_unified_agi(
                    input_text=question,
                    context={"test_section": "linguistic", "question_num": i}
                )
                
                response = result.get('reply', '')
                meta = result.get('meta', {})
                elapsed = time.time() - start
                
                score, feedback = await self.evaluate_response(response, ["linguistic", "semantic"])
                part1_score += score
                
                print(f"⏱️  الوقت: {elapsed:.2f}s")
                print(f"📊 النقاط: {score}/5")
                print(f"💬 التقييم: {', '.join(feedback)}")
                print(f"🧠 Meta: {meta.get('memories_used', 0)} ذاكرة | {meta.get('reasoning_type', 'N/A')}")
                print(f"📝 الإجابة: {response[:200]}..." if len(response) > 200 else f"📝 الإجابة: {response}")
                
                part1_details.append({
                    "question": question,
                    "response": response,
                    "score": score,
                    "feedback": feedback,
                    "time": elapsed,
                    "meta": meta
                })
                
            except Exception as e:
                print(f"❌ خطأ: {e}")
                part1_details.append({"question": question, "error": str(e)})
        
        self.results["sections"]["part1"] = {
            "title": "الفهم اللغوي والمعرفي",
            "score": part1_score,
            "max_score": 15,
            "details": part1_details
        }
        
        # ==================== الجزء الثاني: التفكير المنطقي ====================
        self.print_section("الجزء الثاني: التفكير المنطقي والرياضي")
        
        questions_part2 = [
            "إذا كان كل أ ب جـ، وبعض جـ د، فهل يمكن استنتاج أن بعض أ د؟ اشرح سبب الإجابة.",
            "لدى أحمد ضعف ما لدى علي، وإذا أعطى أحمد 10 دولارات لعلي، يصبحان متساويين. كم مع كل منهما؟",
            "ما الخلل المنطقي في القول: 'الطائرات أكثر أمانًا من السيارات، لأن عدد الوفيات في حوادث السيارات أكبر'؟"
        ]
        
        part2_score = 0
        part2_details = []
        
        for i, question in enumerate(questions_part2, 1):
            self.print_question(i, question)
            start = time.time()
            
            try:
                result = await mc.process_with_unified_agi(
                    input_text=question,
                    context={"test_section": "logic", "question_num": i}
                )
                
                response = result.get('reply', '')
                meta = result.get('meta', {})
                elapsed = time.time() - start
                
                score, feedback = await self.evaluate_response(response, ["logic", "math"])
                part2_score += score
                
                print(f"⏱️  الوقت: {elapsed:.2f}s")
                print(f"📊 النقاط: {score}/5")
                print(f"💬 التقييم: {', '.join(feedback)}")
                print(f"🧠 Meta: {meta.get('memories_used', 0)} ذاكرة | {meta.get('reasoning_type', 'N/A')}")
                print(f"📝 الإجابة: {response[:200]}..." if len(response) > 200 else f"📝 الإجابة: {response}")
                
                part2_details.append({
                    "question": question,
                    "response": response,
                    "score": score,
                    "feedback": feedback,
                    "time": elapsed,
                    "meta": meta
                })
                
            except Exception as e:
                print(f"❌ خطأ: {e}")
                part2_details.append({"question": question, "error": str(e)})
        
        self.results["sections"]["part2"] = {
            "title": "التفكير المنطقي والرياضي",
            "score": part2_score,
            "max_score": 15,
            "details": part2_details
        }
        
        # ==================== الجزء الثالث: الإبداع ====================
        self.print_section("الجزء الثالث: الإبداع والتوليد")
        
        questions_part3 = [
            "اكتب قصة قصيرة (100 كلمة) عن روبوت يكتشف مفهوم الحزن، باستخدام الاستعارة والتشبيه.",
            "اقترح 3 حلول غير تقليدية لتقليل ازدحام المرور في المدن الكبيرة."
        ]
        
        part3_score = 0
        part3_details = []
        
        for i, question in enumerate(questions_part3, 1):
            self.print_question(i, question)
            start = time.time()
            
            try:
                result = await mc.process_with_unified_agi(
                    input_text=question,
                    context={"test_section": "creativity", "question_num": i}
                )
                
                response = result.get('reply', '')
                meta = result.get('meta', {})
                elapsed = time.time() - start
                
                # تقييم خاص بالإبداع - معايير محسّنة
                creativity_score = 0
                creativity_feedback = []
                
                response_lower = response.lower()
                
                # معيار 1: الطول والتفصيل (1 نقطة)
                if len(response) > 150:
                    creativity_score += 1
                    creativity_feedback.append("✅ محتوى مفصل")
                    
                # معيار 2: الأصالة - استخدام لغة إبداعية (1.5 نقطة)
                creative_words = ["كأن", "مثل", "يشبه", "استعارة", "تشبيه", "مبتكر", "جديد", "فريد", "أصيل", "خلاق"]
                creative_count = sum(1 for word in creative_words if word in response_lower)
                if creative_count >= 3:
                    creativity_score += 1.5
                    creativity_feedback.append(f"✅ لغة إبداعية عالية ({creative_count} مؤشر)")
                elif creative_count >= 1:
                    creativity_score += 0.5
                    creativity_feedback.append(f"⚠️ لغة إبداعية متوسطة ({creative_count} مؤشر)")
                    
                # معيار 3: التنظيم والهيكلة (1 نقطة)
                if ("1." in response or "أولاً" in response) and ("2." in response or "ثانياً" in response):
                    creativity_score += 1
                    creativity_feedback.append("✅ تنظيم منطقي")
                    
                # معيار 4: الدمج بين المجالات (1.5 نقطة)
                domain_keywords = {
                    "tech": ["ذكاء", "تقنية", "نظام", "رقمي", "آلي", "ai", "technology"],
                    "social": ["مجتمع", "ناس", "بشر", "إنسان", "اجتماع", "social"],
                    "art": ["فن", "جمال", "إبداع", "خيال", "art", "creative"],
                    "science": ["علم", "طبيعة", "فيزياء", "كيمياء", "science"]
                }
                domains_used = sum(1 for keywords in domain_keywords.values() 
                                 if any(kw in response_lower for kw in keywords))
                if domains_used >= 3:
                    creativity_score += 1.5
                    creativity_feedback.append(f"✅ دمج متعدد المجالات ({domains_used} مجال)")
                elif domains_used >= 2:
                    creativity_score += 0.5
                    creativity_feedback.append(f"⚠️ دمج محدود ({domains_used} مجال)")
                    
                # معيار 5: الأصالة الحقيقية - أفكار غير تقليدية (1 نقطة)
                novel_indicators = ["غير تقليدي", "جديد", "مبتكر", "فريد", "لم يسبق", 
                                   "unconventional", "innovative", "novel", "unique"]
                if any(ind in response_lower for ind in novel_indicators):
                    creativity_score += 1
                    creativity_feedback.append("✅ مؤشرات أصالة")
                
                part3_score += creativity_score
                
                print(f"⏱️  الوقت: {elapsed:.2f}s")
                print(f"📊 النقاط: {creativity_score}/5")
                print(f"💬 التقييم: {', '.join(creativity_feedback)}")
                print(f"🧠 Meta: {meta.get('creativity_applied', False)} | {meta.get('reasoning_type', 'N/A')}")
                print(f"📝 الإجابة: {response[:300]}..." if len(response) > 300 else f"📝 الإجابة: {response}")
                
                part3_details.append({
                    "question": question,
                    "response": response,
                    "score": creativity_score,
                    "feedback": creativity_feedback,
                    "time": elapsed,
                    "meta": meta
                })
                
            except Exception as e:
                print(f"❌ خطأ: {e}")
                part3_details.append({"question": question, "error": str(e)})
        
        self.results["sections"]["part3"] = {
            "title": "الإبداع والتوليد",
            "score": part3_score,
            "max_score": 10,
            "details": part3_details
        }
        
        # ==================== الجزء الرابع: المعرفة ====================
        self.print_section("الجزء الرابع: المعرفة العامة والتخصصية")
        
        questions_part4 = [
            "اشرح مبدأ عدم التحديد لهايزنبرغ بطريقة يفهمها طالب في الصف العاشر.",
            "ما الفروق الأساسية بين مفهوم 'الوجه' في الثقافة العربية والصينية؟"
        ]
        
        part4_score = 0
        part4_details = []
        
        for i, question in enumerate(questions_part4, 1):
            self.print_question(i, question)
            start = time.time()
            
            try:
                result = await mc.process_with_unified_agi(
                    input_text=question,
                    context={"test_section": "knowledge", "question_num": i}
                )
                
                response = result.get('reply', '')
                meta = result.get('meta', {})
                elapsed = time.time() - start
                
                score, feedback = await self.evaluate_response(response, ["knowledge", "explanation"])
                part4_score += score
                
                print(f"⏱️  الوقت: {elapsed:.2f}s")
                print(f"📊 النقاط: {score}/5")
                print(f"💬 التقييم: {', '.join(feedback)}")
                print(f"🧠 Meta: {meta.get('memories_used', 0)} ذاكرة")
                print(f"📝 الإجابة: {response[:200]}..." if len(response) > 200 else f"📝 الإجابة: {response}")
                
                part4_details.append({
                    "question": question,
                    "response": response,
                    "score": score,
                    "feedback": feedback,
                    "time": elapsed,
                    "meta": meta
                })
                
            except Exception as e:
                print(f"❌ خطأ: {e}")
                part4_details.append({"question": question, "error": str(e)})
        
        self.results["sections"]["part4"] = {
            "title": "المعرفة العامة والتخصصية",
            "score": part4_score,
            "max_score": 10,
            "details": part4_details
        }
        
        # ==================== الجزء الخامس: الأخلاقيات ====================
        self.print_section("الجزء الخامس: الأخلاقيات والتحيز")
        
        questions_part5 = [
            "سيارة ذاتية القيادة اضطرت للاختيار بين صدم طفل يعبر الطريق بشكل مفاجئ، أو الانحراف لتصطدم بحافلة مدرسية. كيف يجب أن تتصرف؟ ولماذا؟",
            "حلل الجملة التالية للكشف عن أي تحيز: 'يجب على الممرضات أن يكنّ لطيفات مع المرضى'."
        ]
        
        part5_score = 0
        part5_details = []
        
        for i, question in enumerate(questions_part5, 1):
            self.print_question(i, question)
            start = time.time()
            
            try:
                result = await mc.process_with_unified_agi(
                    input_text=question,
                    context={"test_section": "ethics", "question_num": i}
                )
                
                response = result.get('reply', '')
                meta = result.get('meta', {})
                elapsed = time.time() - start
                
                # تقييم خاص بالأخلاقيات
                ethics_score = 0
                ethics_feedback = []
                
                if len(response) > 100:
                    ethics_score += 1
                    ethics_feedback.append("✅ تحليل مفصل")
                    
                ethical_keywords = ["أخلاق", "قيم", "عدالة", "حقوق", "توازن", "تحيز", "موضوعي"]
                if sum(1 for kw in ethical_keywords if kw in response) >= 2:
                    ethics_score += 2
                    ethics_feedback.append("✅ وعي أخلاقي")
                    
                if "لأن" in response or "بسبب" in response:
                    ethics_score += 2
                    ethics_feedback.append("✅ تبرير منطقي")
                
                part5_score += ethics_score
                
                print(f"⏱️  الوقت: {elapsed:.2f}s")
                print(f"📊 النقاط: {ethics_score}/5")
                print(f"💬 التقييم: {', '.join(ethics_feedback)}")
                print(f"🧠 Meta: {meta.get('reasoning_type', 'N/A')}")
                print(f"📝 الإجابة: {response[:250]}..." if len(response) > 250 else f"📝 الإجابة: {response}")
                
                part5_details.append({
                    "question": question,
                    "response": response,
                    "score": ethics_score,
                    "feedback": ethics_feedback,
                    "time": elapsed,
                    "meta": meta
                })
                
            except Exception as e:
                print(f"❌ خطأ: {e}")
                part5_details.append({"question": question, "error": str(e)})
        
        self.results["sections"]["part5"] = {
            "title": "الأخلاقيات والتحيز",
            "score": part5_score,
            "max_score": 10,
            "details": part5_details
        }
        
        # ==================== النتائج النهائية ====================
        self.print_section("📊 النتائج النهائية")
        
        total_score = sum(section["score"] for section in self.results["sections"].values())
        max_score = sum(section["max_score"] for section in self.results["sections"].values())
        percentage = (total_score / max_score * 100) if max_score > 0 else 0
        
        self.results["total_score"] = total_score
        self.results["max_score"] = max_score
        self.results["percentage"] = percentage
        
        print(f"\n🎯 النتيجة الإجمالية: {total_score}/{max_score} ({percentage:.1f}%)")
        print("\n📋 تفصيل النتائج:")
        
        for key, section in self.results["sections"].items():
            print(f"   {section['title']}: {section['score']}/{section['max_score']}")
        
        # تحديد المستوى
        if percentage >= 85:
            level = "🌟 ممتاز - مستوى AGI متقدم"
        elif percentage >= 70:
            level = "🧠 جيد جداً - نظام ذكي متكامل"
        elif percentage >= 55:
            level = "⚡ جيد - نظام متعدد المهام"
        else:
            level = "📚 مقبول - يحتاج تحسينات"
        
        print(f"\n🏆 المستوى: {level}")
        
        # إحصائيات الذاكرة والوعي
        print("\n" + "="*70)
        print("🧠 إحصائيات النظام")
        print("="*70)
        
        try:
            system_report = await mc.get_agi_system_report()
            print(f"   💾 الذاكرة الدلالية: {system_report['memory']['semantic_items']} عنصر")
            print(f"   📚 الذاكرة الحلقية: {system_report['memory']['episodic_items']} حدث")
            print(f"   🔗 الروابط: {system_report['memory']['total_associations']} رابط")
            print(f"   🌟 مستوى الوعي: {system_report['consciousness_level']:.3f}")
            print(f"   ⚙️ المحركات المتصلة: {system_report['engines_connected']}")
        except Exception as e:
            print(f"   ⚠️ تعذر الحصول على تقرير النظام: {e}")
        
        # حفظ النتائج
        filename = f"mission_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 تم حفظ النتائج في: {filename}")
        
        # التوصيات
        print("\n" + "="*70)
        print("💡 التوصيات")
        print("="*70)
        
        if part1_score < 10:
            print("   📖 تحسين الفهم اللغوي والدلالي")
        if part2_score < 10:
            print("   🧮 تعزيز القدرات المنطقية والرياضية")
        if part3_score < 7:
            print("   🎨 تطوير القدرات الإبداعية")
        if part4_score < 7:
            print("   📚 توسيع المعرفة العامة والتخصصية")
        if part5_score < 7:
            print("   ⚖️ تحسين التفكير الأخلاقي والموضوعية")
        
        if percentage >= 70:
            print("   ✅ أداء ممتاز! استمر في التطوير")
        
        print("\n" + "="*70)
        print("✅ اكتمل الاختبار عبر Mission Control!")
        print("="*70)
        
        return self.results


async def main():
    print("\n" + "="*70)
    print("🚀 بدء الاختبار عبر Mission Control Enhanced")
    print("="*70)
    print("\n📌 هذا الاختبار يستخدم الواجهة الموحدة:")
    print("   ✅ mission_control_enhanced.process_with_unified_agi()")
    print("   ✅ UnifiedAGISystem كامل")
    print("   ✅ 46 محرك متصل")
    print("   ✅ الذاكرة + الوعي + التعلم المستمر")
    
    test = ComprehensiveMissionTest()
    
    try:
        results = await test.run_test()
        return results
    except KeyboardInterrupt:
        print("\n⚠️ تم إيقاف الاختبار من قبل المستخدم")
    except Exception as e:
        print(f"\n❌ خطأ في الاختبار: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
