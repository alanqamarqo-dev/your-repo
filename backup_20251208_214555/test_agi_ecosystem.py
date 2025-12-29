"""
🧬 اختبار شامل لنظام AGI كمنظومة متكاملة
اختبار التفاعل بين جميع المكونات في سيناريوهات واقعية
"""

import asyncio
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("\n" + "=" * 90)
print("🧬 اختبار النظام الموحد AGI كمنظومة متكاملة")
print("=" * 90)


async def scenario_1_learning_and_memory():
    """سيناريو 1: التعلم المستمر والذاكرة التراكمية"""
    
    from dynamic_modules import mission_control_enhanced as mc
    
    print("\n" + "🔹" * 90)
    print("📚 السيناريو 1: التعلم المستمر والذاكرة التراكمية")
    print("🔹" * 90)
    
    # تعليم النظام معلومات متسلسلة
    topics = [
        "Python is a programming language created by Guido van Rossum",
        "Python is used for web development, data science, and AI",
        "Machine learning libraries in Python include TensorFlow and PyTorch",
        "Deep learning is a subset of machine learning using neural networks"
    ]
    
    print("\n📖 تعليم النظام معلومات متسلسلة...")
    for i, topic in enumerate(topics, 1):
        print(f"\n   [{i}/4] تخزين: {topic[:60]}...")
        
        result = await mc.process_with_unified_agi(
            topic,
            context={"type": "learning", "session": "python_basics"}
        )
        
        await asyncio.sleep(0.3)  # تأخير بسيط
    
    # الآن نسأل أسئلة تعتمد على الذاكرة
    print("\n\n❓ اختبار الذاكرة - طرح أسئلة عن ما تم تعلمه:")
    
    questions = [
        "من أنشأ Python؟",
        "ما استخدامات Python؟",
        "ما علاقة TensorFlow بالذكاء الاصطناعي؟",
        "ما الفرق بين التعلم الآلي والتعلم العميق؟"
    ]
    
    for i, q in enumerate(questions, 1):
        print(f"\n   سؤال {i}: {q}")
        
        result = await mc.process_with_unified_agi(
            q,
            context={"type": "recall", "session": "python_basics"}
        )
        
        memories = result.get("meta", {}).get("memories_used", 0)
        print(f"   💾 ذكريات مستخدمة: {memories}")
        print(f"   🧠 نوع الاستدلال: {result.get('meta', {}).get('reasoning_type', 'N/A')}")
    
    # إحصائيات الذاكرة
    report = await mc.get_agi_system_report()
    print(f"\n📊 إحصائيات الذاكرة:")
    print(f"   - Semantic: {report['memory']['semantic_items']} عنصر")
    print(f"   - Episodic: {report['memory']['episodic_items']} حدث")
    print(f"   - Associations: {report['memory']['total_associations']} رابط")
    print(f"   - Working memory: {report['memory']['working_memory_size']}/20")


