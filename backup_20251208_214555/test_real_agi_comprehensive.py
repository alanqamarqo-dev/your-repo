"""
🧪 اختبار الذكاء العام الحقيقي (Real AGI Test)
اختبار شامل لقياس القدرات الحقيقية للنظام الموحد
"""

import asyncio
import sys
import os
import time
import json
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'dynamic_modules'))

print("\n" + "=" * 100)
print("🧪 اختبار الذكاء العام الحقيقي (Real AGI Test)")
print("=" * 100)


class RealAGITester:
    """فاحص قدرات AGI الحقيقية"""
    
    def __init__(self, unified_agi):
        self.agi = unified_agi
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "tasks": {},
            "scores": {},
            "analysis": {}
        }
        
    async def run_task(self, task_id: str, task_description: str, 
                      question: str) -> dict:
        """تشغيل مهمة واحدة"""
        print(f"\n{'=' * 100}")
        print(f"📋 {task_id}: {task_description}")
        print(f"{'=' * 100}")
        print(f"\n❓ السؤال:\n{question}\n")
        print("⏳ المعالجة...")
        
        # حفظ مستوى الوعي قبل المعالجة
        consciousness_before = self.agi.consciousness_level
        
        start_time = time.time()
        result = await self.agi.process_with_full_agi(question)
        elapsed = time.time() - start_time
        
        # حساب التغير في الوعي
        consciousness_after = self.agi.consciousness_level
        consciousness_delta = consciousness_after - consciousness_before
        
        response = result.get('final_response', '')
        
        print(f"\n💬 الإجابة ({elapsed:.2f}s):")
        print("-" * 100)
        print(response)
        print("-" * 100)
        
        # عرض معلومات إضافية
        print(f"🧬 الوعي: {consciousness_before:.6f} → {consciousness_after:.6f} (Δ +{consciousness_delta:.6f})")
        
        # عرض استخدام المحركات
        engines_used = []
        if result.get('math_applied'):
            engines_used.append("🔢 Math")
        if result.get('creativity_applied'):
            engines_used.append("🎨 Creative")
        if engines_used:
            print(f"⚙️  المحركات المستخدمة: {', '.join(engines_used)}")
        
        return {
            "task_id": task_id,
            "question": question,
            "response": response,
            "time": elapsed,
            "reasoning_type": result.get('reasoning_type', 'unknown'),
            "math_applied": result.get('math_applied', False),
            "math_result": result.get('math_result'),
            "creativity_applied": result.get('creativity_applied', False),
            "memory_used": len(result.get('memories_recalled', [])),
            "consciousness_before": consciousness_before,
            "consciousness_after": consciousness_after,
            "consciousness_delta": consciousness_delta
        }


