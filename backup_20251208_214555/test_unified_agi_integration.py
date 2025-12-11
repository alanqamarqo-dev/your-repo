"""
اختبار دمج نظام AGI الموحد مع mission_control_enhanced
"""

import asyncio
import sys
import os

# إضافة المسار للـ repo
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 70)
print("🧬 اختبار دمج نظام AGI الموحد")
print("=" * 70)

async def test_unified_agi_integration():
    """اختبار شامل للدمج"""
    
    try:
        # 1. استيراد mission_control_enhanced
        print("\n📦 [1/5] استيراد mission_control_enhanced...")
        from dynamic_modules import mission_control_enhanced as mc
        print("   ✅ تم الاستيراد بنجاح")
        
        # 2. التحقق من UNIFIED_AGI
        print("\n🧬 [2/5] التحقق من UNIFIED_AGI instance...")
        if mc.UNIFIED_AGI:
            print(f"   ✅ UNIFIED_AGI موجود ونشط")
            print(f"   📊 Memory: {len(mc.UNIFIED_AGI.memory.semantic_memory)} semantic items")
            print(f"   🧠 Reasoning engine: {mc.UNIFIED_AGI.reasoning is not None}")
            print(f"   🔍 Curiosity engine: {mc.UNIFIED_AGI.curiosity is not None}")
            print(f"   🎯 Motivation engine: {mc.UNIFIED_AGI.motivation is not None}")
        else:
            print("   ⚠️ UNIFIED_AGI غير متاح")
        
        # 3. اختبار get_agi_system_report
        print("\n📊 [3/5] اختبار get_agi_system_report()...")
        report = await mc.get_agi_system_report()
        if report.get("status") == "active":
            print(f"   ✅ النظام نشط")
            print(f"   📊 Memory items: {report['memory']}")
            print(f"   🔗 Engines connected: {report['engines_connected']}")
        else:
            print(f"   ⚠️ {report}")
        
        # 4. اختبار معالجة بسيطة
        print("\n🧪 [4/5] اختبار process_with_unified_agi()...")
        test_input = "ما هو الذكاء الاصطناعي العام؟"
        result = await mc.process_with_unified_agi(test_input, {"test": True})
        
        if result.get("status") == "success":
            print(f"   ✅ المعالجة نجحت")
            print(f"   📝 النتيجة: {result.get('reply', '')[:100]}...")
            print(f"   🔍 Reasoning type: {result.get('meta', {}).get('reasoning_type')}")
        else:
            print(f"   ⚠️ فشل: {result.get('message', 'unknown error')}")
        
        # 5. اختبار quick_start_enhanced مع use_unified_agi
        print("\n🚀 [5/5] اختبار quick_start_enhanced مع use_unified_agi=True...")
        result2 = await mc.quick_start_enhanced(
            mission_type="general",
            topic="اشرح لي مفهوم التعلم العميق",
            use_unified_agi=True
        )
        
        if isinstance(result2, dict) and result2.get("status") == "success":
            print(f"   ✅ المعالجة الموحدة نجحت")
            print(f"   🧬 Engine used: {result2.get('meta', {}).get('engine')}")
        else:
            print(f"   📋 Result type: {type(result2)}")
        
        print("\n" + "=" * 70)
        print("✅ جميع الاختبارات اكتملت بنجاح!")
        print("=" * 70)
        
        return True
        
    except Exception as e:
        print(f"\n❌ خطأ في الاختبار: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_autonomous_exploration():
    """اختبار الاستكشاف الذاتي"""
    print("\n" + "=" * 70)
    print("🔍 اختبار الاستكشاف الذاتي")
    print("=" * 70)
    
    try:
        from dynamic_modules import mission_control_enhanced as mc
        
        if not mc.UNIFIED_AGI:
            print("⚠️ UNIFIED_AGI غير متاح - تخطي الاختبار")
            return False
        
        print("\n🔬 بدء استكشاف ذاتي لمدة 10 ثوان...")
        result = await mc.start_autonomous_exploration(
            duration_seconds=10,
            topic="الذكاء الاصطناعي العام"
        )
        
        if result.get("status") == "success":
            print(f"✅ الاستكشاف اكتمل بنجاح")
            print(f"📊 New discoveries: {len(result.get('new_discoveries', []))}")
            print(f"❓ Questions explored: {len(result.get('questions_explored', []))}")
            print(f"🔍 Knowledge gaps: {len(result.get('knowledge_gaps_found', []))}")
        else:
            print(f"⚠️ فشل: {result.get('message')}")
        
        return True
        
    except Exception as e:
        print(f"❌ خطأ: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n🚀 بدء الاختبارات...\n")
    
    # اختبار الدمج الأساسي
    success1 = asyncio.run(test_unified_agi_integration())
    
    # اختبار الاستكشاف الذاتي (اختياري)
    # success2 = asyncio.run(test_autonomous_exploration())
    
    print("\n✨ اختبارات مكتملة!\n")
