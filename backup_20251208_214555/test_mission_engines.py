"""
اختبار المحركات الحقيقية المدمجة في mission_control_enhanced
"""
import asyncio
import sys
import os

# Add repo to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dynamic_modules.mission_control_enhanced import (
    EnhancedMissionController,
    quick_start_enhanced
)


async def test_math_engine():
    """اختبار محرك الرياضيات"""
    print("\n" + "="*60)
    print("🧮 اختبار MathematicalBrain")
    print("="*60)
    
    result = await quick_start_enhanced("science", "solve: 3x + 7 = 22")
    
    print(f"\n📊 النتيجة:")
    if isinstance(result, dict):
        # Check for direct math engine response (bypasses cluster routing)
        if 'meta' in result and result['meta'].get('engine') == 'SymPy_Math_Engine':
            print(f"   - Direct Math Engine Response ✅")
            print(f"   - Engine: {result['meta']['engine']}")
            print(f"   - Confidence: {result['meta']['confidence']:.2f}")
            print(f"   - Real Processing: {result['meta']['real_processing']}")
            print(f"\n✅ الحل الرياضي:")
            print(f"   {result.get('reply_text', result.get('reply', 'No output'))}")
            return result
        
        # Otherwise check cluster routing
        ir = result.get('integration_result', {})
        cluster = ir.get('cluster_result', {}) if isinstance(ir, dict) else {}
        
        print(f"   - Cluster: {cluster.get('cluster_type')}")
        print(f"   - المحركات المستخدمة: {len(cluster.get('engines_used', []))}")
        print(f"   - الثقة: {cluster.get('confidence_score', 0):.2f}")
        
        # عرض مخرجات المحركات
        for res in cluster.get('results', [])[:3]:
            if res.get('engine') == 'MathematicalBrain':
                print(f"\n✅ MathematicalBrain:")
                print(f"   {res.get('output')}")
                print(f"   Source: {res.get('source')}")
                print(f"   Real Processing: {res.get('real_processing')}")
    
    return result


async def test_creative_engine():
    """اختبار محرك الإبداع"""
    print("\n" + "="*60)
    print("🎨 اختبار CreativeInnovationEngine")
    print("="*60)
    
    result = await quick_start_enhanced("creative", "اكتب قصة قصيرة عن ذكاء اصطناعي يتعلم المشاعر")
    
    print(f"\n📊 النتيجة:")
    if isinstance(result, dict):
        ir = result.get('integration_result', {})
        cluster = ir.get('cluster_result', {}) if isinstance(ir, dict) else {}
        
        print(f"   - Cluster: {cluster.get('cluster_type')}")
        print(f"   - المحركات المستخدمة: {len(cluster.get('engines_used', []))}")
        
        # عرض مخرجات المحركات الإبداعية
        for res in cluster.get('results', [])[:3]:
            if res.get('engine') == 'CreativeInnovationEngine':
                print(f"\n✅ CreativeInnovationEngine:")
                print(f"   {res.get('output')[:150]}...")
                print(f"   Real Processing: {res.get('real_processing')}")
    
    return result


async def test_simulation_engine():
    """اختبار محرك المحاكاة"""
    print("\n" + "="*60)
    print("🔬 اختبار AdvancedSimulationEngine")
    print("="*60)
    
    result = await quick_start_enhanced("science", "محاكاة نظام ثرموديناميك كمومي")
    
    print(f"\n📊 النتيجة:")
    if isinstance(result, dict):
        ir = result.get('integration_result', {})
        cluster = ir.get('cluster_result', {}) if isinstance(ir, dict) else {}
        
        print(f"   - Cluster: {cluster.get('cluster_type')}")
        
        # عرض مخرجات محرك المحاكاة
        for res in cluster.get('results', [])[:5]:
            if res.get('engine') == 'AdvancedSimulationEngine':
                print(f"\n✅ AdvancedSimulationEngine:")
                print(f"   {res.get('output')}")
                print(f"   Real Processing: {res.get('real_processing')}")
    
    return result


