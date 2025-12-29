"""
اختبار تفصيلي للنظام الموحد - فحص المكونات الداخلية
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 80)
print("🔬 اختبار تفصيلي للنظام الموحد AGI")
print("=" * 80)


async def test_unified_system_components():
    """اختبار مفصل للمكونات الداخلية"""
    
    from dynamic_modules import mission_control_enhanced as mc
    
    if not mc.UNIFIED_AGI:
        print("\n❌ UNIFIED_AGI غير متاح!")
        return
    
    print("\n✅ UNIFIED_AGI نشط ومتاح\n")
    
    # ========== اختبار 1: الذاكرة ==========
    print("=" * 80)
    print("🧠 اختبار 1: نظام الذاكرة")
    print("=" * 80)
    
    # تخزين معلومة
    memory_item = mc.UNIFIED_AGI.memory.store(
        content="الذكاء الاصطناعي العام (AGI) هو نظام قادر على فهم وتعلم أي مهمة معرفية",
        memory_type="semantic",
        importance=0.9,
        emotional_tag="interesting",
        context={"topic": "AGI"}
    )
    print(f"✅ تم تخزين معلومة: ID={memory_item['id']}")
    
    # استرجاع المعلومة
    recalled = mc.UNIFIED_AGI.memory.recall(
        query="ما هو AGI",
        memory_type="semantic",
        context={"topic": "AGI"}
    )
    print(f"✅ تم استرجاع {len(recalled)} ذكريات")
    if recalled:
        print(f"   📝 المحتوى: {recalled[0]['content'][:80]}...")
    
    # ========== اختبار 2: الاستدلال ==========
    print("\n" + "=" * 80)
    print("🤔 اختبار 2: محرك الاستدلال")
    print("=" * 80)
    
    # اكتشاف نوع الاستدلال
    problem1 = "إذا زادت الحرارة، فإن الجليد يذوب. الحرارة زادت. ماذا يحدث؟"
    reasoning_type1 = mc.UNIFIED_AGI.reasoning.detect_reasoning_type(problem1)
    print(f"✅ نوع الاستدلال المكتشف: {reasoning_type1}")
    
    problem2 = "ماذا لو لم تكن الجاذبية موجودة على الأرض؟"
    reasoning_type2 = mc.UNIFIED_AGI.reasoning.detect_reasoning_type(problem2)
    print(f"✅ نوع الاستدلال المكتشف: {reasoning_type2}")
    
    # ========== اختبار 3: الفضول ==========
    print("\n" + "=" * 80)
    print("🔍 اختبار 3: محرك الفضول")
    print("=" * 80)
    
    # تحديد الثغرات المعرفية
    gaps = mc.UNIFIED_AGI.curiosity.identify_knowledge_gaps()
    print(f"✅ تم تحديد {len(gaps)} ثغرة معرفية")
    for i, gap in enumerate(gaps[:3], 1):
        print(f"   {i}. {gap}")
    
    # توليد أسئلة
    questions = mc.UNIFIED_AGI.curiosity.generate_questions("الذكاء الاصطناعي")
    print(f"\n✅ تم توليد {len(questions)} أسئلة:")
    for i, q in enumerate(questions[:3], 1):
        print(f"   {i}. {q}")
    
    # ========== اختبار 4: التحفيز ==========
    print("\n" + "=" * 80)
    print("🎯 اختبار 4: نظام التحفيز الداخلي")
    print("=" * 80)
    
    current_state = {
        "knowledge_level": 0.6,
        "skills": ["reasoning", "memory"],
        "recent_activities": ["learning", "exploring"]
    }
    
    achievements = [
        {"type": "learning", "description": "learned about AGI"},
        {"type": "problem_solving", "description": "solved reasoning task"}
    ]
    
    # توليد أهداف
    goals = mc.UNIFIED_AGI.motivation.generate_goals(current_state, achievements)
    print(f"✅ تم توليد {len(goals)} أهداف:")
    for i, goal in enumerate(goals[:5], 1):
        print(f"   {i}. [{goal['priority']}] {goal['description']}")
    
    # ========== اختبار 5: المعالجة الكاملة ==========
    print("\n" + "=" * 80)
    print("🧬 اختبار 5: المعالجة الكاملة بـ AGI")
    print("=" * 80)
    
    test_input = "كيف يمكن للذكاء الاصطناعي مساعدة البشرية؟"
    print(f"📥 المدخل: {test_input}")
    
    result = await mc.UNIFIED_AGI.process_with_full_agi(
        input_text=test_input,
        context={"priority": "high", "domain": "AI"}
    )
    
    print(f"\n✅ المعالجة مكتملة:")
    print(f"   🧠 نوع الاستدلال: {result.get('reasoning_type', 'N/A')}")
    print(f"   💾 ذكريات مسترجعة: {len(result.get('memories_recalled', []))}")
    print(f"   🎨 إبداع مطبق: {'نعم' if result.get('creativity_applied') else 'لا'}")
    print(f"   🔍 ثغرات مكتشفة: {len(result.get('curiosity_gaps', []))}")
    print(f"   🎯 أهداف جديدة: {len(result.get('new_goals', []))}")
    
    final_response = result.get('final_response', '')
    if final_response:
        print(f"\n   💬 الرد النهائي: {final_response[:200]}...")
    else:
        print(f"\n   ℹ️  لا يوجد رد نهائي (قد يحتاج LLM)")
    
    # ========== تقرير الحالة النهائية ==========
    print("\n" + "=" * 80)
    print("📊 تقرير الحالة النهائية")
    print("=" * 80)
    
    report = await mc.get_agi_system_report()
    
    print(f"\n💾 الذاكرة:")
    print(f"   - Semantic: {report['memory']['semantic_items']} عنصر")
    print(f"   - Episodic: {report['memory']['episodic_items']} عنصر")
    print(f"   - Procedural: {report['memory']['procedural_items']} عنصر")
    print(f"   - Working: {report['memory']['working_memory_size']}/20")
    print(f"   - Associations: {report['memory']['total_associations']} رابط")
    
    print(f"\n🔍 الفضول:")
    print(f"   - Interest topics: {report['curiosity']['interest_topics']}")
    print(f"   - Explored: {report['curiosity']['explored_count']}")
    
    print(f"\n🎯 التحفيز:")
    print(f"   - Goals: {report['motivation']['current_goals']}")
    print(f"   - Achievements: {report['motivation']['achievements']}")
    
    print(f"\n🧬 عام:")
    print(f"   - Consciousness: {report['consciousness_level']}")
    print(f"   - Engines: {report['engines_connected']}")
    
    print("\n" + "=" * 80)
    print("✅ جميع الاختبارات التفصيلية اكتملت!")
    print("=" * 80)


async def test_memory_associations():
    """اختبار الروابط التلقائية في الذاكرة"""
    
    from dynamic_modules import mission_control_enhanced as mc
    
    if not mc.UNIFIED_AGI:
        return
    
    print("\n" + "=" * 80)
    print("🔗 اختبار إضافي: الروابط التلقائية في الذاكرة")
    print("=" * 80)
    
    # تخزين عدة معلومات مترابطة
    items = [
        "الذكاء الاصطناعي يستخدم خوارزميات للتعلم",
        "التعلم الآلي هو فرع من الذكاء الاصطناعي",
        "الشبكات العصبية تحاكي الدماغ البشري",
        "التعلم العميق يستخدم شبكات عصبية متعددة الطبقات"
    ]
    
    print(f"\n📝 تخزين {len(items)} معلومات مترابطة...")
    for i, content in enumerate(items, 1):
        mc.UNIFIED_AGI.memory.store(
            content=content,
            memory_type="semantic",
            importance=0.8,
            emotional_tag="educational",
            context={"domain": "AI", "session": "test"}
        )
        print(f"   ✅ {i}. تم التخزين")
    
    # استرجاع بكلمات مختلفة
    print(f"\n🔍 اختبار الاسترجاع بكلمات مختلفة:")
    
    queries = [
        "ما هو التعلم",
        "أخبرني عن الشبكات",
        "كيف يعمل الذكاء"
    ]
    
    for query in queries:
        recalled = mc.UNIFIED_AGI.memory.recall(
            query=query,
            memory_type="semantic",
            context={"domain": "AI"}
        )
        print(f"\n   📋 '{query}' → {len(recalled)} نتيجة")
        for item in recalled[:2]:
            print(f"      • {item['content'][:60]}...")
    
    # عرض الروابط
    print(f"\n🔗 فحص الروابط التلقائية:")
    assoc_index = mc.UNIFIED_AGI.memory.association_index
    print(f"   إجمالي الكلمات المفهرسة: {len(assoc_index)}")
    
    # عرض بعض الكلمات المفهرسة
    sample_words = list(assoc_index.keys())[:10]
    for word in sample_words:
        ids = assoc_index[word]
        print(f"   '{word}' → {len(ids)} ذكريات مرتبطة")


if __name__ == "__main__":
    print("\n🚀 بدء الاختبار التفصيلي...\n")
    
    asyncio.run(test_unified_system_components())
    asyncio.run(test_memory_associations())
    
    print("\n✨ اختبار مكتمل!\n")
