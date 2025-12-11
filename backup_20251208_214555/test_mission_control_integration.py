"""
🧪 اختبار تكامل Mission Control Enhanced مع النظام الموحد
================================================================

يتحقق من:
1. تحميل mission_control_enhanced.py بدون أخطاء
2. التكامل مع unified_agi_system.py
3. عدم حدوث تعارضات في الاستيراد
4. توافق ENGINE_REGISTRY
"""

import sys
import os

# إضافة المسار
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_import_mission_control():
    """اختبار 1: استيراد mission_control_enhanced"""
    print("\n" + "="*70)
    print("🧪 Test 1: Import mission_control_enhanced.py")
    print("="*70)
    
    try:
        # محاولة استيراد mission_control
        import dynamic_modules.mission_control_enhanced as mission_control
        
        print("✅ mission_control_enhanced تم استيراده بنجاح")
        
        # التحقق من وجود المكونات الأساسية
        has_registry = hasattr(mission_control, '_LOCAL_ENGINE_REGISTRY')
        has_focus = hasattr(mission_control, 'SmartFocusController')
        has_llm = hasattr(mission_control, 'LLMIntegrationEngine')
        
        print(f"📊 _LOCAL_ENGINE_REGISTRY: {'✅' if has_registry else '❌'}")
        print(f"📊 SmartFocusController: {'✅' if has_focus else '❌'}")
        print(f"📊 LLMIntegrationEngine: {'✅' if has_llm else '❌'}")
        
        if has_registry:
            registry_size = len(mission_control._LOCAL_ENGINE_REGISTRY)
            print(f"📊 Registry Size: {registry_size} محركات")
        
        return True
        
    except Exception as e:
        print(f"❌ فشل الاستيراد: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_unified_agi_compatibility():
    """اختبار 2: التوافق مع unified_agi_system"""
    print("\n" + "="*70)
    print("🧪 Test 2: Compatibility with unified_agi_system")
    print("="*70)
    
    try:
        # استيراد كلا النظامين
        import dynamic_modules.mission_control_enhanced as mission_control
        from dynamic_modules.unified_agi_system import UnifiedAGISystem
        
        print("✅ تم استيراد النظامين معاً بنجاح")
        
        # التحقق من UNIFIED_AGI في mission_control
        has_unified = hasattr(mission_control, 'UNIFIED_AGI')
        print(f"📊 UNIFIED_AGI متاح في mission_control: {'✅' if has_unified else '❌'}")
        
        if has_unified and mission_control.UNIFIED_AGI:
            unified = mission_control.UNIFIED_AGI
            print(f"📊 UNIFIED_AGI Type: {type(unified).__name__}")
            
            # التحقق من الأنظمة المفعلة
            systems = {
                "DKN": getattr(unified, 'dkn_enabled', False),
                "Smart Router": getattr(unified, 'smart_routing_enabled', False),
                "Autonomous": getattr(unified, 'autonomous_enabled', False),
            }
            
            print("\n📊 حالة الأنظمة:")
            for name, enabled in systems.items():
                print(f"   {'✅' if enabled else '❌'} {name}: {enabled}")
        
        return True
        
    except Exception as e:
        print(f"❌ فشل التوافق: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_smart_focus_controller():
    """اختبار 3: SmartFocusController"""
    print("\n" + "="*70)
    print("🧪 Test 3: SmartFocusController Functionality")
    print("="*70)
    
    try:
        import asyncio
        from dynamic_modules.mission_control_enhanced import SmartFocusController
        
        controller = SmartFocusController()
        print("✅ SmartFocusController تم إنشاؤه بنجاح")
        
        # اختبار rapid_diagnosis
        async def test_diagnosis():
            result = await controller.rapid_diagnosis(timeout=5.0)
            return result
        
        diagnosis = asyncio.run(test_diagnosis())
        print(f"📊 Active Engines: {len(diagnosis.get('active_engines', []))}")
        print(f"📊 Diagnosis Time: {diagnosis.get('diagnosis_time', 0):.3f}s")
        
        # اختبار activate_mission_mode
        async def test_mission():
            result = await controller.activate_mission_mode("test_mission", timeout=10.0)
            return result
        
        mission_result = asyncio.run(test_mission())
        print(f"📊 Mission: {mission_result.get('mission', 'N/A')}")
        print(f"📊 Activation Time: {mission_result.get('activation_time', 0):.3f}s")
        
        return True
        
    except Exception as e:
        print(f"❌ فشل SmartFocusController: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_engine_registry_sharing():
    """اختبار 4: مشاركة ENGINE_REGISTRY"""
    print("\n" + "="*70)
    print("🧪 Test 4: ENGINE_REGISTRY Sharing")
    print("="*70)
    
    try:
        import dynamic_modules.mission_control_enhanced as mission_control
        from dynamic_modules.unified_agi_system import UnifiedAGISystem
        
        # الحصول على registry من mission_control
        mc_registry = mission_control._LOCAL_ENGINE_REGISTRY
        print(f"📊 mission_control registry: {len(mc_registry)} محركات")
        
        # إنشاء unified_agi بنفس الـ registry
        unified = UnifiedAGISystem(mc_registry)
        print("✅ UnifiedAGISystem تم إنشاؤه بـ registry مشترك")
        
        # التحقق من المحركات المشتركة
        shared_engines = [
            "Mathematical_Brain",
            "Creative_Innovation",
            "Meta_Learning",
            "Causal_Graph"
        ]
        
        print("\n📊 المحركات المشتركة:")
        for engine_name in shared_engines:
            in_mc = engine_name in mc_registry
            print(f"   {'✅' if in_mc else '❌'} {engine_name}: {in_mc}")
        
        return True
        
    except Exception as e:
        print(f"❌ فشل مشاركة Registry: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_no_conflicts():
    """اختبار 5: عدم وجود تعارضات"""
    print("\n" + "="*70)
    print("🧪 Test 5: No Import Conflicts")
    print("="*70)
    
    try:
        # استيراد جميع المكونات معاً
        import dynamic_modules.mission_control_enhanced as mc
        from dynamic_modules.unified_agi_system import (
            UnifiedAGISystem,
            DKN_AVAILABLE,
            KNOWLEDGE_GRAPH_AVAILABLE,
            SCIENTIFIC_SYSTEMS_AVAILABLE,
            SELF_IMPROVEMENT_AVAILABLE,
            SMART_ROUTER_AVAILABLE,
            AUTONOMOUS_AVAILABLE
        )
        
        print("✅ جميع الاستيرادات نجحت بدون تعارضات")
        
        # التحقق من توافق الأعلام
        print("\n📊 حالة الأنظمة في unified_agi_system:")
        print(f"   {'✅' if DKN_AVAILABLE else '❌'} DKN_AVAILABLE: {DKN_AVAILABLE}")
        print(f"   {'✅' if KNOWLEDGE_GRAPH_AVAILABLE else '❌'} KNOWLEDGE_GRAPH: {KNOWLEDGE_GRAPH_AVAILABLE}")
        print(f"   {'✅' if SCIENTIFIC_SYSTEMS_AVAILABLE else '❌'} SCIENTIFIC: {SCIENTIFIC_SYSTEMS_AVAILABLE}")
        print(f"   {'✅' if SELF_IMPROVEMENT_AVAILABLE else '❌'} SELF_IMPROVEMENT: {SELF_IMPROVEMENT_AVAILABLE}")
        print(f"   {'✅' if SMART_ROUTER_AVAILABLE else '❌'} SMART_ROUTER: {SMART_ROUTER_AVAILABLE}")
        print(f"   {'✅' if AUTONOMOUS_AVAILABLE else '❌'} AUTONOMOUS: {AUTONOMOUS_AVAILABLE}")
        
        # التحقق من المحركات في mission_control
        mc_engines = {
            "UNIFIED_AGI": mc.UNIFIED_AGI is not None,
            "MATH_BRAIN": mc.MATH_BRAIN is not None,
            "CREATIVE_ENGINE": mc.CREATIVE_ENGINE is not None,
        }
        
        print("\n📊 المحركات في mission_control:")
        for name, available in mc_engines.items():
            print(f"   {'✅' if available else '❌'} {name}: {available}")
        
        return True
        
    except Exception as e:
        print(f"❌ تعارضات موجودة: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """تشغيل جميع الاختبارات"""
    print("\n" + "🌟"*35)
    print("🚀 بدء اختبارات تكامل Mission Control Enhanced")
    print("🌟"*35)
    
    tests = [
        ("Import Mission Control", test_import_mission_control),
        ("Unified AGI Compatibility", test_unified_agi_compatibility),
        ("SmartFocusController", test_smart_focus_controller),
        ("Engine Registry Sharing", test_engine_registry_sharing),
        ("No Conflicts", test_no_conflicts),
    ]
    
    results = {}
    for name, test_func in tests:
        try:
            results[name] = test_func()
        except Exception as e:
            print(f"\n❌ خطأ حرج في {name}: {e}")
            results[name] = False
    
    # النتائج النهائية
    print("\n" + "="*70)
    print("📊 النتائج النهائية")
    print("="*70)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, success in results.items():
        symbol = "✅" if success else "❌"
        print(f"{symbol} {name}: {'نجح' if success else 'فشل'}")
    
    print(f"\n{'='*70}")
    print(f"🎯 النتيجة: {passed}/{total} اختبارات ناجحة ({passed/total*100:.1f}%)")
    print(f"{'='*70}")
    
    if passed == total:
        print("\n🎉 جميع الاختبارات نجحت! التكامل مكتمل بدون تكسير!")
    elif passed >= total * 0.75:
        print("\n✅ معظم الاختبارات نجحت! التكامل يعمل بشكل جيد.")
    else:
        print("\n⚠️ بعض الاختبارات فشلت. راجع الأخطاء أعلاه.")
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
