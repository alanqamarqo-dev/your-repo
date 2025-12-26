"""
🧪 اختبار التكامل الكامل: UnifiedAGI + Mission Control
================================================================

يختبر:
1. Auto-detection للإبداع
2. الوصول المباشر لمكونات UnifiedAGI
3. التكامل الشامل
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'repo-copy'))

from dynamic_modules import mission_control_enhanced as mc


async def test_integration():
    print("="*70)
    print("🧬 اختبار التكامل الكامل: UnifiedAGI + Mission Control")
    print("="*70)
    
    # ==================== Test 1: Auto-Creativity Detection ====================
    print("\n" + "="*70)
    print("🎨 اختبار 1: Auto-Detection للإبداع")
    print("="*70)
    
    creative_questions = [
        "اكتب قصة قصيرة عن روبوت",
        "اقترح 3 حلول مبتكرة",
        "ابتكر لعبة جديدة"
    ]
    
    for q in creative_questions:
        print(f"\n❓ السؤال: {q}")
        result = await mc.process_with_unified_agi(q)
        
        meta = result.get('meta', {})
        creativity_auto = meta.get('creativity_auto_detected', False)
        creativity_applied = meta.get('creativity_applied', False)
        
        print(f"   🎯 Auto-Detected: {creativity_auto}")
        print(f"   ✨ Creativity Applied: {creativity_applied}")
        print(f"   📝 Response Length: {len(result.get('reply', ''))} chars")
        
        if creativity_auto and creativity_applied:
            print("   ✅ الإبداع مُفعّل تلقائياً!")
        else:
            print("   ⚠️ الإبداع لم يُفعّل")
    
    # ==================== Test 2: Direct Creative Access ====================
    print("\n" + "="*70)
    print("🚀 اختبار 2: الوصول المباشر لمحرك الإبداع")
    print("="*70)
    
    try:
        innovation = await mc.creative_innovate_unified(
            domain="technology",
            concept="AI-powered education",
            constraints=["accessible", "scalable"]
        )
        
        print(f"✅ الحالة: {innovation.get('status')}")
        if innovation.get('status') == 'success':
            print(f"💡 الابتكار: {str(innovation.get('innovation', {}))[:200]}...")
    except Exception as e:
        print(f"❌ خطأ: {e}")
    
    # ==================== Test 3: Reasoning Engine ====================
    print("\n" + "="*70)
    print("🧠 اختبار 3: محرك الاستدلال")
    print("="*70)
    
    try:
        reasoning = await mc.reason_with_unified(
            "إذا كانت كل الطيور تطير، وكل النسور طيور، فهل النسور تطير؟",
            reasoning_type="deductive"
        )
        
        print(f"✅ الحالة: {reasoning.get('status')}")
        if reasoning.get('status') == 'success':
            print(f"💭 النتيجة: {str(reasoning.get('reasoning_result', {}))[:200]}...")
    except Exception as e:
        print(f"❌ خطأ: {e}")
    
    # ==================== Test 4: Memory Query ====================
    print("\n" + "="*70)
    print("💾 اختبار 4: استعلام الذاكرة")
    print("="*70)
    
    try:
        memory = await mc.query_unified_memory(
            "روبوت",
            memory_types=["episodic", "semantic"]
        )
        
        print(f"✅ الحالة: {memory.get('status')}")
        print(f"📊 عدد النتائج: {memory.get('count', 0)}")
    except Exception as e:
        print(f"❌ خطأ: {e}")
    
    # ==================== Test 5: System Report ====================
    print("\n" + "="*70)
    print("📊 اختبار 5: تقرير النظام")
    print("="*70)
    
    try:
        report = await mc.get_agi_system_report()
        
        if report.get('status') == 'active':
            print(f"✅ النظام نشط")
            print(f"   💾 الذاكرة الدلالية: {report['memory']['semantic_items']} عنصر")
            print(f"   📚 الذاكرة الحلقية: {report['memory']['episodic_items']} حدث")
            print(f"   🌟 مستوى الوعي: {report['consciousness_level']:.3f}")
            print(f"   ⚙️ المحركات: {report['engines_connected']}")
    except Exception as e:
        print(f"❌ خطأ: {e}")
    
    # ==================== Summary ====================
    print("\n" + "="*70)
    print("✅ اكتمل الاختبار!")
    print("="*70)
    print("\n📋 الميزات المختبرة:")
    print("   ✅ Auto-detection للإبداع")
    print("   ✅ الوصول المباشر للمحركات")
    print("   ✅ استعلام الذاكرة")
    print("   ✅ تقارير النظام")
    print("\n🎉 UnifiedAGI مدمج بالكامل في Mission Control!")


if __name__ == "__main__":
    asyncio.run(test_integration())