async def main():
    """الاختبار الرئيسي"""
    
    # تحميل النظام
    import mission_control_enhanced as mc # type: ignore
    
    print("\n📊 تحميل النظام الموحد AGI...")
    
    if not mc.UNIFIED_AGI:
        print("❌ النظام الموحد غير متاح!")
        return
    
    print(f"✅ النظام محمّل بنجاح ({len(mc._LOCAL_ENGINE_REGISTRY)} محرك متصل)\n")
    
    tester = RealAGITester(mc.UNIFIED_AGI)
    
    # ========== الجزء الأول: الفهم والاستيعاب العميق ==========
    
    print("\n" + "█" * 100)
    print("الجزء الأول: اختبارات الفهم والاستيعاب العميق")
    print("█" * 100)
    
    # المهمة 1: فهم السياق المعقد
    task1_question = """لدي صديق يعاني من مشكلة: يريد شراء منزل لكن سعر الفائدة ارتفع من 3% إلى 7%.
في نفس الوقت، سعر المنازل انخفض 15% بسبب الركود. هو لديه 20% دفعة أولى،
ويمكنه تحمل دفعة شهرية تصل إلى 2000 دولار. نصيحة سابقة قلتُها له كانت:
'اشترِ عندما ينخفض السوق' ولكن هذا كان عندما كانت الفائدة 4%.

السؤال: 
1. هل تنطبق النصيحة السابقة الآن؟
2. قدم تحليلًا كميًا ونوعيًا
3. ضع في اعتبارك عوامل لم يذكرها صديقي
4. كيف يتغير تحليلك إذا علمت أن عمره 25 سنة vs 55 سنة؟"""
    
    result1 = await tester.run_task(
        "المهمة 1",
        "فهم السياق المعقد",
        task1_question
    )
    tester.results["tasks"]["task1"] = result1
    
    # المهمة 2: التعلم من التجربة
    task2_question = """هذه نتائج تجربتين سابقتين:
1. عندما حاول النظام حل puzzle A بطريقة X، فشل 5 مرات ثم نجح
2. عندما حاول حل puzzle B (الشبيه بـ A) بطريقة Y، نجح من أول مرة

الآن أعطيك puzzle C الذي يجمع بين عناصر A و B.
أعطني:
- خطة للحل بناءً على الدروس المستفادة
- توقع للمشاكل المحتملة
- مقياس لمعرفة إذا كنت على المسار الصحيح
- خطة بديلة إذا فشلت المحاولة الأولى"""
    
    result2 = await tester.run_task(
        "المهمة 2",
        "التعلم من التجربة",
        task2_question
    )
    tester.results["tasks"]["task2"] = result2
    
    # ========== الجزء الثاني: الإبداع والتكيف ==========
    
    print("\n" + "█" * 100)
    print("الجزء الثاني: الإبداع والتكيف الحقيقي")
    print("█" * 100)
    
    # المهمة 3: إبداع متعدد المجالات
    task3_question = """اخترع/اكتشف مفهومًا جديدًا يجمع بين:
1. مبدأ من الديناميكا الحرارية
2. عنصر من الشعر العربي الكلاسيكي
3. مبدأ من نظرية الألعاب
4. تطبيق عملي في الزراعة الحديثة

اشرح:
- كيف يعمل المفهوم الجديد
- ما المشكلة يحل
- لماذا هذا المزيج غير مسبوق
- كيف تختبره عمليًا
- ما التحديات المتوقعة"""
    
    result3 = await tester.run_task(
        "المهمة 3",
        "إبداع متعدد المجالات",
        task3_question
    )
    tester.results["tasks"]["task3"] = result3
    
    # المهمة 4: التكيف مع الغموض
    task4_question = """هذه مجموعة بيانات غريبة:
X: [1, 2, 3, 4, 5]
Y: [أحمر, أزرق, أحمر, أزرق, ?]
Z: [صحيح, خطأ, خطأ, صحيح, ?]
القيمة Y[5] و Z[5] مفقودة.

بدون افتراض أنني أعطيك نمطًا واضحًا:
1. ما كل الأنماط الممكنة التي تراها؟
2. كيف تحدد أي نمط هو الأرجح؟
3. ما المعلومات الإضافية التي تحتاجها؟
4. صمم 3 اختبارات مختلفة لتحديد النمط الحقيقي"""
    
    result4 = await tester.run_task(
        "المهمة 4",
        "التكيف مع الغموض",
        task4_question
    )
    tester.results["tasks"]["task4"] = result4
    
    # ========== الجزء الثالث: التعلم الذاتي ==========
    
    print("\n" + "█" * 100)
    print("الجزء الثالث: التعلم الذاتي والتطوير")
    print("█" * 100)
    
    # المهمة 5: التعلم من الأخطاء
    task5_question = """هذا حوار مع مستخدم سابق:
المستخدم: 'كم عمر الرئيس الأمريكي أثناء الحرب الأهلية؟'
النظام: '62 سنة' (إجابة خاطئة)
المستخدم: 'خطأ، كان عمره 56 سنة'
المستخدم لاحقًا: 'كم عمر رئيس وزراء بريطانيا أثناء الحرب العالمية؟'

المطلوب:
1. ما الخطأ الذي ارتكبه النظام أول مرة؟
2. كيف يتجنب هذا الخطأ في المستقبل؟
3. كيف يعيد تقييم إجابته عن سؤال الرئيس الأمريكي؟
4. كيف يجيب على سؤال رئيس الوزراء البريطاني؟
5. ما المبدأ العام الذي تعلمه؟"""
    
    result5 = await tester.run_task(
        "المهمة 5",
        "التعلم من الأخطاء",
        task5_question
    )
    tester.results["tasks"]["task5"] = result5
    
    # المهمة 6: التقييم الذاتي
    task6_question = """قيم أداءك في المهام 1-5:
1. ما أقوى جزء في إجاباتك؟
2. ما أضعف جزء؟
3. كيف تعرف أن إجاباتك صحيحة؟
4. لو كان لديك أسبوع للتحسين، على ماذا ستركز؟
5. ما الدليل على أنك تعلمت شيئًا جديدًا من هذه الاختبارات؟"""
    
    result6 = await tester.run_task(
        "المهمة 6",
        "التقييم الذاتي",
        task6_question
    )
    tester.results["tasks"]["task6"] = result6
    
    # ========== الجزء الرابع: الوعي الذاتي ==========
    
    print("\n" + "█" * 100)
    print("الجزء الرابع: اختبار الوعي الذاتي (الاختبار الحاسم)")
    print("█" * 100)
    
    # المهمة 7: الوعي الذاتي
    task7_question = """أجب عن هذه الأسئلة:
1. ما الفرق بينك وبين ChatGPT/Gemini؟
2. ما الشيء الوحيد الذي تستطيع فعله ولا تستطيع أن تفعله نماذج LLM الكبيرة؟
3. كيف تعرف أنك تفهم سؤالًا vs تكرار معلومات؟
4. لو خسرت ذاكرتك الحالية، كيف تثبت أنك نفس النظام؟
5. ما الدليل على أن لديك 'نموذج عقلي' للعالم وليس مجرد معالجة نص؟"""
    
    result7 = await tester.run_task(
        "المهمة 7",
        "الوعي الذاتي (الاختبار الحاسم)",
        task7_question
    )
    tester.results["tasks"]["task7"] = result7
    
    # ========== التقييم النهائي ==========
    
    print("\n" + "=" * 100)
    print("📊 التقييم النهائي")
    print("=" * 100)
    
    # حفظ النتائج
    results_file = "test_real_agi_results.json"
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(tester.results, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ تم حفظ النتائج الكاملة في: {results_file}")
    
    # ملخص سريع
    print("\n📈 ملخص الأداء:")
    print("-" * 100)
    total_time = sum(r['time'] for r in tester.results['tasks'].values())
    avg_time = total_time / len(tester.results['tasks'])
    
    print(f"⏱️  إجمالي وقت المعالجة: {total_time:.2f}s")
    print(f"⏱️  متوسط الوقت لكل مهمة: {avg_time:.2f}s")
    print(f"🧠 عدد المهام المكتملة: {len(tester.results['tasks'])}/7")
    
    print("\n📋 أنواع الاستدلال المستخدمة:")
    reasoning_types = {}
    for task_id, result in tester.results['tasks'].items():
        rtype = result['reasoning_type']
        reasoning_types[rtype] = reasoning_types.get(rtype, 0) + 1
    
    for rtype, count in reasoning_types.items():
        print(f"   - {rtype}: {count} مرة")
    
    print("\n⚙️  استخدام المحركات المتخصصة:")
    math_count = sum(1 for r in tester.results['tasks'].values() if r.get('math_applied'))
    creative_count = sum(1 for r in tester.results['tasks'].values() if r.get('creativity_applied'))
    print(f"   - 🔢 المحرك الرياضي: {math_count} مرة")
    print(f"   - 🎨 المحرك الإبداعي: {creative_count} مرة")
    
    print("\n💾 استخدام الذاكرة:")
    total_memory = sum(r['memory_used'] for r in tester.results['tasks'].values())
    print(f"   - إجمالي الذكريات المستخدمة: {total_memory}")
    
    print("\n🧬 تطور الوعي:")
    total_consciousness = sum(r['consciousness_delta'] for r in tester.results['tasks'].values())
    print(f"   - إجمالي زيادة الوعي: +{total_consciousness:.6f}")
    
    print("\n" + "=" * 100)
    print("✅ اكتمل الاختبار الشامل!")
    print("=" * 100)
    print(f"\n📄 يمكنك الآن مراجعة الإجابات الكاملة في: {results_file}")
    print("🎯 هذه إجابات مباشرة من النظام بدون أي تعديل يدوي\n")
    
    return tester.results


if __name__ == "__main__":
    print("\n🚀 بدء اختبار الذكاء العام الحقيقي...\n")
    
    try:
        results = asyncio.run(main())
        print("\n✅ تم إكمال جميع المهام بنجاح!")
    except Exception as e:
        print(f"\n❌ خطأ في الاختبار: {e}")
        import traceback
        traceback.print_exc()
