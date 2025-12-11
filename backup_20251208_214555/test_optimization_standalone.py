"""
اختبار مباشر لاستدعاء OptimizationEngine من خلال simulate_engine
"""
import asyncio
import sys
sys.path.insert(0, 'D:\\AGL\\repo-copy')

async def test_direct_engine():
    """اختبار استدعاء مباشر لمحرك التحسين"""
    print("\n" + "="*60)
    print("🧪 اختبار مباشر لـ OptimizationEngine")
    print("="*60)
    
    # استيراد المحرك
    from Core_Engines.optimization_engine import OptimizationEngine
    
    engine = OptimizationEngine()
    
    problem = """
    لديك مزرعة مساحتها 1000 متر مربع وميزانية 5000 دولار.
    تريد زراعة 3 محاصيل مختلفة (قمح، ذرة، أرز).
    القمح يحتاج 2 متر مربع وتكلفته 30 دولار وربحه 15 دولار.
    الذرة تحتاج 1.5 متر وتكلفتها 25 دولار وربحها 12 دولار.
    الأرز يحتاج 1 متر وتكلفته 20 دولار وربحه 10 دولار.
    ما هو التوزيع الأمثل لتحقيق أقصى ربح؟
    """
    
    print(f"\n📝 المسألة:")
    print(problem.strip())
    print("\n⏳ جاري الحل...")
    
    try:
        result = engine.process_task(problem)
        
        print("\n✅ النتيجة:")
        print("="*60)
        
        if result.get('status') == 'success':
            print(f"\n🎯 الحالة: نجح")
            print(f"🔧 المحرك: {result.get('engine')}")
            
            solution = result.get('solution', {})
            print(f"\n💰 القيمة المثلى: ${solution.get('objective_value', 0)}")
            
            print(f"\n📊 التخصيص الأمثل:")
            for var, value in solution.get('variables', {}).items():
                if value > 0:
                    print(f"   • {var}: {value} وحدة")
            
            print(f"\n📋 استخدام الموارد:")
            for resource, usage in solution.get('constraints_usage', {}).items():
                print(f"   • {resource}: {usage['used']}/{usage['limit']} ({usage['percentage']}%)")
            
            if 'explanation' in result:
                print(f"\n💡 الشرح:")
                print(result['explanation'])
            
            print("\n" + "="*60)
            print("🎉 محرك التحسين يعمل بنجاح!")
            
        else:
            print(f"\n⚠️  الحالة: {result.get('status')}")
            print(f"رسالة: {result.get('message')}")
        
    except Exception as e:
        print(f"\n❌ خطأ: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_direct_engine())
