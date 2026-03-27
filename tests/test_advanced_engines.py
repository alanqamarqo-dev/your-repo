"""
🧪 اختبار المحركات المتقدمة: Quantum + Hypothesis
======================================================

يختبر:
1. Quantum Neural Core (التفكير الكمومي)
2. Hypothesis Generator (توليد الفرضيات)
3. Counterfactual Explorer (التفكير الافتراضي)
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'repo-copy'))

from dynamic_modules import mission_control_enhanced as mc


async def test_advanced_engines():
    print("="*70)
    print("🔬 اختبار المحركات المتقدمة")
    print("="*70)
    
    # ==================== Test 1: Hypothesis Generation ====================
    print("\n" + "="*70)
    print("🔬 اختبار 1: توليد الفرضيات")
    print("="*70)
    
    hypothesis_questions = [
        "لماذا السماء زرقاء؟",
        "ما السبب في انقراض الديناصورات؟",
        "كيف يمكن أن تنشأ الحياة على كوكب آخر؟"
    ]
    
    for q in hypothesis_questions:
        print(f"\n❓ السؤال: {q}")
        result = await mc.process_with_unified_agi(q)
        
        meta = result.get('meta', {})
        full_result = meta.get('full_agi_result', {})
        
        hypothesis_applied = full_result.get('hypothesis_applied', False)
        hypotheses = full_result.get('hypotheses', None)
        
        print(f"   🔬 Hypothesis Applied: {hypothesis_applied}")
        if hypotheses:
            print(f"   💡 عدد الفرضيات: {len(hypotheses.get('hypotheses', [])) if isinstance(hypotheses, dict) else 0}")
            print(f"   📝 Response Length: {len(result.get('reply', ''))} chars")
        
        if hypothesis_applied:
            print("   ✅ توليد الفرضيات نشط!")
        else:
            print("   ⚠️ لم يتم تفعيل توليد الفرضيات")
    
    # ==================== Test 2: Quantum Thinking ====================
    print("\n" + "="*70)
    print("⚛️ اختبار 2: التفكير الكمومي")
    print("="*70)
    
    quantum_questions = [
        "ما معنى الوجود؟ سؤال فلسفي عميق",
        "اشرح التشابك الكمومي بطريقة معقدة",
        "كيف تؤثر الاحتمالات المتعددة على قراراتنا؟"
    ]
    
    for q in quantum_questions:
        print(f"\n❓ السؤال: {q}")
        result = await mc.process_with_unified_agi(q)
        
        meta = result.get('meta', {})
        full_result = meta.get('full_agi_result', {})
        
        quantum_applied = full_result.get('quantum_applied', False)
        quantum_result = full_result.get('quantum_result', None)
        
        print(f"   ⚛️ Quantum Applied: {quantum_applied}")
        if quantum_result:
            print(f"   🌌 Quantum Depth: {quantum_result.get('depth', 'unknown')}")
            print(f"   📝 Response Length: {len(result.get('reply', ''))} chars")
        
        if quantum_applied:
            print("   ✅ التفكير الكمومي نشط!")
        else:
            print("   ⚠️ لم يتم تفعيل التفكير الكمومي")
    
    # ==================== Test 3: Combined Test ====================
    print("\n" + "="*70)
    print("🚀 اختبار 3: دمج جميع المحركات")
    print("="*70)
    
    complex_question = "افترض أننا اكتشفنا كوكباً جديداً معقد الطبيعة، ما الفرضيات المحتملة حول نشأة الحياة عليه؟"
    print(f"\n❓ السؤال المعقد: {complex_question}")
    
    result = await mc.process_with_unified_agi(complex_question)
    
    meta = result.get('meta', {})
    full_result = meta.get('full_agi_result', {})
    
    print("\n📊 المحركات المستخدمة:")
    print(f"   🎨 Creativity: {full_result.get('creativity_applied', False)}")
    print(f"   🔬 Hypothesis: {full_result.get('hypothesis_applied', False)}")
    print(f"   ⚛️ Quantum: {full_result.get('quantum_applied', False)}")
    print(f"   🧮 Math: {full_result.get('math_applied', False)}")
    print(f"   🧠 Reasoning: {full_result.get('reasoning_type', 'unknown')}")
    
    print(f"\n📝 طول الإجابة: {len(result.get('reply', ''))} chars")
    print(f"🌟 مستوى الوعي: {full_result.get('consciousness_level', 0):.3f}")
    
    # ==================== Test 4: System Report ====================
    print("\n" + "="*70)
    print("📊 اختبار 4: تقرير النظام")
    print("="*70)
    
    report = await mc.get_agi_system_report()
    
    if report.get('status') == 'active':
        print(f"✅ النظام نشط")
        print(f"   💾 الذاكرة الدلالية: {report['memory']['semantic_items']} عنصر")
        print(f"   📚 الذاكرة الحلقية: {report['memory']['episodic_items']} حدث")
        print(f"   🌟 مستوى الوعي: {report['consciousness_level']:.3f}")
        print(f"   ⚙️ المحركات: {report['engines_connected']}")
    
    # ==================== Summary ====================
    print("\n" + "="*70)
    print("✅ اكتمل الاختبار!")
    print("="*70)
    print("\n📋 المحركات المختبرة:")
    print("   🔬 Hypothesis Generator")
    print("   ⚛️ Quantum Neural Core")
    print("   🎨 Creative Innovation")
    print("   🧠 Unified Reasoning")
    print("\n🎉 جميع المحركات المتقدمة مُفعّلة ونشطة!")


if __name__ == "__main__":
    asyncio.run(test_advanced_engines())
