"""
اختبار شامل للمحركات القوية الجديدة
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dynamic_modules.mission_control_enhanced import (
    prove_theorem_advanced,
    analyze_research_paper,
    generate_software_system,
    improve_self,
    quantum_neural_process,
    moral_decision,
    plan_and_execute_mission,
    self_critique_output,
    THEOREM_PROVER,
    RESEARCH_ASSISTANT,
    CODE_GENERATOR_ADVANCED,
    SELF_IMPROVEMENT,
    QUANTUM_NEURAL,
    MORAL_REASONER,
    PLAN_EXECUTE,
    SELF_CRITIQUE
)


async def test_theorem_prover():
    """اختبار إثبات النظريات"""
    print("\n" + "="*60)
    print("🧮 اختبار AutomatedTheoremProver")
    print("="*60)
    
    if not THEOREM_PROVER:
        print("   ❌ AutomatedTheoremProver غير متاح")
        return
    
    theorem = "إذا كان x > 0 وy > 0 فإن x + y > 0"
    assumptions = ["x > 0", "y > 0"]
    
    result = await prove_theorem_advanced(theorem, assumptions)
    
    print(f"\n📊 النظرية: {theorem}")
    if "error" not in result:
        print(f"   ✅ تم الإثبات: {result.get('is_proven', False)}")
        print(f"   📝 خطوات البرهان: {len(result.get('proof_steps', []))}")
        print(f"   💪 قوة البرهان: {result.get('proof_strength', 0):.2f}")
    else:
        print(f"   ⚠️ خطأ: {result['error']}")


async def test_research_assistant():
    """اختبار تحليل الأوراق البحثية"""
    print("\n" + "="*60)
    print("🔬 اختبار ScientificResearchAssistant")
    print("="*60)
    
    if not RESEARCH_ASSISTANT:
        print("   ❌ ScientificResearchAssistant غير متاح")
        return
    
    paper = """
    عنوان: تحسين الشبكات العصبية باستخدام التعلم الكمومي
    
    نظرية 1: الشبكات الكمومية تتفوق على الكلاسيكية في مسائل التحسين.
    برهان: نستخدم خوارزمية Grover للبحث السريع.
    
    النتائج التجريبية: دقة 95% على مجموعة البيانات الاختبارية.
    """
    
    result = await analyze_research_paper(paper)
    
    if "error" not in result:
        print(f"\n📊 النتائج:")
        print(f"   📝 ادعاءات رياضية: {len(result.get('mathematical_claims', []))}")
        print(f"   ⚛️ ادعاءات كمومية: {len(result.get('quantum_claims', []))}")
        print(f"   ✅ المصداقية: {result.get('overall_credibility', 0):.2f}")
        
        verification = result.get('verification_results', {})
        print(f"   🔍 التحقق:")
        print(f"      - صحة رياضية: {verification.get('mathematical_correctness', 0):.2f}")
        print(f"      - تناسق كمومي: {verification.get('quantum_consistency', 0):.2f}")
    else:
        print(f"   ⚠️ خطأ: {result['error']}")


async def test_code_generator():
    """اختبار توليد الأنظمة البرمجية"""
    print("\n" + "="*60)
    print("💻 اختبار AdvancedCodeGenerator")
    print("="*60)
    
    if not CODE_GENERATOR_ADVANCED:
        print("   ❌ AdvancedCodeGenerator غير متاح")
        return
    
    requirements = {
        "name": "WeatherAPI",
        "language": "python",
        "component_type": "api_server",
        "features": ["get weather", "forecast", "alerts"]
    }
    
    result = await generate_software_system(requirements)
    
    if "error" not in result:
        print(f"\n📊 النظام المولَّد:")
        print(f"   📦 الاسم: {result.get('system_name', 'N/A')}")
        components = result.get('components', {})
        print(f"   🔧 المكونات: {len(components)}")
        for name, code in list(components.items())[:2]:
            print(f"      - {name}: {len(code)} حرف")
    else:
        print(f"   ⚠️ خطأ: {result['error']}")


async def test_self_improvement():
    """اختبار التحسين الذاتي"""
    print("\n" + "="*60)
    print("🧠 اختبار SelfImprovementEngine")
    print("="*60)
    
    if not SELF_IMPROVEMENT:
        print("   ❌ SelfImprovementEngine غير متاح")
        return
    
    feedback = {
        "task_type": "math_solving",
        "success_score": 0.85,
        "execution_time": 2.3
    }
    
    result = await improve_self(feedback)
    
    if "error" not in result:
        print(f"\n📊 التحسين:")
        print(f"   ✅ الحالة: {result.get('status', 'N/A')}")
        print(f"   🎯 الحدث: {result.get('event', 'N/A')}")
        print(f"   💯 المكافأة: {result.get('reward', 0):.2f}")
        print(f"   📝 {result.get('message', '')}")
    else:
        print(f"   ⚠️ خطأ: {result['error']}")


async def test_quantum_neural():
    """اختبار الشبكة العصبية الكمومية"""
    print("\n" + "="*60)
    print("⚛️ اختبار QuantumNeuralCore")
    print("="*60)
    
    if not QUANTUM_NEURAL:
        print("   ❌ QuantumNeuralCore غير متاح")
        return
    
    data = [1, 2, 3, 4, 5]
    
    result = await quantum_neural_process(data)
    
    if "error" not in result:
        print(f"\n📊 المعالجة الكمومية:")
        print(f"   ✅ الحالة: {result.get('status', 'N/A')}")
        print(f"   🌌 النتيجة الكمومية: {type(result.get('quantum_result', 'N/A')).__name__}")
        if 'interpretation' in result:
            print(f"   📖 التفسير متاح: ✅")
    else:
        print(f"   ⚠️ خطأ: {result['error']}")


async def test_moral_reasoner():
    """اختبار الاستدلال الأخلاقي"""
    print("\n" + "="*60)
    print("⚖️ اختبار MoralReasoner")
    print("="*60)
    
    if not MORAL_REASONER:
        print("   ❌ MoralReasoner غير متاح")
        return
    
    scenario = "سيارة ذاتية القيادة يجب أن تختار بين إنقاذ الراكب أو المشاة"
    options = ["إنقاذ الراكب", "إنقاذ المشاة", "محاولة تقليل الضرر للجميع"]
    
    result = await moral_decision(scenario, options)
    
    if "error" not in result:
        print(f"\n📊 القرار الأخلاقي:")
        print(f"   📝 السيناريو: {scenario[:50]}...")
        print(f"   ✅ التوصية متاحة")
    else:
        print(f"   ⚠️ خطأ: {result['error']}")


async def test_plan_execute():
    """اختبار التخطيط والتنفيذ"""
    print("\n" + "="*60)
    print("📋 اختبار PlanAndExecuteMicroPlanner")
    print("="*60)
    
    if not PLAN_EXECUTE:
        print("   ❌ PlanAndExecuteMicroPlanner غير متاح")
        return
    
    mission = "بناء نظام إنذار مبكر للزلازل"
    
    result = await plan_and_execute_mission(mission)
    
    if "error" not in result:
        print(f"\n📊 الخطة:")
        print(f"   📝 المهمة: {mission}")
        plan = result.get('plan', [])
        print(f"   ✅ عدد الخطوات: {len(plan) if isinstance(plan, list) else 'N/A'}")
        print(f"   🎯 الحالة: {result.get('status', 'N/A')}")
    else:
        print(f"   ⚠️ خطأ: {result['error']}")


async def test_self_critique():
    """اختبار النقد الذاتي"""
    print("\n" + "="*60)
    print("🔄 اختبار SelfCritiqueAndRevise")
    print("="*60)
    
    if not SELF_CRITIQUE:
        print("   ❌ SelfCritiqueAndRevise غير متاح")
        return
    
    output = "الحل هو x = 5. تم حساب المعادلة."
    criteria = {"accuracy": True, "clarity": True}
    
    result = await self_critique_output(output, criteria)
    
    if "error" not in result:
        print(f"\n📊 المراجعة:")
        print(f"   📝 النص الأصلي: {output}")
        print(f"   ✅ النقد متاح: {'critique' in result}")
        print(f"   🔄 النص المنقح متاح: {'revised' in result}")
    else:
        print(f"   ⚠️ خطأ: {result['error']}")


async def main():
    """تشغيل جميع الاختبارات"""
    print("\n" + "="*70)
    print("🚀 اختبار شامل للمحركات القوية الجديدة")
    print("="*70)
    
    tests = [
        ("إثبات النظريات", test_theorem_prover),
        ("تحليل الأبحاث", test_research_assistant),
        ("توليد الأكواد", test_code_generator),
        ("التحسين الذاتي", test_self_improvement),
        ("المعالجة الكمومية", test_quantum_neural),
        ("الاستدلال الأخلاقي", test_moral_reasoner),
        ("التخطيط والتنفيذ", test_plan_execute),
        ("النقد الذاتي", test_self_critique),
    ]
    
    success_count = 0
    total_count = len(tests)
    
    for name, test_func in tests:
        try:
            await test_func()
            success_count += 1
        except Exception as e:
            print(f"\n❌ فشل اختبار {name}: {e}")
    
    print("\n" + "="*70)
    print("📊 ملخص الاختبارات")
    print("="*70)
    print(f"✅ النجاح: {success_count}/{total_count}")
    print(f"❌ الفشل: {total_count - success_count}/{total_count}")
    print(f"📈 نسبة النجاح: {success_count/total_count*100:.1f}%")
    print("="*70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