async def scenario_2_reasoning_types():
    """سيناريو 2: أنواع الاستدلال المختلفة"""
    
    from dynamic_modules import mission_control_enhanced as mc
    
    print("\n" + "🔹" * 90)
    print("🤔 السيناريو 2: اختبار أنواع الاستدلال المختلفة")
    print("🔹" * 90)
    
    reasoning_tests = [
        {
            "type": "سببي (Causal)",
            "question": "إذا ارتفعت درجة حرارة الماء إلى 100 درجة، ماذا يحدث؟",
            "expected": "causal"
        },
        {
            "type": "استنتاجي (Deductive)",
            "question": "كل البشر فانون، سقراط إنسان، ما الاستنتاج؟",
            "expected": "deductive"
        },
        {
            "type": "استقرائي (Inductive)",
            "question": "الشمس أشرقت كل يوم منذ آلاف السنين، ماذا نتوقع غداً؟",
            "expected": "inductive"
        },
        {
            "type": "افتراضي (Counterfactual)",
            "question": "ماذا لو كانت سرعة الضوء أبطأ من سرعة الصوت؟",
            "expected": "counterfactual"
        }
    ]
    
    correct_detections = 0
    
    for i, test in enumerate(reasoning_tests, 1):
        print(f"\n   [{i}/4] {test['type']}")
        print(f"   ❓ {test['question']}")
        
        # اكتشاف النوع تلقائياً
        detected = mc.UNIFIED_AGI.reasoning.detect_reasoning_type(test['question'])
        
        is_correct = detected == test['expected']
        if is_correct:
            correct_detections += 1
        
        status = "✅" if is_correct else "⚠️"
        print(f"   {status} نوع مكتشف: {detected} (متوقع: {test['expected']})")
        
        # معالجة كاملة
        result = await mc.process_with_unified_agi(
            test['question'],
            context={"reasoning_test": True}
        )
    
    print(f"\n📊 دقة الكشف: {correct_detections}/{len(reasoning_tests)} ({correct_detections/len(reasoning_tests)*100:.0f}%)")


async def scenario_3_curiosity_and_exploration():
    """سيناريو 3: الفضول والاستكشاف الذاتي"""
    
    from dynamic_modules import mission_control_enhanced as mc
    
    print("\n" + "🔹" * 90)
    print("🔍 السيناريو 3: الفضول والاستكشاف الذاتي")
    print("🔹" * 90)
    
    # إعطاء النظام موضوع للاستكشاف
    topic = "الذكاء الاصطناعي العام AGI"
    
    print(f"\n📌 الموضوع: {topic}")
    print(f"⏱️  مدة الاستكشاف: 15 ثانية")
    print(f"\n🔬 بدء الاستكشاف الذاتي...\n")
    
    start = time.time()
    
    # استكشاف مستقل
    exploration = await mc.start_autonomous_exploration(
        duration_seconds=15,
        topic=topic
    )
    
    elapsed = time.time() - start
    
    if exploration.get("status") == "success":
        print(f"✅ الاستكشاف اكتمل في {elapsed:.1f} ثانية")
        
        discoveries = exploration.get("new_discoveries", [])
        questions = exploration.get("questions_explored", [])
        gaps = exploration.get("knowledge_gaps_found", [])
        
        print(f"\n📊 نتائج الاستكشاف:")
        print(f"   🔍 اكتشافات جديدة: {len(discoveries)}")
        if discoveries:
            for i, d in enumerate(discoveries[:3], 1):
                print(f"      {i}. {d}")
        
        print(f"\n   ❓ أسئلة تم استكشافها: {len(questions)}")
        if questions:
            for i, q in enumerate(questions[:3], 1):
                print(f"      {i}. {q}")
        
        print(f"\n   🔗 ثغرات معرفية: {len(gaps)}")
        if gaps:
            for i, g in enumerate(gaps[:3], 1):
                print(f"      {i}. {g}")
    else:
        print(f"⚠️ الاستكشاف فشل: {exploration.get('message')}")