async def test_hypothesis_engine():
    """اختبار محرك توليد الفرضيات"""
    print("\n" + "="*60)
    print("💡 اختبار HypothesisGeneratorEngine")
    print("="*60)
    
    result = await quick_start_enhanced("strategic", "توليد فرضيات لتحسين كفاءة الطاقة الشمسية")
    
    print(f"\n📊 النتيجة:")
    if isinstance(result, dict):
        ir = result.get('integration_result', {})
        cluster = ir.get('cluster_result', {}) if isinstance(ir, dict) else {}
        
        print(f"   - Cluster: {cluster.get('cluster_type')}")
        
        # عرض مخرجات محرك الفرضيات
        for res in cluster.get('results', [])[:5]:
            if res.get('engine') == 'HypothesisGeneratorEngine':
                print(f"\n✅ HypothesisGeneratorEngine:")
                print(f"   {res.get('output')}")
                print(f"   Real Processing: {res.get('real_processing')}")
    
    return result


async def test_causal_graph_engine():
    """اختبار محرك الرسم السببي"""
    print("\n" + "="*60)
    print("🔗 اختبار CausalGraphEngine")
    print("="*60)
    
    result = await quick_start_enhanced("technical", "تحليل العلاقات السببية في نظام التبريد")
    
    print(f"\n📊 النتيجة:")
    if isinstance(result, dict):
        ir = result.get('integration_result', {})
        cluster = ir.get('cluster_result', {}) if isinstance(ir, dict) else {}
        
        print(f"   - Cluster: {cluster.get('cluster_type')}")
        
        # عرض مخرجات محرك الرسم السببي
        for res in cluster.get('results', [])[:5]:
            if res.get('engine') == 'CausalGraphEngine':
                print(f"\n✅ CausalGraphEngine:")
                print(f"   {res.get('output')}")
                print(f"   Real Processing: {res.get('real_processing')}")
    
    return result


async def run_all_tests():
    """تشغيل جميع الاختبارات"""
    print("\n" + "🚀 " + "="*58)
    print("🚀 بدء اختبار جميع المحركات المدمجة")
    print("🚀 " + "="*58)
    
    results = {}
    
    # اختبار كل محرك
    try:
        results['math'] = await test_math_engine()
    except Exception as e:
        print(f"\n❌ فشل اختبار MathematicalBrain: {e}")
        results['math'] = None
    
    try:
        results['creative'] = await test_creative_engine()
    except Exception as e:
        print(f"\n❌ فشل اختبار CreativeInnovationEngine: {e}")
        results['creative'] = None
    
    try:
        results['simulation'] = await test_simulation_engine()
    except Exception as e:
        print(f"\n❌ فشل اختبار AdvancedSimulationEngine: {e}")
        results['simulation'] = None
    
    try:
        results['hypothesis'] = await test_hypothesis_engine()
    except Exception as e:
        print(f"\n❌ فشل اختبار HypothesisGeneratorEngine: {e}")
        results['hypothesis'] = None
    
    try:
        results['causal'] = await test_causal_graph_engine()
    except Exception as e:
        print(f"\n❌ فشل اختبار CausalGraphEngine: {e}")
        results['causal'] = None
    
    # ملخص النتائج
    print("\n" + "="*60)
    print("📊 ملخص الاختبارات")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v is not None)
    total = len(results)
    
    print(f"\n✅ النجاح: {passed}/{total}")
    print(f"❌ الفشل: {total - passed}/{total}")
    print(f"📈 نسبة النجاح: {(passed/total)*100:.1f}%")
    
    for name, result in results.items():
        status = "✅" if result is not None else "❌"
        print(f"   {status} {name}")
    
    return results


if __name__ == "__main__":
    print("🔧 تشغيل اختبارات المحركات المدمجة...")
    asyncio.run(run_all_tests())
