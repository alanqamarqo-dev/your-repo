"""
اختبار التكامل بين mission_control_enhanced والمسار السريع لتوليد الأكواد
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dynamic_modules.mission_control_enhanced import quick_start_enhanced, FAST_TRACK_EXPANSION


async def test_code_generation_detection():
    """اختبار اكتشاف طلبات الكود"""
    print("\n" + "="*60)
    print("🔍 اختبار اكتشاف طلبات الكود")
    print("="*60)
    
    test_cases = [
        ("write code to calculate fibonacci", True),
        ("اكتب كود بايثون لحساب المساحة", True),
        ("function to sort array", True),
        ("ما هي عاصمة فرنسا؟", False),
        ("python script for data analysis", True),
        ("how are you?", False)
    ]
    
    passed = 0
    for text, expected in test_cases:
        result = FAST_TRACK_EXPANSION.is_fast_task(text)
        status = "✅" if result == expected else "❌"
        print(f"{status} '{text[:40]}...' → {result} (expected: {expected})")
        if result == expected:
            passed += 1
    
    print(f"\n📊 النتيجة: {passed}/{len(test_cases)} اختبارات نجحت")
    return passed == len(test_cases)


async def test_fast_code_mission():
    """اختبار المسار السريع الكامل"""
    print("\n" + "="*60)
    print("⚡ اختبار المسار السريع لتوليد الكود")
    print("="*60)
    
    code_request = "write a Python function to calculate the factorial of a number"
    
    print(f"\n📝 الطلب: {code_request}")
    print("🚀 تشغيل المسار السريع...")
    
    result = await quick_start_enhanced("code", code_request)
    
    print(f"\n📊 النتيجة:")
    print(f"   - Mission Type: {result.get('mission_type')}")
    print(f"   - Status: {result.get('status')}")
    
    fast_track_result = result.get('fast_track_result')
    if fast_track_result:
        print(f"\n✅ Fast Track Result Found:")
        print(f"   - Engine: {fast_track_result.get('engine')}")
        print(f"   - Confidence: {fast_track_result.get('confidence')}")
        print(f"   - Fast Track: {fast_track_result.get('fast_track')}")
        print(f"   - Output Preview: {fast_track_result.get('output')[:100]}...")
    
    integration = result.get('integration_result', {})
    cluster = integration.get('cluster_result', {})
    print(f"\n🔧 Integration Details:")
    print(f"   - Cluster: {cluster.get('cluster_type')}")
    print(f"   - Engines Used: {len(cluster.get('engines_used', []))}")
    print(f"   - Confidence: {cluster.get('confidence_score', 0):.2f}")
    
    return fast_track_result is not None


async def test_auto_detection():
    """اختبار الاكتشاف التلقائي للأكواد"""
    print("\n" + "="*60)
    print("🤖 اختبار الاكتشاف التلقائي")
    print("="*60)
    
    # طلب كود بدون تحديد "code" صراحةً
    code_request = "اكتب دالة بايثون لحساب مجموع الأرقام"
    
    print(f"\n📝 الطلب: {code_request}")
    print("🔍 الاكتشاف التلقائي يجب أن يفعّل المسار السريع...")
    
    # استخدام mission_type عادي لكن النظام يجب أن يكتشف أنه كود
    result = await quick_start_enhanced("technical", code_request)
    
    print(f"\n📊 النتيجة:")
    print(f"   - Mission Type: {result.get('mission_type')}")
    
    # فحص إذا تم تفعيل المسار السريع
    fast_track_result = result.get('fast_track_result')
    if fast_track_result:
        print(f"✅ تم تفعيل المسار السريع تلقائياً!")
        print(f"   - Fast Track Flag: {fast_track_result.get('fast_track')}")
        return True
    else:
        print(f"⚠️ لم يتم تفعيل المسار السريع")
        # فحص في النتائج العادية
        cluster = result.get('integration_result', {}).get('cluster_result', {})
        for res in cluster.get('results', []):
            if res.get('engine') == 'FastTrackCodeGeneration':
                print(f"   - وُجد FastTrackCodeGeneration في النتائج")
                print(f"   - Output: {res.get('output')[:80]}...")
                return True
        return False


async def run_all_tests():
    """تشغيل جميع الاختبارات"""
    print("\n" + "🚀 " + "="*58)
    print("🚀 بدء اختبار تكامل المسار السريع مع Mission Control")
    print("🚀 " + "="*58)
    
    results = {}
    
    try:
        results['detection'] = await test_code_generation_detection()
    except Exception as e:
        print(f"\n❌ فشل اختبار الاكتشاف: {e}")
        results['detection'] = False
    
    try:
        results['fast_mission'] = await test_fast_code_mission()
    except Exception as e:
        print(f"\n❌ فشل اختبار المسار السريع: {e}")
        results['fast_mission'] = False
    
    try:
        results['auto_detection'] = await test_auto_detection()
    except Exception as e:
        print(f"\n❌ فشل اختبار الاكتشاف التلقائي: {e}")
        results['auto_detection'] = False
    
    print("\n" + "="*60)
    print("📊 ملخص النتائج")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    print(f"\n✅ النجاح: {passed}/{total}")
    print(f"❌ الفشل: {total - passed}/{total}")
    print(f"📈 نسبة النجاح: {(passed/total)*100:.1f}%\n")
    
    for name, result in results.items():
        status = "✅" if result else "❌"
        print(f"   {status} {name}")
    
    return results


if __name__ == "__main__":
    print("🔧 تشغيل اختبارات تكامل Fast Track...")
    asyncio.run(run_all_tests())