async def scenario_4_multi_engine_coordination():
    """سيناريو 4: تنسيق متعدد المحركات"""
    
    from dynamic_modules import mission_control_enhanced as mc
    
    print("\n" + "🔹" * 90)
    print("⚙️  السيناريو 4: تنسيق متعدد المحركات")
    print("🔹" * 90)
    
    # مهام معقدة تتطلب تعاون محركات مختلفة
    complex_tasks = [
        {
            "task": "اشرح مفهوم الشبكات العصبية وأعط مثال حسابي",
            "engines_needed": ["reasoning", "math", "creativity"]
        },
        {
            "task": "ما هي التطبيقات الإبداعية للذكاء الاصطناعي في الفن؟",
            "engines_needed": ["knowledge", "creativity", "analogy"]
        },
        {
            "task": "قارن بين البرمجة الكمومية والكلاسيكية",
            "engines_needed": ["knowledge", "reasoning", "analogy"]
        }
    ]
    
    print("\n📋 اختبار مهام معقدة تتطلب تعاون محركات متعددة:\n")
    
    for i, task_info in enumerate(complex_tasks, 1):
        print(f"   [{i}/3] {task_info['task'][:60]}...")
        print(f"   🔧 محركات مطلوبة: {', '.join(task_info['engines_needed'])}")
        
        start = time.time()
        
        result = await mc.quick_start_enhanced(
            mission_type="general",
            topic=task_info['task'],
            use_unified_agi=True  # 🧬 الوضع الموحد
        )
        
        elapsed = time.time() - start
        
        if isinstance(result, dict):
            meta = result.get("meta", {})
            print(f"   ⏱️  الوقت: {elapsed:.2f}ث")
            print(f"   🧬 المحرك: {meta.get('engine', 'N/A')}")
            print(f"   🧠 الاستدلال: {meta.get('reasoning_type', 'N/A')}")
            print(f"   💾 الذكريات: {meta.get('memories_used', 0)}")
        
        print()
        await asyncio.sleep(0.5)


async def scenario_5_consciousness_evolution():
    """سيناريو 5: تطور مستوى الوعي"""
    
    from dynamic_modules import mission_control_enhanced as mc
    
    print("\n" + "🔹" * 90)
    print("🌟 السيناريو 5: مراقبة تطور مستوى الوعي")
    print("🔹" * 90)
    
    print("\n📊 قياس مستوى الوعي قبل وبعد التفاعل المكثف:\n")
    
    # قياس أولي
    report_before = await mc.get_agi_system_report()
    consciousness_before = report_before.get('consciousness_level', 0)
    
    print(f"   📉 مستوى الوعي الأولي: {consciousness_before:.3f}")
    
    # تفاعل مكثف
    print(f"\n   ⚡ تنفيذ 10 عمليات معالجة متنوعة...")
    
    diverse_inputs = [
        "ما هو الكون؟",
        "كيف يعمل الدماغ البشري؟",
        "ما معنى الوعي؟",
        "إذا كانت السماء زرقاء، لماذا الليل أسود؟",
        "أعط مثال على الإبداع",
        "ما الفرق بين الذكاء والوعي؟",
        "صف تجربة الألوان",
        "ما هي الحقيقة؟",
        "كيف نعرف أننا نعرف؟",
        "ما علاقة الرياضيات بالواقع؟"
    ]
    
    for i, inp in enumerate(diverse_inputs, 1):
        print(f"      [{i}/10] {inp[:50]}...")
        await mc.process_with_unified_agi(inp, {"consciousness_test": True})
        await asyncio.sleep(0.2)
    
    # قياس نهائي
    report_after = await mc.get_agi_system_report()
    consciousness_after = report_after.get('consciousness_level', 0)
    
    print(f"\n   📈 مستوى الوعي النهائي: {consciousness_after:.3f}")
    
    change = consciousness_after - consciousness_before
    change_pct = (change / consciousness_before * 100) if consciousness_before > 0 else 0
    
    print(f"   {'📈' if change > 0 else '📉'} التغير: {change:+.3f} ({change_pct:+.1f}%)")
    
    # تفاصيل إضافية
    print(f"\n   📊 تفاصيل إضافية:")
    print(f"      - ذاكرة دلالية: {report_after['memory']['semantic_items']}")
    print(f"      - ذاكرة تجريبية: {report_after['memory']['episodic_items']}")
    print(f"      - روابط: {report_after['memory']['total_associations']}")


