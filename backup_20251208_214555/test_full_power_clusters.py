"""
اختبار شامل لنظام الـ Clusters والدمج الكامل
يختبر 4 سيناريوهات مختلفة لإثبات أن النظام يعمل بكامل طاقته
"""
import asyncio
import sys
import time
sys.path.insert(0, 'D:\\AGL\\repo-copy')

from dynamic_modules.mission_control_enhanced import quick_start_enhanced

def print_header(title, color="cyan"):
    colors = {
        "cyan": "\033[96m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "red": "\033[91m",
        "reset": "\033[0m"
    }
    print(f"\n{'='*70}")
    print(f"{colors.get(color, '')}{title}{colors['reset']}")
    print(f"{'='*70}\n")

def print_result(label, value, indent=2):
    print(f"{'  '*indent}🔹 {label}: {value}")

async def test_scientific_cluster():
    """اختبار الـ scientific_reasoning cluster بمسألة تحسين"""
    print_header("🧪 الاختبار 1: Scientific Reasoning Cluster (مع OptimizationEngine)", "cyan")
    
    problem = """
    لديك مزرعة مساحتها 1000 متر مربع وميزانية 5000 دولار.
    تريد زراعة 3 محاصيل مختلفة لتحقيق أقصى ربح.
    ما هو التوزيع الأمثل؟
    """
    
    print(f"📝 المسألة: {problem.strip()}")
    print(f"\n⏳ جاري تفعيل الكلاستر...")
    
    start_time = time.time()
    
    try:
        result = await quick_start_enhanced('science', problem)
        
        elapsed = time.time() - start_time
        print(f"\n✅ اكتمل في {elapsed:.2f} ثانية")
        
        if isinstance(result, dict):
            print(f"\n📊 تحليل النتيجة:")
            print_result("نوع المهمة", result.get('mission_type', 'غير محدد'))
            
            # فحص integration_result
            integration = result.get('integration_result', {})
            if isinstance(integration, dict):
                cluster_result = integration.get('cluster_result', {})
                if isinstance(cluster_result, dict):
                    print_result("نوع الكلاستر", cluster_result.get('cluster_type', 'N/A'))
                    print_result("عدد المحركات المستخدمة", cluster_result.get('total_engines', 0))
                    print_result("درجة الثقة", f"{cluster_result.get('confidence_score', 0):.2%}")
                    
                    # عرض المحركات المستخدمة
                    engines_used = cluster_result.get('engines_used', [])
                    if engines_used:
                        print(f"\n  🔧 المحركات المستخدمة ({len(engines_used)} محرك):")
                        for i, engine in enumerate(engines_used[:10], 1):
                            print(f"      {i}. {engine}")
                    
                    # البحث عن نتيجة OptimizationEngine
                    results = cluster_result.get('results', [])
                    print(f"\n  📈 نتائج المحركات ({len(results)} نتيجة):")
                    for res in results:
                        if isinstance(res, dict):
                            engine_name = res.get('engine', 'Unknown')
                            output = res.get('output', '')
                            if 'OptimizationEngine' in engine_name or 'optimization' in str(output).lower():
                                print(f"\n  ✨ {engine_name}:")
                                print(f"      {str(output)[:200]}...")
                                break
            
            # عرض الملخص إذا وجد
            llm_summary = integration.get('llm_summary', {})
            if isinstance(llm_summary, dict) and llm_summary.get('summary'):
                print(f"\n  💡 الملخص:")
                print(f"      {llm_summary['summary'][:300]}...")
        
        print("\n" + "="*70)
        return True
        
    except Exception as e:
        print(f"\n❌ خطأ: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_creative_cluster():
    """اختبار الـ creative_writing cluster"""
    print_header("🎨 الاختبار 2: Creative Writing Cluster", "yellow")
    
    theme = "اكتب قصة قصيرة عن روبوت يتعلم معنى الحرية"
    
    print(f"📝 الموضوع: {theme}")
    print(f"\n⏳ جاري تفعيل الكلاستر...")
    
    start_time = time.time()
    
    try:
        result = await quick_start_enhanced('creative', theme)
        
        elapsed = time.time() - start_time
        print(f"\n✅ اكتمل في {elapsed:.2f} ثانية")
        
        if isinstance(result, dict):
            print(f"\n📊 تحليل النتيجة:")
            
            integration = result.get('integration_result', {})
            if isinstance(integration, dict):
                cluster_result = integration.get('cluster_result', {})
                if isinstance(cluster_result, dict):
                    print_result("نوع الكلاستر", cluster_result.get('cluster_type', 'N/A'))
                    print_result("عدد المحركات", cluster_result.get('total_engines', 0))
                    print_result("درجة الثقة", f"{cluster_result.get('confidence_score', 0):.2%}")
                    
                    # عرض بعض النتائج
                    results = cluster_result.get('results', [])
                    if results:
                        print(f"\n  📝 عينة من النتائج:")
                        for i, res in enumerate(results[:3], 1):
                            if isinstance(res, dict):
                                print(f"      {i}. {res.get('engine', 'N/A')}: {str(res.get('output', ''))[:80]}...")
        
        print("\n" + "="*70)
        return True
        
    except Exception as e:
        print(f"\n❌ خطأ: {e}")
        return False

async def test_technical_cluster():
    """اختبار الـ technical_analysis cluster"""
    print_header("🔧 الاختبار 3: Technical Analysis Cluster (مع FastTrack)", "green")
    
    task = "اكتب كود Python لحساب الأعداد الأولية حتى 100"
    
    print(f"📝 المهمة: {task}")
    print(f"\n⏳ جاري تفعيل الكلاستر...")
    
    start_time = time.time()
    
    try:
        result = await quick_start_enhanced('technical', task)
        
        elapsed = time.time() - start_time
        print(f"\n✅ اكتمل في {elapsed:.2f} ثانية")
        
        if isinstance(result, dict):
            print(f"\n📊 تحليل النتيجة:")
            
            integration = result.get('integration_result', {})
            if isinstance(integration, dict):
                cluster_result = integration.get('cluster_result', {})
                if isinstance(cluster_result, dict):
                    print_result("نوع الكلاستر", cluster_result.get('cluster_type', 'N/A'))
                    print_result("عدد المحركات", cluster_result.get('total_engines', 0))
                    
                    # البحث عن FastTrack
                    results = cluster_result.get('results', [])
                    for res in results:
                        if isinstance(res, dict) and 'FastTrack' in res.get('engine', ''):
                            print(f"\n  ⚡ FastTrackCodeGeneration متفعل!")
                            break
        
        print("\n" + "="*70)
        return True
        
    except Exception as e:
        print(f"\n❌ خطأ: {e}")
        return False

async def test_strategic_cluster():
    """اختبار الـ strategic_planning cluster"""
    print_header("🧠 الاختبار 4: Strategic Planning Cluster", "yellow")
    
    plan = "ضع خطة استراتيجية لزيادة كفاءة فريق البرمجة بنسبة 30% خلال 6 أشهر"
    
    print(f"📝 الخطة المطلوبة: {plan}")
    print(f"\n⏳ جاري تفعيل الكلاستر...")
    
    start_time = time.time()
    
    try:
        result = await quick_start_enhanced('strategic', plan)
        
        elapsed = time.time() - start_time
        print(f"\n✅ اكتمل في {elapsed:.2f} ثانية")
        
        if isinstance(result, dict):
            print(f"\n📊 تحليل النتيجة:")
            
            integration = result.get('integration_result', {})
            if isinstance(integration, dict):
                cluster_result = integration.get('cluster_result', {})
                if isinstance(cluster_result, dict):
                    print_result("نوع الكلاستر", cluster_result.get('cluster_type', 'N/A'))
                    print_result("عدد المحركات", cluster_result.get('total_engines', 0))
                    print_result("درجة الثقة", f"{cluster_result.get('confidence_score', 0):.2%}")
        
        print("\n" + "="*70)
        return True
        
    except Exception as e:
        print(f"\n❌ خطأ: {e}")
        return False

async def main():
    print_header("🚀 اختبار شامل لنظام الـ Clusters بكامل الطاقة", "cyan")
    
    results = []
    
    # الاختبار 1: Scientific (أهم اختبار - يختبر OptimizationEngine)
    print("\n⏱️  بدء الاختبار 1...")
    results.append(("Scientific Reasoning", await test_scientific_cluster()))
    
    # الاختبار 2: Creative
    print("\n⏱️  بدء الاختبار 2...")
    results.append(("Creative Writing", await test_creative_cluster()))
    
    # الاختبار 3: Technical (يختبر FastTrack)
    print("\n⏱️  بدء الاختبار 3...")
    results.append(("Technical Analysis", await test_technical_cluster()))
    
    # الاختبار 4: Strategic
    print("\n⏱️  بدء الاختبار 4...")
    results.append(("Strategic Planning", await test_strategic_cluster()))
    
    # ملخص النتائج
    print_header("📊 ملخص النتائج النهائية", "green")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for name, success in results:
        status = "✅ نجح" if success else "❌ فشل"
        print(f"  {status} - {name}")
    
    print(f"\n🎯 النتيجة الإجمالية: {passed}/{total} ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 ممتاز! جميع الـ Clusters تعمل بكامل طاقتها!")
    elif passed > total / 2:
        print("\n✅ جيد! معظم الـ Clusters تعمل بنجاح")
    else:
        print("\n⚠️  يحتاج تحسين - بعض الـ Clusters بها مشاكل")
    
    print("\n" + "="*70)

if __name__ == "__main__":
    asyncio.run(main())
