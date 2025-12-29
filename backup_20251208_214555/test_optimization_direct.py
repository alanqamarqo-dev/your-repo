"""
اختبار مباشر لمحرك التحسين ضمن mission_control_enhanced
"""
import asyncio
import sys
sys.path.insert(0, 'D:\\AGL\\repo-copy')

from dynamic_modules.mission_control_enhanced import quick_start_enhanced

async def test_optimization():
    """اختبار مسألة التحسين"""
    print("\n" + "="*60)
    print("🧪 اختبار محرك التحسين في mission_control_enhanced")
    print("="*60)
    
    # مسألة التحسين
    problem = """
    لديك مزرعة مساحتها 1000 متر مربع وميزانية 5000 دولار.
    تريد زراعة 3 محاصيل مختلفة لتحقيق أقصى ربح.
    ما هو التوزيع الأمثل؟
    """
    
    print(f"\n📝 المسألة: {problem.strip()}")
    print("\n⏳ جاري المعالجة...")
    
    try:
        result = await quick_start_enhanced('science', problem)
        
        print("\n✅ النتيجة:")
        print("="*60)
        
        if isinstance(result, dict):
            # عرض المفاتيح الرئيسية
            print(f"\n🔑 المفاتيح المتاحة: {list(result.keys())}")
            
            # البحث عن النتيجة
            if 'focused_output' in result:
                focused = result['focused_output']
                if isinstance(focused, dict):
                    print(f"\n📊 focused_output:")
                    if 'formatted_output' in focused:
                        print(focused['formatted_output'][:500])
                else:
                    print(f"\n📊 focused_output: {str(focused)[:500]}")
            
            if 'llm_summary' in result:
                summary = result['llm_summary']
                if isinstance(summary, dict) and 'summary' in summary:
                    print(f"\n💡 الملخص:")
                    print(summary['summary'][:500])
            
            # البحث عن نتائج المحركات
            if 'cluster_results' in result:
                print(f"\n🔧 نتائج المحركات:")
                for engine_result in result.get('cluster_results', []):
                    if isinstance(engine_result, dict):
                        engine = engine_result.get('engine', 'unknown')
                        output = engine_result.get('output', '')
                        if 'OptimizationEngine' in engine or 'optimization' in str(output).lower():
                            print(f"\n✅ {engine}:")
                            print(str(output)[:300])
        else:
            print(f"\nنوع النتيجة: {type(result)}")
            print(str(result)[:500])
        
        print("\n" + "="*60)
        print("✅ الاختبار اكتمل")
        
    except Exception as e:
        print(f"\n❌ خطأ: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_optimization())
