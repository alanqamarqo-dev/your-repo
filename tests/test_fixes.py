import sys, os, asyncio
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'repo-copy'))

from dynamic_modules import mission_control_enhanced as mc

async def run_tests():
    print("🧪 اختبار الإصلاحات الجديدة...")

    # 1. اختبار الإبداع المباشر
    print("\n1️⃣ اختبار الإبداع المباشر:")
    res = await mc.creative_innovate_unified(domain="literature", concept="اكتب قصة قصيرة عن روبوت يكتشف المشاعر", creativity_level="high")
    print("✅ النتيجة:", res.get('status'))

    # 2. اختبار الاستدلال
    print("\n2️⃣ اختبار الاستدلال المباشر:")
    res = await mc.reason_with_unified("إذا كانت كل الطيور تطير، وكل النسور طيور، فهل النسور تطير؟", reasoning_type="deductive")
    print("✅ النتيجة:", res.get('status'))

    # 3. اختبار الذاكرة
    print("\n3️⃣ اختبار استعلام الذاكرة:")
    res = mc.query_unified_memory("روبوت")
    print("✅ النتيجة:", res.get('status'), "عدد النتائج:", res.get('count'))

    # 4. اختبار التقرير
    print("\n4️⃣ اختبار تقرير النظام:")
    res = mc.get_agi_system_report()
    print("✅ النتيجة:", res.get('status'))
    if res.get('status') == 'success':
        print(res.get('report'))

    # 5. اختبار إصلاح auto-detection
    print("\n5️⃣ اختبار إصلاح auto-detection:")
    res = await mc.fix_auto_creativity("ابتكر لعبة جديدة للأطفال")
    print("✅ النتيجة:", res.get('status') if isinstance(res, dict) else 'ok')

if __name__ == '__main__':
    asyncio.run(run_tests())
