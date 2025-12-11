"""
🌐 اختبار نظام AGI الموحد مع مزود LLM خارجي حقيقي
اختبار كامل مع Ollama/Qwen2.5 للحصول على إجابات فعلية
"""

import asyncio
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("\n" + "=" * 90)
print("🌐 اختبار نظام AGI الموحد مع مزود LLM خارجي (Ollama)")
print("=" * 90)


async def test_with_real_llm():
    """اختبار شامل مع LLM حقيقي"""
    
    from dynamic_modules import mission_control_enhanced as mc
    
    if not mc.UNIFIED_AGI:
        print("\n❌ UNIFIED_AGI غير متاح!")
        return False
    
    print("\n✅ النظام الموحد متصل ونشط")
    print(f"📡 النموذج: qwen2.5:3b-instruct")
    print(f"🔗 المحركات المتصلة: 46")
    
    # === اختبار 1: سؤال بسيط ===
    print("\n" + "▸" * 90)
    print("📝 الاختبار 1: سؤال معرفي بسيط")
    print("▸" * 90)
    
    question1 = "ما هو الذكاء الاصطناعي العام AGI؟"
    print(f"\n❓ السؤال: {question1}")
    print(f"⏳ جاري المعالجة مع LLM الخارجي...")
    
    start = time.time()
    result1 = await mc.process_with_unified_agi(
        question1,
        context={"test": "real_llm", "type": "knowledge"}
    )
    elapsed1 = time.time() - start
    
    if result1.get("status") == "success":
        reply = result1.get("reply", "")
        print(f"\n✅ تم الاستلام في {elapsed1:.2f} ثانية")
        print(f"📊 طول الإجابة: {len(reply)} حرف")
        print(f"\n💬 الإجابة:")
        print(f"{'─' * 90}")
        print(reply if reply else "(لا توجد إجابة - قد يكون LLM غير متصل)")
        print(f"{'─' * 90}")
        
        meta = result1.get("meta", {})
        print(f"\n📊 معلومات إضافية:")
        print(f"   🧠 نوع الاستدلال: {meta.get('reasoning_type', 'N/A')}")
        print(f"   💾 ذكريات مستخدمة: {meta.get('memories_used', 0)}")
        print(f"   🎨 إبداع مطبق: {'نعم' if meta.get('creativity_applied') else 'لا'}")
    else:
        print(f"\n⚠️ فشل: {result1.get('message', 'unknown error')}")
    
    # === اختبار 2: سؤال استدلالي ===
    print("\n" + "▸" * 90)
    print("🤔 الاختبار 2: سؤال استدلالي معقد")
    print("▸" * 90)
    
    question2 = "إذا كان جميع البشر فانون، وسقراط إنسان، ما الاستنتاج المنطقي؟ اشرح السبب."
    print(f"\n❓ السؤال: {question2}")
    print(f"⏳ جاري المعالجة...")
    
    start = time.time()
    result2 = await mc.quick_start_enhanced(
        mission_type="general",
        topic=question2,
        use_unified_agi=True  # 🧬 الوضع الموحد
    )
    elapsed2 = time.time() - start
    
    if isinstance(result2, dict):
        reply = result2.get("reply_text") or result2.get("reply", "")
        print(f"\n✅ تم الاستلام في {elapsed2:.2f} ثانية")
        print(f"📊 طول الإجابة: {len(reply)} حرف")
        print(f"\n💬 الإجابة:")
        print(f"{'─' * 90}")
        print(reply if reply else "(لا توجد إجابة)")
        print(f"{'─' * 90}")
        
        meta = result2.get("meta", {})
        if meta:
            print(f"\n📊 معلومات إضافية:")
            print(f"   🧬 المحرك: {meta.get('engine', 'N/A')}")
            print(f"   🧠 نوع الاستدلال: {meta.get('reasoning_type', 'N/A')}")
    
    # === اختبار 3: سؤال إبداعي ===
    print("\n" + "▸" * 90)
    print("🎨 الاختبار 3: سؤال إبداعي")
    print("▸" * 90)
    
    question3 = "اقترح فكرة مبتكرة لاستخدام الذكاء الاصطناعي في التعليم"
    print(f"\n❓ السؤال: {question3}")
    print(f"⏳ جاري المعالجة...")
    
    start = time.time()
    result3 = await mc.process_with_unified_agi(
        question3,
        context={"type": "creative", "domain": "education"}
    )
    elapsed3 = time.time() - start
    
    if result3.get("status") == "success":
        reply = result3.get("reply", "")
        print(f"\n✅ تم الاستلام في {elapsed3:.2f} ثانية")
        print(f"📊 طول الإجابة: {len(reply)} حرف")
        print(f"\n💬 الإجابة:")
        print(f"{'─' * 90}")
        print(reply if reply else "(لا توجد إجابة)")
        print(f"{'─' * 90}")
    
    # === اختبار 4: التعلم من المحادثة ===
    print("\n" + "▸" * 90)
    print("🧠 الاختبار 4: التعلم المستمر والذاكرة")
    print("▸" * 90)
    
    # تعليم النظام
    learning_facts = [
        "الشمس نجم في مركز النظام الشمسي",
        "الأرض تدور حول الشمس في 365 يوماً",
        "القمر يدور حول الأرض في 28 يوماً"
    ]
    
    print(f"\n📖 تعليم النظام {len(learning_facts)} حقائق...")
    for i, fact in enumerate(learning_facts, 1):
        print(f"   [{i}/3] {fact}")
        await mc.process_with_unified_agi(fact, {"type": "learning", "session": "astronomy"})
        await asyncio.sleep(0.3)
    
    # الآن نسأل سؤال يعتمد على الذاكرة
    print(f"\n❓ اختبار الذاكرة: 'كم يوماً تستغرق الأرض للدوران حول الشمس؟'")
    print(f"⏳ جاري المعالجة...")
    
    start = time.time()
    result4 = await mc.process_with_unified_agi(
        "كم يوماً تستغرق الأرض للدوران حول الشمس؟",
        context={"type": "recall", "session": "astronomy"}
    )
    elapsed4 = time.time() - start
    
    if result4.get("status") == "success":
        reply = result4.get("reply", "")
        memories_used = result4.get("meta", {}).get("memories_used", 0)
        
        print(f"\n✅ تم الاستلام في {elapsed4:.2f} ثانية")
        print(f"💾 استخدم {memories_used} ذكريات سابقة")
        print(f"\n💬 الإجابة:")
        print(f"{'─' * 90}")
        print(reply if reply else "(لا توجد إجابة)")
        print(f"{'─' * 90}")
        
        # التحقق من استخدام الذاكرة
        if memories_used > 0:
            print(f"\n✅ النظام استخدم الذاكرة بنجاح! 🎯")
        elif "365" in reply:
            print(f"\n✅ النظام أجاب بشكل صحيح (قد يكون من معرفته الخاصة أو الذاكرة)")
    
    # === اختبار 5: افتراضي (Counterfactual) ===
    print("\n" + "▸" * 90)
    print("🔮 الاختبار 5: سؤال افتراضي (What-if)")
    print("▸" * 90)
    
    question5 = "ماذا لو كانت سرعة الضوء أبطأ من سرعة الصوت؟ كيف سيبدو العالم؟"
    print(f"\n❓ السؤال: {question5}")
    print(f"⏳ جاري المعالجة...")
    
    start = time.time()
    result5 = await mc.process_with_unified_agi(
        question5,
        context={"type": "counterfactual"}
    )
    elapsed5 = time.time() - start
    
    if result5.get("status") == "success":
        reply = result5.get("reply", "")
        reasoning_type = result5.get("meta", {}).get("reasoning_type", "N/A")
        
        print(f"\n✅ تم الاستلام في {elapsed5:.2f} ثانية")
        print(f"🧠 نوع الاستدلال المكتشف: {reasoning_type}")
        print(f"\n💬 الإجابة:")
        print(f"{'─' * 90}")
        print(reply if reply else "(لا توجد إجابة)")
        print(f"{'─' * 90}")
        
        if reasoning_type == "counterfactual":
            print(f"\n✅ النظام اكتشف نوع الاستدلال بشكل صحيح! 🎯")
    
    # === التقرير النهائي ===
    print("\n" + "=" * 90)
    print("📊 التقرير النهائي")
    print("=" * 90)
    
    report = await mc.get_agi_system_report()
    
    print(f"\n🧬 حالة النظام:")
    print(f"   ✅ الحالة: {report['status']}")
    print(f"   🔗 المحركات: {report['engines_connected']}")
    print(f"   🌟 مستوى الوعي: {report['consciousness_level']:.3f}")
    
    print(f"\n💾 الذاكرة:")
    mem = report['memory']
    total = mem['semantic_items'] + mem['episodic_items'] + mem['procedural_items']
    print(f"   📚 إجمالي الذكريات: {total}")
    print(f"   - Semantic: {mem['semantic_items']}")
    print(f"   - Episodic: {mem['episodic_items']}")
    print(f"   - Procedural: {mem['procedural_items']}")
    print(f"   - Working: {mem['working_memory_size']}/20")
    print(f"   🔗 Associations: {mem['total_associations']}")
    
    print(f"\n⏱️  أوقات الاستجابة:")
    avg_time = (elapsed1 + elapsed2 + elapsed3 + elapsed4 + elapsed5) / 5
    print(f"   - الاختبار 1: {elapsed1:.2f}ث")
    print(f"   - الاختبار 2: {elapsed2:.2f}ث")
    print(f"   - الاختبار 3: {elapsed3:.2f}ث")
    print(f"   - الاختبار 4: {elapsed4:.2f}ث")
    print(f"   - الاختبار 5: {elapsed5:.2f}ث")
    print(f"   📊 المتوسط: {avg_time:.2f}ث")
    
    return True


