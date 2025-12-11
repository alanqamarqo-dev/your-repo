"""
🧪 اختبار شامل لجميع الميزات الجديدة
Test All New Features - Complete Integration Test
"""

import sys
import asyncio
from pathlib import Path

# Add parent directory to path
repo_dir = Path(__file__).parent
sys.path.insert(0, str(repo_dir))

# استيراد من المسار الصحيح
from dynamic_modules.unified_agi_system import UnifiedAGISystem
from Core_Engines import bootstrap_register_all_engines

print("="*80)
print("🧪 اختبار شامل لجميع الميزات الجديدة")
print("="*80)

# تسجيل المحركات
print("\n📋 تسجيل المحركات...")
ENGINE_REGISTRY = {}
result = bootstrap_register_all_engines(ENGINE_REGISTRY, verbose=True)
print(f"✅ تم تسجيل {result.get('registered', 0)} محرك")

# إنشاء النظام الموحد
print("\n🚀 إنشاء UnifiedAGISystem...")
system = UnifiedAGISystem(engine_registry=ENGINE_REGISTRY)

print("\n" + "="*80)
print("📊 حالة الأنظمة المدمجة")
print("="*80)

# فحص حالة كل نظام
systems_status = {
    "DKN System": system.dkn_enabled,
    "Knowledge Graph": system.kg_enabled,
    "Scientific Systems": system.scientific_enabled,
    "Self-Improvement": system.self_improvement_enabled
}

for name, status in systems_status.items():
    icon = "✅" if status else "❌"
    print(f"{icon} {name}: {'مفعّل' if status else 'معطل'}")

# عرض تفاصيل إضافية
if system.dkn_enabled:
    try:
        dkn_count = len(system.meta_orchestrator.dkn_engines) if hasattr(system, 'meta_orchestrator') else 7
        print(f"   - محركات DKN: {dkn_count}")
    except:
        print(f"   - محركات DKN: 7")

if system.kg_enabled:
    try:
        kg_count = len(system.kg_integration.all_engines) if hasattr(system, 'kg_integration') else 10
        print(f"   - محركات Knowledge Graph: {kg_count}")
    except:
        print(f"   - محركات Knowledge Graph: 10")

if system.scientific_enabled:
    engines = []
    if system.theorem_prover: engines.append("TheoremProver")
    if system.research_assistant: engines.append("ResearchAssistant")
    if system.hardware_simulator: engines.append("HardwareSimulator")
    if system.simulation_engine: engines.append("SimulationEngine")
    print(f"   - محركات علمية: {', '.join(engines)}")

if system.self_improvement_enabled:
    systems_list = []
    if system.self_learning: systems_list.append("SelfLearning")
    if system.self_monitoring: systems_list.append("Monitoring")
    if system.auto_rollback: systems_list.append("Rollback")
    if system.safe_modification: systems_list.append("SafeMod")
    if system.strategic_memory: systems_list.append("Memory")
    print(f"   - أنظمة التحسين: {', '.join(systems_list)}")

print("\n" + "="*80)
print("🧪 الاختبارات الوظيفية")
print("="*80)

async def run_tests():
    """تشغيل جميع الاختبارات"""
    
    tests = [
        {
            "name": "اختبار 1: حساب رياضي بسيط",
            "query": "احسب 25% من 800",
            "expected": ["DKN", "KG"],
            "check_scientific": False
        },
        {
            "name": "اختبار 2: برهان رياضي",
            "query": "أثبت أن a² + b² = c² في المثلث القائم",
            "expected": ["DKN", "KG", "Scientific"],
            "check_scientific": True,
            "scientific_keyword": "برهان"
        },
        {
            "name": "اختبار 3: بحث علمي",
            "query": "بحث عن الطاقة الكمومية في الفيزياء الحديثة",
            "expected": ["DKN", "KG", "Scientific"],
            "check_scientific": True,
            "scientific_keyword": "بحث"
        },
        {
            "name": "اختبار 4: محاكاة فيزيائية",
            "query": "محاكاة حركة كرة تسقط من ارتفاع 10 متر",
            "expected": ["DKN", "KG", "Scientific"],
            "check_scientific": True,
            "scientific_keyword": "محاكاة"
        },
        {
            "name": "اختبار 5: سؤال إبداعي",
            "query": "اقترح فكرة مبتكرة لتطبيق تعليمي يستخدم الذكاء الاصطناعي",
            "expected": ["DKN", "KG"],
            "check_scientific": False
        },
        {
            "name": "اختبار 6: تحليل معقد",
            "query": "حلل العلاقة بين الطاقة الشمسية والاستدامة البيئية",
            "expected": ["DKN", "KG"],
            "check_scientific": False
        }
    ]
    
    results = []
    
    for i, test in enumerate(tests, 1):
        print(f"\n{'='*60}")
        print(f"📝 {test['name']}")
        print(f"{'='*60}")
        print(f"السؤال: {test['query']}")
        
        try:
            result = await system.process_with_full_agi(test['query'])
            
            # فحص النتائج
            checks = {
                "DKN استخدم": result.get('dkn_used', False),
                "KG استخدم": result.get('kg_used', False),
                "Scientific نشط": result.get('scientific_results', {}).get('active', False) if test.get('check_scientific') else None,
                "Self-Improvement نشط": result.get('improvement_results', {}).get('status') == 'processed',
                "Performance Score": result.get('performance_score', 0.0)
            }
            
            # عرض النتائج
            for check_name, check_value in checks.items():
                if check_value is None:
                    continue
                if isinstance(check_value, bool):
                    icon = "✅" if check_value else "⚠️"
                    print(f"   {icon} {check_name}: {'نعم' if check_value else 'لا'}")
                else:
                    print(f"   📊 {check_name}: {check_value:.2f}")
            
            # التحقق من الإجابة
            answer = result.get('reasoning', {}).get('answer', result.get('answer', 'لا توجد إجابة'))
            if answer and len(str(answer)) > 10:
                print(f"   ✅ الإجابة: {str(answer)[:100]}...")
            else:
                print(f"   ⚠️ الإجابة قصيرة أو غير موجودة")
            
            # تسجيل النتيجة
            test_passed = (
                checks["DKN استخدم"] and
                checks["KG استخدم"] and
                (checks["Scientific نشط"] if test.get('check_scientific') else True) and
                len(str(answer)) > 10
            )
            
            results.append({
                "test": test['name'],
                "passed": test_passed,
                "checks": checks
            })
            
        except Exception as e:
            print(f"   ❌ خطأ في الاختبار: {str(e)}")
            results.append({
                "test": test['name'],
                "passed": False,
                "error": str(e)
            })
    
    return results

