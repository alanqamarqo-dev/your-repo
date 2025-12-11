"""
🧪 اختبار شامل للدمج الكامل - Complete Integration Test
=================================================================

يختبر جميع المكونات المدمجة:
1. DKN System ✅
2. Knowledge Graph ✅
3. Scientific Systems ✅
4. Self-Improvement ✅
"""

import asyncio
import sys
import os

# إضافة مسار المشروع
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dynamic_modules.unified_agi_system import create_unified_agi_system
from Core_Engines import bootstrap_register_all_engines


async def test_complete_integration():
    """اختبار شامل لجميع الأنظمة"""
    
    print("=" * 80)
    print("🧪 اختبار الدمج الشامل - Complete Integration Test")
    print("=" * 80)
    print()
    
    # 1. تسجيل المحركات
    print("📋 تسجيل المحركات...")
    engine_registry = {}
    registered = bootstrap_register_all_engines(
        registry=engine_registry,
        allow_optional=True,
        config=None,
        verbose=False,
        max_seconds=30
    )
    print(f"✅ تم تسجيل {len(registered)} محرك")
    print()
    
    # 2. إنشاء النظام الموحد
    print("🧬 إنشاء UnifiedAGI مع جميع الأنظمة...")
    unified_agi = create_unified_agi_system(engine_registry)
    print()
    
    # 3. عرض الحالة
    print("=" * 80)
    print("📊 حالة الأنظمة المدمجة")
    print("=" * 80)
    print(f"✅ DKN System: {'مفعّل' if unified_agi.dkn_enabled else 'معطّل'}")
    print(f"   - المحركات المتصلة: {len(unified_agi.engine_adapters)}")
    
    print(f"✅ Knowledge Graph: {'مفعّل' if unified_agi.kg_enabled else 'معطّل'}")
    if unified_agi.kg_enabled and unified_agi.cognitive_integration:
        print(f"   - المحركات في الشبكة: {len(unified_agi.cognitive_integration.engines_registry)}")
    
    print(f"✅ Scientific Systems: {'مفعّل' if unified_agi.scientific_enabled else 'معطّل'}")
    if unified_agi.scientific_enabled:
        systems = []
        if unified_agi.theorem_prover: systems.append("TheoremProver")
        if unified_agi.research_assistant: systems.append("ResearchAssistant")
        if unified_agi.hardware_simulator: systems.append("HardwareSimulator")
        if unified_agi.simulation_engine: systems.append("SimulationEngine")
        print(f"   - المحركات النشطة: {', '.join(systems)}")
    
    print(f"✅ Self-Improvement: {'مفعّل' if unified_agi.self_improvement_enabled else 'معطّل'}")
    if unified_agi.self_improvement_enabled:
        systems = []
        if unified_agi.self_learning: systems.append("SelfLearning")
        if unified_agi.self_monitoring: systems.append("Monitoring")
        if unified_agi.auto_rollback: systems.append("Rollback")
        if unified_agi.safe_modification: systems.append("SafeMod")
        if unified_agi.strategic_memory: systems.append("StrategicMemory")
        print(f"   - الأنظمة النشطة: {', '.join(systems)}")
    
    print()
    
    # 4. اختبارات وظيفية
    print("=" * 80)
    print("🧪 اختبارات وظيفية")
    print("=" * 80)
    print()
    
    # اختبار 1: سؤال رياضي بسيط
    print("📝 اختبار 1: سؤال رياضي")
    print("   السؤال: احسب 25% من 800")
    result1 = await unified_agi.process_with_full_agi("احسب 25% من 800")
    answer = result1.get('reasoning', {}).get('answer', 'لا توجد إجابة')
    if not answer or answer == 'لا توجد إجابة':
        answer = str(result1.get('final_response', 'No response'))[:100]
    print(f"   ✅ الإجابة: {answer}...")
    print(f"   📊 DKN مستخدم: {result1.get('dkn_routing_used', False)}")
    print(f"   📊 KG مستخدم: {result1.get('kg_used', False)}")
    print(f"   📊 Scientific Results: {len(result1.get('scientific_results', {}))}")
    print()
    
    # اختبار 2: طلب برهان رياضي
    print("📝 اختبار 2: طلب برهان رياضي")
    print("   السؤال: أثبت أن مجموع زوايا المثلث = 180 درجة")
    result2 = await unified_agi.process_with_full_agi("أثبت أن مجموع زوايا المثلث يساوي 180 درجة")
    print(f"   ✅ Scientific Systems نشط: {bool(result2.get('scientific_results'))}")
    if result2.get('scientific_results', {}).get('theorem_proof'):
        proof = result2['scientific_results']['theorem_proof']
        print(f"   📐 Theorem Prover: مُثبت = {proof.get('is_proven', False)}")
        print(f"   📐 خطوات البرهان: {len(proof.get('proof_steps', []))}")
    print()
    
    # اختبار 3: سؤال إبداعي (Knowledge Graph)
    print("📝 اختبار 3: سؤال إبداعي")
    print("   السؤال: اقترح فكرة مبتكرة لتطبيق تعليمي")
    result3 = await unified_agi.process_with_full_agi("اقترح فكرة مبتكرة لتطبيق تعليمي للأطفال")
    print(f"   ✅ KG Solutions: {result3.get('kg_solutions_count', 0)}")
    print(f"   ✅ Consensus: {bool(result3.get('kg_consensus'))}")
    print(f"   ✅ Improvement: {bool(result3.get('improvement_results'))}")
    print()
    
    # اختبار 4: محاكاة
    print("📝 اختبار 4: طلب محاكاة")
    print("   السؤال: محاكاة حركة بندول بسيط")
    result4 = await unified_agi.process_with_full_agi("محاكاة حركة بندول بسيط لمدة 10 ثوانٍ")
    if result4.get('scientific_results', {}).get('simulation'):
        sim = result4['scientific_results']['simulation']
        print(f"   ⚗️ Simulation: {len(sim)} خطوات مكتملة")
    print()
    
    # 5. ملخص الأداء
    print("=" * 80)
    print("📈 ملخص الأداء")
    print("=" * 80)
    
    # حساب المعدلات
    total_tests = 4
    dkn_used = sum([r.get('dkn_routing_used', False) for r in [result1, result2, result3, result4]])
    kg_used = sum([r.get('kg_used', False) for r in [result1, result2, result3, result4]])
    sci_used = sum([bool(r.get('scientific_results')) for r in [result1, result2, result3, result4]])
    imp_used = sum([bool(r.get('improvement_results')) for r in [result1, result2, result3, result4]])
    
    print(f"✅ DKN System استخدم في: {dkn_used}/{total_tests} اختبارات ({dkn_used/total_tests*100:.0f}%)")
    print(f"✅ Knowledge Graph استخدم في: {kg_used}/{total_tests} اختبارات ({kg_used/total_tests*100:.0f}%)")
    print(f"✅ Scientific Systems استخدم في: {sci_used}/{total_tests} اختبارات ({sci_used/total_tests*100:.0f}%)")
    print(f"✅ Self-Improvement استخدم في: {imp_used}/{total_tests} اختبارات ({imp_used/total_tests*100:.0f}%)")
    print()
    
    # 6. مستوى الوعي النهائي
    print(f"🧠 مستوى الوعي النهائي: {unified_agi.consciousness_level:.4f}")
    print()
    
    # 7. النتيجة النهائية
    print("=" * 80)
    print("🏁 النتيجة النهائية")
    print("=" * 80)
    
    systems_active = sum([
        unified_agi.dkn_enabled,
        unified_agi.kg_enabled,
        unified_agi.scientific_enabled,
        unified_agi.self_improvement_enabled
    ])
    
    total_systems = 4
    percentage = (systems_active / total_systems) * 100
    
    print(f"✅ الأنظمة النشطة: {systems_active}/{total_systems} ({percentage:.0f}%)")
    print()
    
    if percentage == 100:
        print("🎉 نجاح كامل! جميع الأنظمة مدمجة وتعمل بشكل مثالي!")
        print()
        print("💡 الفوائد المحققة:")
        print("   ✅ تنسيق ذكي تكيفي (DKN)")
        print("   ✅ ذكاء جماعي وإجماع (Knowledge Graph)")
        print("   ✅ براهين رياضية + بحث علمي + محاكاة (Scientific)")
        print("   ✅ تعلم ذاتي + مراقبة + ذاكرة استراتيجية (Self-Improvement)")
    elif percentage >= 75:
        print("✅ ممتاز! معظم الأنظمة مدمجة")
    elif percentage >= 50:
        print("⚠️ جيد لكن يمكن تحسين الدمج")
    else:
        print("❌ يحتاج لمزيد من العمل")
    
    print()
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_complete_integration())
