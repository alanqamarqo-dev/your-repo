"""
اختبار مقارنة بين الوضع العادي والوضع الموحد AGI
"""

import asyncio
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 80)
print("🧪 اختبار مقارنة: الوضع العادي vs الوضع الموحد AGI")
print("=" * 80)


async def test_comparison():
    """مقارنة شاملة بين الوضعين"""
    
    from dynamic_modules import mission_control_enhanced as mc
    
    # الأسئلة الاختبارية
    test_questions = [
        {
            "type": "معرفي",
            "question": "ما العلاقة بين الذكاء الاصطناعي والتعلم الآلي والتعلم العميق؟"
        },
        {
            "type": "إبداعي",
            "question": "اقترح ثلاث أفكار مبتكرة لحل مشكلة التغير المناخي"
        },
        {
            "type": "استدلالي",
            "question": "إذا كانت جميع الطيور تطير، والبطريق طائر، هل يطير البطريق؟ اشرح المنطق"
        },
        {
            "type": "تركيبي",
            "question": "كيف يمكن دمج الذكاء الاصطناعي مع الطاقة المتجددة لبناء مدن ذكية مستدامة؟"
        }
    ]
    
    print("\n" + "=" * 80)
    print("📊 بدء الاختبارات المقارنة")
    print("=" * 80)
    
    for i, test in enumerate(test_questions, 1):
        print(f"\n{'='*80}")
        print(f"🧪 الاختبار {i}/4: {test['type']}")
        print(f"❓ السؤال: {test['question']}")
        print(f"{'='*80}")
        
        # ========== الوضع العادي ==========
        print(f"\n{'─'*80}")
        print("📝 الوضع العادي (Traditional Mode)")
        print(f"{'─'*80}")
        
        start_time = time.time()
        try:
            result_normal = await mc.quick_start_enhanced(
                mission_type="general",
                topic=test["question"],
                use_unified_agi=False  # الوضع العادي
            )
            normal_time = time.time() - start_time
            
            if isinstance(result_normal, dict):
                normal_reply = result_normal.get("reply_text") or result_normal.get("reply", "")
            else:
                normal_reply = str(result_normal)
            
            print(f"⏱️  الوقت: {normal_time:.2f} ثانية")
            print(f"📊 الطول: {len(normal_reply)} حرف")
            print(f"\n💬 الإجابة:")
            print(f"{normal_reply[:500]}..." if len(normal_reply) > 500 else normal_reply)
            
        except Exception as e:
            print(f"❌ خطأ: {e}")
            normal_reply = ""
            normal_time = 0
        
        # ========== الوضع الموحد ==========
        print(f"\n{'─'*80}")
        print("🧬 الوضع الموحد AGI (Unified AGI Mode)")
        print(f"{'─'*80}")
        
        start_time = time.time()
        try:
            result_unified = await mc.quick_start_enhanced(
                mission_type="general",
                topic=test["question"],
                use_unified_agi=True  # الوضع الموحد
            )
            unified_time = time.time() - start_time
            
            if isinstance(result_unified, dict):
                unified_reply = result_unified.get("reply_text") or result_unified.get("reply", "")
                meta = result_unified.get("meta", {})
            else:
                unified_reply = str(result_unified)
                meta = {}
            
            print(f"⏱️  الوقت: {unified_time:.2f} ثانية")
            print(f"📊 الطول: {len(unified_reply)} حرف")
            
            # معلومات إضافية من AGI الموحد
            if meta:
                print(f"🧠 نوع الاستدلال: {meta.get('reasoning_type', 'unknown')}")
                print(f"💾 ذكريات مستخدمة: {meta.get('memories_used', 0)}")
                print(f"🎨 إبداع مطبق: {'نعم' if meta.get('creativity_applied') else 'لا'}")
                gaps = meta.get('curiosity_gaps', [])
                if gaps:
                    print(f"🔍 ثغرات معرفية: {len(gaps)}")
            
            print(f"\n💬 الإجابة:")
            print(f"{unified_reply[:500]}..." if len(unified_reply) > 500 else unified_reply)
            
        except Exception as e:
            print(f"❌ خطأ: {e}")
            unified_reply = ""
            unified_time = 0
        
        # ========== المقارنة ==========
        print(f"\n{'─'*80}")
        print("📊 المقارنة")
        print(f"{'─'*80}")
        
        if normal_reply and unified_reply:
            time_diff = unified_time - normal_time
            length_diff = len(unified_reply) - len(normal_reply)
            
            print(f"⏱️  الوقت: {'الموحد أسرع' if time_diff < 0 else 'العادي أسرع'} بـ {abs(time_diff):.2f}ث")
            print(f"📏 الطول: {'الموحد أطول' if length_diff > 0 else 'العادي أطول'} بـ {abs(length_diff)} حرف")
            
            # تحليل بسيط للجودة
            normal_words = len(normal_reply.split())
            unified_words = len(unified_reply.split())
            print(f"📝 عدد الكلمات: عادي={normal_words}, موحد={unified_words}")
        
        print(f"\n{'─'*80}")
        print(f"✅ الاختبار {i}/4 مكتمل")
        print(f"{'─'*80}")
        
        # فترة راحة قصيرة بين الاختبارات
        await asyncio.sleep(1)
    
    # ========== تقرير حالة النظام ==========
    print(f"\n{'='*80}")
    print("📊 تقرير حالة نظام AGI الموحد")
    print(f"{'='*80}")
    
    try:
        report = await mc.get_agi_system_report()
        if report.get("status") == "active":
            print(f"\n✅ النظام نشط")
            print(f"\n💾 حالة الذاكرة:")
            mem = report["memory"]
            print(f"   - Semantic (دلالية): {mem['semantic_items']} عنصر")
            print(f"   - Episodic (تجريبية): {mem['episodic_items']} عنصر")
            print(f"   - Procedural (إجرائية): {mem['procedural_items']} عنصر")
            print(f"   - Working (عاملة): {mem['working_memory_size']}/20 عنصر")
            print(f"   - Associations (روابط): {mem['total_associations']} رابط")
            
            print(f"\n🔍 حالة الفضول:")
            cur = report["curiosity"]
            print(f"   - مواضيع اهتمام: {cur['interest_topics']}")
            print(f"   - عدد الاستكشافات: {cur['explored_count']}")
            
            print(f"\n🎯 حالة التحفيز:")
            mot = report["motivation"]
            print(f"   - أهداف حالية: {mot['current_goals']}")
            print(f"   - إنجازات: {mot['achievements']}")
            
            print(f"\n🧬 حالة عامة:")
            print(f"   - مستوى الوعي: {report['consciousness_level']}")
            print(f"   - محركات متصلة: {report['engines_connected']}")
    except Exception as e:
        print(f"❌ خطأ في التقرير: {e}")
    
    print(f"\n{'='*80}")
    print("✅ جميع الاختبارات المقارنة اكتملت!")
    print(f"{'='*80}")


