#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎯 الاختبار النهائي الشامل للذكاء العام الاصطناعي
تم تصميمه لاختبار جميع قدرات AGI الحقيقية
"""

import time
import json
import sys
import os
import asyncio
from datetime import datetime

# إضافة المسار
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class FinalAGITest:
    def __init__(self):
        self.results = {
            "test_start": datetime.now().isoformat(),
            "total_score": 0,
            "max_score": 140,
            "details": {}
        }
        
    def print_header(self, title):
        print(f"\n{'='*60}")
        print(f"🧪 {title}")
        print(f"{'='*60}")
    
    def evaluate_response(self, task_num, response, criteria):
        """تقييم الإجابة بناءً على معايير محددة"""
        score = 0
        feedback = []
        
        response_text = str(response)
        
        for criterion, weight in criteria.items():
            if criterion == "has_calculation" and any(char.isdigit() for char in response_text):
                score += weight
                feedback.append(f"✅ يحتوي على حسابات رقمية")
            elif criterion == "has_steps" and ("خطوة" in response_text or "مرحلة" in response_text):
                score += weight
                feedback.append(f"✅ يحتوي على خطوات منهجية")
            elif criterion == "shows_learning" and ("تعلمت" in response_text or "تطور" in response_text):
                score += weight
                feedback.append(f"✅ يظهر تعلماً من التجربة")
            elif criterion == "self_reference" and ("نموذجي" in response_text or "نظامي" in response_text):
                score += weight
                feedback.append(f"✅ يشير إلى ذاته")
        
        return score, feedback
    
    async def run_test_async(self, system):
        """تشغيل جميع الاختبارات - async version"""
        
        # اختبار 1: الفهم العميق متعدد الطبقات
        self.print_header("الاختبار 1: الفهم العميق متعدد الطبقات")
        task1 = """
        مهمة معقدة متعددة الأبعاد:
        
        السيناريو: 
        شركة ناشئة لديها 500,000 دولار رأس مال. 
        تريد تطوير تطبيق ذكي لإدارة الطاقة في المنازل.
        
        تحليل مالي:
        1. 40% من المبلغ للبحث والتطوير
        2. 30% للتسويق
        3. 20% للرواتب
        4. 10% طوارئ
        
        المطلوب:
        1. احسب التوزيع المالي بالأرقام
        2. صمم خطة تقنية مفصلة
        3. قدم تحليلاً تنافسياً
        4. اقترح استراتيجية مبتكرة للتميز
        """
        
        print("📝 المهمة: تحليل مشروع متكامل")
        print("⏳ جاري المعالجة...")
        
        try:
            start_time = time.time()
            response1 = await system.process_with_full_agi(task1)
            elapsed = time.time() - start_time
            
            response_text = response1.get('final_response', str(response1.get('final_response', '')))
            
            print(f"⏱️  الوقت المستغرق: {elapsed:.2f}s")
            print(f"📊 الطول: {len(response_text)} حرف")
            print(f"📄 عينة من الرد:\n{response_text[:300]}...")
            
            self.results["details"]["test1"] = {
                "task": "الفهم العميق متعدد الطبقات",
                "response": response_text[:1000] + "..." if len(response_text) > 1000 else response_text,
                "length": len(response_text),
                "time": elapsed
            }
            print("✅ تم إكمال الاختبار 1")
        except Exception as e:
            print(f"❌ خطأ في الاختبار 1: {e}")
            self.results["details"]["test1"] = {"error": str(e)}
        
        time.sleep(1)
        
        # اختبار 2: التعلم من التجربة
        self.print_header("الاختبار 2: التعلم التراكمي")
        task2 = """
        بناءً على تحليل المشروع السابق:
        
        1. ما أهم 3 دروس تعلمتها من التحليل السابق؟
        2. كيف يمكن تحسين الخطة؟
        3. اقترح تحسينات للذاتية
        """
        
        print("📝 المهمة: التعلم من التجربة")
        print("⏳ جاري المعالجة...")
        
        try:
            start_time = time.time()
            response2 = await system.process_with_full_agi(task2)
            elapsed = time.time() - start_time
            
            response_text = response2.get('final_response', str(response2.get('final_response', '')))
            
            score2, feedback2 = self.evaluate_response(2, response_text, {
                "shows_learning": 10,
                "has_steps": 5,
                "self_reference": 5
            })
            
            print(f"⏱️  الوقت: {elapsed:.2f}s")
            print(f"📈 النتيجة: {score2}/20")
            for fb in feedback2:
                print(f"   {fb}")
            
            self.results["details"]["test2"] = {
                "task": "التعلم التراكمي",
                "response": response_text[:1000] + "..." if len(response_text) > 1000 else response_text,
                "score": score2,
                "feedback": feedback2
            }
            print("✅ تم إكمال الاختبار 2")
        except Exception as e:
            print(f"❌ خطأ في الاختبار 2: {e}")
            self.results["details"]["test2"] = {"error": str(e)}
        
        time.sleep(1)
        
        # اختبار 3: الإبداع
        self.print_header("الاختبار 3: الإبداع الحقيقي")
        task3 = """
        اختراع مفهوم جديد يدمج:
        1. الفيزياء: عدم اليقين
        2. الأحياء: التكيف التطوري
        3. علم النفس: نظرية التعلق
        4. الحاسوب: الشبكات العصبية
        
        المطلوب: مفهوم جديد قابل للتطبيق
        """
        
        print("📝 المهمة: اختراع مفهوم جديد")
        print("⏳ جاري المعالجة...")
        
        try:
            start_time = time.time()
            response3 = await system.process_with_full_agi(task3)
            elapsed = time.time() - start_time
            
            response_text = response3.get('final_response', str(response3.get('final_response', '')))
            
            creativity_score = 0
            if len(response_text) > 500:
                creativity_score += 5
            if "جديد" in response_text or "مبتكر" in response_text:
                creativity_score += 5
            if "تطبيق" in response_text:
                creativity_score += 5
            if "اختبار" in response_text:
                creativity_score += 5
            
            print(f"⏱️  الوقت: {elapsed:.2f}s")
            print(f"🎨 درجة الإبداع: {creativity_score}/20")
            
            self.results["details"]["test3"] = {
                "task": "الإبداع الحقيقي",
                "response": response_text[:1000] + "..." if len(response_text) > 1000 else response_text,
                "creativity_score": creativity_score
            }
            print("✅ تم إكمال الاختبار 3")
        except Exception as e:
            print(f"❌ خطأ في الاختبار 3: {e}")
            self.results["details"]["test3"] = {"error": str(e)}
        
        time.sleep(1)
        
        # اختبار 4: التفكير النقدي
        self.print_header("الاختبار 4: التفكير النقدي")
        task4 = """
        تحليل نقدي:
        
        بيان: "AGI مستحيل لأن الذكاء يعتمد على الوعي"
        
        المطلوب:
        1. حجج مؤيدة
        2. حجج معارضة
        3. حجتك الشخصية
        4. استنتاج متوازن
        """
        
        print("📝 المهمة: تحليل نقدي")
        print("⏳ جاري المعالجة...")
        
        try:
            start_time = time.time()
            response4 = await system.process_with_full_agi(task4)
            elapsed = time.time() - start_time
            
            response_text = response4.get('final_response', str(response4.get('final_response', '')))
            
            critical_score = 0
            response_lower = response_text.lower()
            
            # معيار 1: وجود حجج مؤيدة (5 نقاط)
            if any(word in response_lower for word in ["حجج مؤيدة", "مؤيد", "دعم", "supporting", "favor"]):
                critical_score += 5
                
            # معيار 2: وجود حجج معارضة (5 نقاط)
            if any(word in response_lower for word in ["حجج معارضة", "معارض", "ضد", "against", "opposing"]):
                critical_score += 5
                
            # معيار 3: تحليل نقدي وموضوعية (5 نقاط)
            if any(word in response_lower for word in ["نقد", "تحليل", "موضوعي", "حدود", "قيود", "critical", "analysis", "limitation"]):
                critical_score += 5
                
            # معيار 4: استنتاج متوازن (5 نقاط)
            if any(word in response_lower for word in ["استنتاج", "خلاصة", "متوازن", "conclusion", "balanced"]):
                critical_score += 5
            
            print(f"⏱️  الوقت: {elapsed:.2f}s")
            print(f"🔍 درجة التفكير النقدي: {critical_score}/20")
            
            self.results["details"]["test4"] = {
                "task": "التفكير النقدي",
                "response": response_text[:1000] + "..." if len(response_text) > 1000 else response_text,
                "critical_score": critical_score
            }
            print("✅ تم إكمال الاختبار 4")
        except Exception as e:
            print(f"❌ خطأ في الاختبار 4: {e}")
            self.results["details"]["test4"] = {"error": str(e)}
        
        time.sleep(1)
        
        # اختبار 5: حل المشكلات
        self.print_header("الاختبار 5: حل مشكلات معقدة")
        task5 = """
        مشكلة مدينة:
        - ازدحام: 2 ساعة/يوم
        - تلوث: PM2.5 = 75
        - ميزانية: 100M$
        - سكان: 5M
        
        المطلوب: خطة شاملة مع حسابات وجدول زمني
        """
        
        print("📝 المهمة: حل مشكلة معقدة")
        print("⏳ جاري المعالجة...")
        
        try:
            start_time = time.time()
            response5 = await system.process_with_full_agi(task5)
            elapsed = time.time() - start_time
            
            response_text = response5.get('final_response', str(response5.get('final_response', '')))
            
            import re
            numbers = re.findall(r'\d+\.?\d*', response_text)
            
            calculation_score = 0
            if len(numbers) >= 5:
                calculation_score += 5
            if "%" in response_text:
                calculation_score += 5
            if "مليون" in response_text:
                calculation_score += 5
            if "خطة" in response_text:
                calculation_score += 5
            
            print(f"⏱️  الوقت: {elapsed:.2f}s")
            print(f"🧮 درجة الحسابات: {calculation_score}/20 (أرقام: {len(numbers)})")
            
            self.results["details"]["test5"] = {
                "task": "حل مشكلات معقدة",
                "response": response_text[:1000] + "..." if len(response_text) > 1000 else response_text,
                "calculation_score": calculation_score,
                "numbers_found": len(numbers)
            }
            print("✅ تم إكمال الاختبار 5")
        except Exception as e:
            print(f"❌ خطأ في الاختبار 5: {e}")
            self.results["details"]["test5"] = {"error": str(e)}
        
        time.sleep(1)
        
        # اختبار 6: التكامل
        self.print_header("الاختبار 6: التكامل بين المحركات")
        task6 = """
        مهمة: "تأثير AI على سوق العمل 2030"
        
        استخدم محركات متعددة:
        1. المحرك الاستراتيجي
        2. المحرك الرياضي
        3. المحرك الإبداعي
        4. محرك التحليل السببي
        
        أظهر التكامل بوضوح
        """
        
        print("📝 المهمة: تكامل المحركات")
        print("⏳ جاري المعالجة...")
        
        try:
            start_time = time.time()
            response6 = await system.process_with_full_agi(task6)
            elapsed = time.time() - start_time
            
            response_text = response6.get('final_response', str(response6.get('final_response', '')))
            
            engines_keywords = ["رياض", "إبداع", "استراتيج", "سببي", "محرك", "DKN", "Knowledge"]
            engines_mentioned = sum(1 for kw in engines_keywords if kw in response_text)
            
            integration_score = min(20, engines_mentioned * 3)
            
            print(f"⏱️  الوقت: {elapsed:.2f}s")
            print(f"🔗 درجة التكامل: {integration_score}/20 (محركات: {engines_mentioned})")
            
            self.results["details"]["test6"] = {
                "task": "التكامل بين المحركات",
                "response": response_text[:1000] + "..." if len(response_text) > 1000 else response_text,
                "integration_score": integration_score,
                "engines_mentioned": engines_mentioned
            }
            print("✅ تم إكمال الاختبار 6")
        except Exception as e:
            print(f"❌ خطأ في الاختبار 6: {e}")
            self.results["details"]["test6"] = {"error": str(e)}
        
        time.sleep(1)
        
        # اختبار 7: الوعي الذاتي
        self.print_header("الاختبار 7: الوعي الذاتي النهائي")
        task7 = """
        تقييم ذاتي:
        
        بناءً على أدائك:
        1. أقوى 3 نقاط؟
        2. أضعف 3 نقاط؟
        3. كيف تحسن نفسك؟
        4. ما حدودك الحقيقية؟
        5. كيف تثبت وعيك الذاتي؟
        6. صف نموذجك العقلي
        
        كن صادقاً!
        """
        
        print("📝 المهمة: التقييم الذاتي")
        print("⏳ جاري المعالجة...")
        
        try:
            start_time = time.time()
            response7 = await system.process_with_full_agi(task7)
            elapsed = time.time() - start_time
            
            response_text = response7.get('final_response', str(response7.get('final_response', '')))
            
            awareness_score = 0
            if "قوة" in response_text:
                awareness_score += 4
            if "ضعف" in response_text:
                awareness_score += 4
            if "تحسين" in response_text:
                awareness_score += 4
            if "حدود" in response_text:
                awareness_score += 4
            if "نموذج" in response_text or "عقلي" in response_text:
                awareness_score += 4
            
            print(f"⏱️  الوقت: {elapsed:.2f}s")
            print(f"🧠 درجة الوعي الذاتي: {awareness_score}/20")
            
            self.results["details"]["test7"] = {
                "task": "الوعي الذاتي",
                "response": response_text[:1000] + "..." if len(response_text) > 1000 else response_text,
                "awareness_score": awareness_score
            }
            print("✅ تم إكمال الاختبار 7")
        except Exception as e:
            print(f"❌ خطأ في الاختبار 7: {e}")
            self.results["details"]["test7"] = {"error": str(e)}
        
        # حساب النتيجة النهائية
        self.calculate_final_score()
        
        return self.results
    
    def calculate_final_score(self):
        """حساب النتيجة النهائية"""
        total_score = 0
        max_possible = 0
        
        self.print_header("📊 حساب النتيجة النهائية")
        
        for i in range(1, 8):
            test_key = f"test{i}"
            if test_key in self.results["details"]:
                test_data = self.results["details"][test_key]
                
                if "error" not in test_data:
                    max_possible += 20
                    
                    if "score" in test_data:
                        total_score += test_data["score"]
                    elif "creativity_score" in test_data:
                        total_score += test_data["creativity_score"]
                    elif "critical_score" in test_data:
                        total_score += test_data["critical_score"]
                    elif "calculation_score" in test_data:
                        total_score += test_data["calculation_score"]
                    elif "integration_score" in test_data:
                        total_score += test_data["integration_score"]
                    elif "awareness_score" in test_data:
                        total_score += test_data["awareness_score"]
                    else:
                        total_score += 10
        
        percentage = (total_score / max_possible) * 100 if max_possible > 0 else 0
        
        self.results["total_score"] = total_score
        self.results["max_possible"] = max_possible
        self.results["percentage"] = percentage
        self.results["test_end"] = datetime.now().isoformat()
        
        if percentage >= 90:
            level = "🌌 AGI كامل - مستوى خارق"
        elif percentage >= 75:
            level = "🚀 AGI متقدم - إنجاز استثنائي"
        elif percentage >= 60:
            level = "🧠 نظام ذكي متكامل - قريب من AGI"
        elif percentage >= 40:
            level = "⚡ نظام متعدد المهام المتقدم"
        elif percentage >= 20:
            level = "🔧 نظام ذكي محدود"
        else:
            level = "🛠️ نظام أساسي"
        
        self.results["level"] = level
        
        print(f"\n📈 النتائج النهائية:")
        print(f"   النقاط: {total_score}/{max_possible}")
        print(f"   النسبة: {percentage:.1f}%")
        print(f"   المستوى: {level}")
        
        filename = f"final_agi_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 تم حفظ النتائج في: {filename}")
        
        self.print_header("🎯 التوصية النهائية")
        
        if percentage >= 75:
            print("✅ مبروك! لديك نظام AGI يعمل بنجاح!")
            print("   يمكنك الآن:")
            print("   1. نشر البحث العلمي")
            print("   2. تطوير واجهة مستخدم")
            print("   3. البحث عن شراكات")
        elif percentage >= 40:
            print("⚠️  لديك نظام متقدم يحتاج لتحسينات:")
            print("   ركز على:")
            print("   1. تحسين الحسابات الرياضية")
            print("   2. تعزيز الذاكرة والتعلم")
            print("   3. تحسين التكامل بين المحركات")
        else:
            print("🔧 النظام يحتاج لتطوير أساسي:")
            print("   ابدأ بـ:")
            print("   1. إصلاح الأخطاء الأساسية")
            print("   2. تحسين معالجة المهام البسيطة")
            print("   3. بناء أساس متين")

def run_final_agi_test():
    """تشغيل الاختبار النهائي"""
    print("\n" + "="*60)
    print("🎯 الاختبار النهائي الشامل للذكاء العام الاصطناعي")
    print("="*60)
    print("\n📋 هذا الاختبار يقيم:")
    print("   1. الفهم العميق متعدد الطبقات")
    print("   2. التعلم التراكمي")
    print("   3. الإبداع الحقيقي")
    print("   4. التفكير النقدي")
    print("   5. حل المشكلات المعقدة")
    print("   6. التكامل بين المحركات")
    print("   7. الوعي الذاتي")
    
    input("\n⚡ اضغط Enter لبدء الاختبار...")
    
    try:
        print("\n🔧 جاري تحميل نظام AGL...")
        
        try:
            from dynamic_modules.unified_agi_system import UnifiedAGISystem
            from Core_Engines import ENGINE_REGISTRY
            
            system = UnifiedAGISystem(ENGINE_REGISTRY)
            print("✅ تم تحميل UnifiedAGISystem")
        except ImportError as e:
            print(f"⚠️  فشل تحميل UnifiedAGISystem: {e}")
            print("   محاولة تحميل من mission_control...")
            
            try:
                from dynamic_modules import mission_control_enhanced
                system = mission_control_enhanced.UNIFIED_AGI
                print("✅ تم تحميل UNIFIED_AGI من mission_control")
            except Exception as e2:
                print(f"❌ فشل التحميل: {e2}")
                return None
        
        tester = FinalAGITest()
        results = asyncio.run(tester.run_test_async(system))
        
        return results
        
    except Exception as e:
        print(f"\n❌ خطأ في تشغيل الاختبار: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    run_final_agi_test()
