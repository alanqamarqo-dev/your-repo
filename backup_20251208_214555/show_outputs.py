"""
اختبار سريع لعرض المخرجات الكاملة للإجابات
"""
import asyncio
import sys
import json
sys.path.insert(0, 'D:\\AGL\\repo-copy')

from dynamic_modules.mission_control_enhanced import quick_start_enhanced

def print_section(title):
    print("\n" + "="*70)
    print(f"📋 {title}")
    print("="*70 + "\n")

async def show_scientific_output():
    """عرض مخرجات Scientific Reasoning بالتفصيل"""
    print_section("مخرجات الاختبار العلمي (Scientific Reasoning)")
    
    problem = "لديك مزرعة مساحتها 1000 متر مربع وميزانية 5000 دولار. تريد زراعة 3 محاصيل مختلفة لتحقيق أقصى ربح."
    
    print(f"📝 السؤال: {problem}\n")
    print("⏳ جاري المعالجة...")
    
    result = await quick_start_enhanced('science', problem)
    
    print("\n✅ النتيجة الكاملة:")
    print("-" * 70)
    
    if isinstance(result, dict):
        # عرض كل شيء بشكل منظم
        integration = result.get('integration_result', {})
        
        # 1. نتائج الكلاستر
        if isinstance(integration, dict):
            cluster_result = integration.get('cluster_result', {})
            
            if isinstance(cluster_result, dict):
                print("\n🎯 معلومات الكلاستر:")
                print(f"   • النوع: {cluster_result.get('cluster_type', 'N/A')}")
                print(f"   • عدد المحركات: {cluster_result.get('total_engines', 0)}")
                print(f"   • درجة الثقة: {cluster_result.get('confidence_score', 0):.2%}")
                
                # 2. نتائج كل محرك
                results = cluster_result.get('results', [])
                print(f"\n🔧 نتائج المحركات ({len(results)} محرك):")
                print("-" * 70)
                
                for i, res in enumerate(results, 1):
                    if isinstance(res, dict):
                        engine = res.get('engine', 'Unknown')
                        output = res.get('output', '')
                        confidence = res.get('confidence', 0)
                        
                        print(f"\n{i}. {engine}")
                        print(f"   الثقة: {confidence:.2%}")
                        print(f"   المخرج:")
                        
                        # عرض المخرج بشكل مناسب
                        if len(str(output)) > 500:
                            print(f"   {str(output)[:500]}...")
                            print(f"   [... باقي المخرج مقتطع للاختصار]")
                        else:
                            print(f"   {output}")
                        print("-" * 70)
                
                # 3. المخرج المدمج
                integrated = cluster_result.get('integrated_output', {})
                if integrated:
                    print("\n📊 المخرج المدمج (بعد المراجعة):")
                    print("-" * 70)
                    if isinstance(integrated, dict):
                        for key, value in integrated.items():
                            print(f"   • {key}: {value}")
                    else:
                        print(f"   {integrated}")
            
            # 4. الملخص من LLM
            llm_summary = integration.get('llm_summary', {})
            if isinstance(llm_summary, dict):
                summary = llm_summary.get('summary', '')
                if summary:
                    print("\n💡 الملخص النهائي من LLM:")
                    print("-" * 70)
                    print(summary)
            
            # 5. المخرج المركّز
            focused = integration.get('focused_output', {})
            if focused:
                print("\n🎯 المخرج المركّز:")
                print("-" * 70)
                if isinstance(focused, dict):
                    formatted = focused.get('formatted_output', '')
                    if formatted:
                        print(formatted)
                    else:
                        print(json.dumps(focused, ensure_ascii=False, indent=2))
                else:
                    print(focused)
    
    print("\n" + "="*70)

async def show_creative_output():
    """عرض مخرجات Creative Writing بالتفصيل"""
    print_section("مخرجات الاختبار الإبداعي (Creative Writing)")
    
    theme = "اكتب قصة قصيرة عن روبوت يكتشف معنى الصداقة"
    
    print(f"📝 الموضوع: {theme}\n")
    print("⏳ جاري المعالجة...")
    
    result = await quick_start_enhanced('creative', theme)
    
    print("\n✅ القصة الكاملة:")
    print("-" * 70)
    
    if isinstance(result, dict):
        integration = result.get('integration_result', {})
        
        if isinstance(integration, dict):
            # البحث عن المحتوى الإبداعي
            cluster_result = integration.get('cluster_result', {})
            
            if isinstance(cluster_result, dict):
                # عرض نتائج المحركات الإبداعية
                results = cluster_result.get('results', [])
                
                print("\n📝 المحتوى من المحركات الإبداعية:\n")
                
                for res in results:
                    if isinstance(res, dict):
                        engine = res.get('engine', '')
                        if 'Creative' in engine or 'Quantum' in engine or 'NLP' in engine:
                            output = res.get('output', '')
                            print(f"🎨 {engine}:")
                            print(f"{output}\n")
                            print("-" * 70)
            
            # الملخص النهائي
            llm_summary = integration.get('llm_summary', {})
            if isinstance(llm_summary, dict) and llm_summary.get('summary'):
                print("\n📖 القصة النهائية (ملخص LLM):")
                print("-" * 70)
                print(llm_summary['summary'])
    
    print("\n" + "="*70)

async def main():
    print("\n" + "="*70)
    print("🎯 عرض المخرجات الكاملة من الاختبارات")
    print("="*70)
    
    # الاختبار 1: العلمي (يُظهر OptimizationEngine)
    await show_scientific_output()
    
    # الاختبار 2: الإبداعي (يُظهر القصة)
    print("\n\n")
    await show_creative_output()
    
    print("\n" + "="*70)
    print("✅ اكتمل عرض جميع المخرجات")
    print("="*70 + "\n")

if __name__ == "__main__":
    asyncio.run(main())