async def quick_test():
    """اختبار سريع واحد للمقارنة"""
    from dynamic_modules import mission_control_enhanced as mc
    
    question = "ما هو الفرق بين الذكاء الاصطناعي الضيق والذكاء الاصطناعي العام؟"
    
    print(f"\n🧪 اختبار سريع")
    print(f"❓ السؤال: {question}\n")
    
    # العادي
    print("📝 الوضع العادي:")
    start = time.time()
    result1 = await mc.quick_start_enhanced("general", question, use_unified_agi=False)
    time1 = time.time() - start
    reply1 = result1.get("reply", "") if isinstance(result1, dict) else str(result1)
    print(f"⏱️  {time1:.2f}ث | 📏 {len(reply1)} حرف")
    print(f"💬 {reply1[:200]}...\n")
    
    # الموحد
    print("🧬 الوضع الموحد:")
    start = time.time()
    result2 = await mc.quick_start_enhanced("general", question, use_unified_agi=True)
    time2 = time.time() - start
    reply2 = result2.get("reply", "") if isinstance(result2, dict) else str(result2)
    meta = result2.get("meta", {}) if isinstance(result2, dict) else {}
    print(f"⏱️  {time2:.2f}ث | 📏 {len(reply2)} حرف")
    if meta:
        print(f"🧠 Reasoning: {meta.get('reasoning_type', 'N/A')}")
    print(f"💬 {reply2[:200]}...")


if __name__ == "__main__":
    import sys
    
    # اختر نوع الاختبار
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        print("\n🚀 اختبار سريع...\n")
        asyncio.run(quick_test())
    else:
        print("\n🚀 اختبار مقارنة شامل...\n")
        asyncio.run(test_comparison())
    
    print("\n✨ الاختبار مكتمل!\n")