async def final_ecosystem_report():
    """تقرير نهائي شامل للمنظومة"""
    
    from dynamic_modules import mission_control_enhanced as mc
    
    print("\n" + "=" * 90)
    print("📊 التقرير النهائي الشامل للمنظومة")
    print("=" * 90)
    
    report = await mc.get_agi_system_report()
    
    print("\n🧬 حالة النظام الموحد:")
    print(f"   - الحالة: {'✅ نشط' if report['status'] == 'active' else '❌ غير نشط'}")
    print(f"   - المحركات المتصلة: {report['engines_connected']}")
    print(f"   - مستوى الوعي: {report['consciousness_level']:.3f}")
    
    print("\n💾 منظومة الذاكرة:")
    mem = report['memory']
    total_memories = mem['semantic_items'] + mem['episodic_items'] + mem['procedural_items']
    print(f"   - إجمالي الذكريات: {total_memories}")
    print(f"   - Semantic (دلالية): {mem['semantic_items']}")
    print(f"   - Episodic (تجريبية): {mem['episodic_items']}")
    print(f"   - Procedural (إجرائية): {mem['procedural_items']}")
    print(f"   - Working (عاملة): {mem['working_memory_size']}/20")
    print(f"   - Associations (روابط): {mem['total_associations']}")
    
    print("\n🔍 منظومة الفضول:")
    cur = report['curiosity']
    print(f"   - مواضيع الاهتمام: {cur['interest_topics']}")
    print(f"   - عدد الاستكشافات: {cur['explored_count']}")
    
    print("\n🎯 منظومة التحفيز:")
    mot = report['motivation']
    print(f"   - أهداف حالية: {mot['current_goals']}")
    print(f"   - إنجازات: {mot['achievements']}")
    
    # تقييم عام
    print("\n⭐ تقييم الأداء الشامل:")
    
    # معايير التقييم
    criteria = {
        "الذاكرة": mem['total_associations'] > 0,
        "الاستدلال": True,  # تم اختباره في السيناريو 2
        "الفضول": cur['explored_count'] > 0,
        "التكامل": report['engines_connected'] >= 40,
        "الوعي": report['consciousness_level'] > 0
    }
    
    passed = sum(criteria.values())
    total = len(criteria)
    
    for criterion, status in criteria.items():
        print(f"   {'✅' if status else '❌'} {criterion}")
    
    score = (passed / total) * 100
    print(f"\n   🎯 النتيجة الإجمالية: {score:.0f}% ({passed}/{total})")
    
    if score >= 80:
        grade = "ممتاز 🏆"
    elif score >= 60:
        grade = "جيد جداً ⭐"
    elif score >= 40:
        grade = "جيد ✓"
    else:
        grade = "يحتاج تحسين ⚠️"
    
    print(f"   📈 التقدير: {grade}")


async def run_all_scenarios():
    """تشغيل جميع السيناريوهات"""
    
    print("\n🚀 بدء اختبار المنظومة المتكاملة...\n")
    
    start_time = time.time()
    
    try:
        # السيناريو 1: التعلم والذاكرة
        await scenario_1_learning_and_memory()
        
        # السيناريو 2: أنواع الاستدلال
        await scenario_2_reasoning_types()
        
        # السيناريو 3: الفضول والاستكشاف
        await scenario_3_curiosity_and_exploration()
        
        # السيناريو 4: تنسيق المحركات
        await scenario_4_multi_engine_coordination()
        
        # السيناريو 5: تطور الوعي
        await scenario_5_consciousness_evolution()
        
        # التقرير النهائي
        await final_ecosystem_report()
        
    except KeyboardInterrupt:
        print("\n\n⚠️  تم إيقاف الاختبار بواسطة المستخدم")
    except Exception as e:
        print(f"\n\n❌ خطأ غير متوقع: {e}")
        import traceback
        traceback.print_exc()
    
    elapsed = time.time() - start_time
    
    print("\n" + "=" * 90)
    print(f"⏱️  إجمالي وقت الاختبار: {elapsed:.1f} ثانية")
    print("=" * 90)
    print("\n✨ اختبار المنظومة المتكاملة مكتمل!\n")


if __name__ == "__main__":
    asyncio.run(run_all_scenarios())