async def test_simple_conversation():
    """محادثة بسيطة لاختبار سريع"""
    
    from dynamic_modules import mission_control_enhanced as mc
    
    print("\n" + "=" * 90)
    print("💬 اختبار محادثة بسيطة")
    print("=" * 90)
    
    questions = [
        "ما هو 2 + 2؟",
        "من هو ألبرت أينشتاين؟",
        "اشرح لي البرمجة بكلمات بسيطة"
    ]
    
    for i, q in enumerate(questions, 1):
        print(f"\n[{i}/3] ❓ {q}")
        print(f"⏳ انتظار الإجابة...")
        
        start = time.time()
        result = await mc.quick_start_enhanced(
            mission_type="general",
            topic=q,
            use_unified_agi=True
        )
        elapsed = time.time() - start
        
        if isinstance(result, dict):
            reply = result.get("reply_text") or result.get("reply", "")
            print(f"✅ ({elapsed:.2f}ث)")
            print(f"💬 {reply[:200]}{'...' if len(reply) > 200 else ''}")
        
        await asyncio.sleep(0.5)


if __name__ == "__main__":
    import sys
    
    print("\n🚀 بدء الاختبار مع LLM الخارجي...")
    print("📡 النموذج: qwen2.5:3b-instruct")
    print("🌐 المزود: Ollama")
    
    if len(sys.argv) > 1 and sys.argv[1] == "--simple":
        print("\n🎯 وضع الاختبار البسيط\n")
        asyncio.run(test_simple_conversation())
    else:
        print("\n🎯 وضع الاختبار الشامل\n")
        asyncio.run(test_with_real_llm())
    
    print("\n✨ الاختبار مكتمل!\n")