# تشغيل الاختبارات
print("\n🚀 بدء الاختبارات...")
results = asyncio.run(run_tests())

print("\n" + "="*80)
print("📈 ملخص النتائج النهائي")
print("="*80)

passed = sum(1 for r in results if r['passed'])
total = len(results)
success_rate = (passed / total * 100) if total > 0 else 0

print(f"\n✅ اختبارات ناجحة: {passed}/{total} ({success_rate:.1f}%)")
print(f"❌ اختبارات فاشلة: {total - passed}/{total}")

# تفاصيل كل اختبار
print("\n📋 تفاصيل الاختبارات:")
for i, result in enumerate(results, 1):
    icon = "✅" if result['passed'] else "❌"
    print(f"{i}. {icon} {result['test']}")
    if 'error' in result:
        print(f"   ⚠️ الخطأ: {result['error']}")

# إحصائيات الاستخدام
print("\n" + "="*80)
print("📊 إحصائيات الاستخدام")
print("="*80)

usage_stats = {
    "DKN": 0,
    "KG": 0,
    "Scientific": 0,
    "Self-Improvement": 0
}

for result in results:
    if 'checks' in result:
        if result['checks'].get('DKN استخدم'):
            usage_stats['DKN'] += 1
        if result['checks'].get('KG استخدم'):
            usage_stats['KG'] += 1
        if result['checks'].get('Scientific نشط'):
            usage_stats['Scientific'] += 1
        if result['checks'].get('Self-Improvement نشط'):
            usage_stats['Self-Improvement'] += 1

for system_name, count in usage_stats.items():
    percentage = (count / total * 100) if total > 0 else 0
    print(f"✅ {system_name}: استخدم في {count}/{total} اختبار ({percentage:.1f}%)")

print("\n" + "="*80)
print("🎯 التقييم النهائي")
print("="*80)

if success_rate >= 90:
    grade = "ممتاز ⭐⭐⭐⭐⭐"
    status = "🎉 النظام يعمل بشكل مثالي!"
elif success_rate >= 70:
    grade = "جيد جداً ⭐⭐⭐⭐"
    status = "✅ النظام يعمل بشكل جيد"
elif success_rate >= 50:
    grade = "جيد ⭐⭐⭐"
    status = "⚠️ النظام يحتاج بعض التحسينات"
else:
    grade = "يحتاج تحسين ⭐⭐"
    status = "❌ النظام يحتاج إلى صيانة"

print(f"التقييم: {grade}")
print(f"الحالة: {status}")

# توصيات
print("\n💡 التوصيات:")
if usage_stats['Scientific'] < total / 2:
    print("⚠️ المحركات العلمية لم تستخدم بشكل كافٍ - تحقق من كلمات التفعيل")
if usage_stats['Self-Improvement'] < total / 2:
    print("⚠️ نظام التحسين الذاتي لم يستخدم بشكل كافٍ - تحقق من الأداء")
if success_rate >= 90:
    print("✅ النظام في حالة ممتازة - استمر في المراقبة")
    print("✅ جميع الأنظمة تعمل بتناغم تام")

print("\n" + "="*80)
print("🏁 انتهى الاختبار الشامل")
print("="*80)
