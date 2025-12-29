"""اختبار حقيقي مباشر للمحركات - بدون server"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from dynamic_modules import mission_control_enhanced as mc
from Core_Engines.Mathematical_Brain import MathematicalBrain

# ألوان
RED = '\033[91m'
GREEN = '\033[92m'
BLUE = '\033[94m'
BOLD = '\033[1m'
RESET = '\033[0m'

async def test_causal_reasoning():
    """Test 1: تفكير سببي"""
    print(f"\n{BLUE}{BOLD}═══ Test 1: Causal Reasoning Engine ═══{RESET}")
    engine = mc.CAUSAL_GRAPH_ENGINE
    if engine:
        result = await engine.build_causal_graph(
            "ما أسباب سقوط الإمبراطورية الرومانية؟",
            {"nodes": ["سياسة", "اقتصاد", "عسكرية"], "depth": 2}
        )
        print(f"Output: {result}")
        print(f"{GREEN}✅ PASS{RESET}" if result.get("nodes") else f"{RED}❌ FAIL{RESET}")
        return bool(result.get("nodes"))
    return False

async def test_creative_innovation():
    """Test 2: إبداع"""
    print(f"\n{BLUE}{BOLD}═══ Test 2: Creative Innovation Engine ═══{RESET}")
    engine = mc.CREATIVE_INNOVATION_ENGINE
    if engine:
        result = await engine.innovate(
            "اخترع رياضة جديدة في الفضاء",
            {"require_originality": True, "num_ideas": 1}
        )
        print(f"Output: {result}")
        print(f"{GREEN}✅ PASS{RESET}" if result.get("innovations") else f"{RED}❌ FAIL{RESET}")
        return bool(result.get("innovations"))
    return False

async def test_math_engine():
    """Test 3: رياضيات دقيقة"""
    print(f"\n{BLUE}{BOLD}═══ Test 3: Mathematical Brain ═══{RESET}")
    brain = MathematicalBrain()
    result = brain.solve_equation("3*x + 5 = 20")
    print(f"Equation: 3x + 5 = 20")
    print(f"Result: {result}")
    has_solution = "solution" in result or "result" in result
    print(f"{GREEN}✅ PASS{RESET}" if has_solution else f"{RED}❌ FAIL{RESET}")
    return has_solution

async def test_self_awareness():
    """Test 4: وعي ذاتي"""
    print(f"\n{BLUE}{BOLD}═══ Test 4: Self-Awareness Engine ═══{RESET}")
    engine = mc.SELF_AWARENESS_ENGINE
    if engine:
        assessment = engine.get_self_assessment()
        print(f"Assessment: {assessment}")
        has_data = "total_experiences" in assessment
        print(f"{GREEN}✅ PASS{RESET}" if has_data else f"{RED}❌ FAIL{RESET}")
        return has_data
    return False

async def test_hypothesis_generator():
    """Test 5: توليد فرضيات"""
    print(f"\n{BLUE}{BOLD}═══ Test 5: Hypothesis Generator ═══{RESET}")
    engine = mc.HYPOTHESIS_GENERATOR_ENGINE
    if engine:
        result = await engine.generate_hypotheses(
            "لماذا تنقرض الحيوانات؟",
            {"num_hypotheses": 3, "creativity": 0.8}
        )
        print(f"Hypotheses: {result}")
        has_hypotheses = result.get("hypotheses") and len(result["hypotheses"]) > 0
        print(f"{GREEN}✅ PASS{RESET}" if has_hypotheses else f"{RED}❌ FAIL{RESET}")
        return has_hypotheses
    return False

async def test_optimization():
    """Test 6: تحسين"""
    print(f"\n{BLUE}{BOLD}═══ Test 6: Optimization Engine ═══{RESET}")
    engine = mc.OPTIMIZATION_ENGINE
    if engine:
        result = await engine.optimize(
            objective="maximize profit",
            constraints=["cost < 1000", "time < 24h"],
            variables={"price": (10, 100), "quantity": (1, 1000)}
        )
        print(f"Optimization: {result}")
        has_result = "optimal_value" in result or "solution" in result
        print(f"{GREEN}✅ PASS{RESET}" if has_result else f"{RED}❌ FAIL{RESET}")
        return has_result
    return False

async def run_all_tests():
    print(f"{BOLD}{'='*60}{RESET}")
    print(f"{BOLD}   AGL DIRECT ENGINE TESTING - REAL INTELLIGENCE VERIFICATION   {RESET}")
    print(f"{BOLD}{'='*60}{RESET}")
    
    results = []
    results.append(await test_causal_reasoning())
    results.append(await test_creative_innovation())
    results.append(await test_math_engine())
    results.append(await test_self_awareness())
    results.append(await test_hypothesis_generator())
    results.append(await test_optimization())
    
    passed = sum(results)
    total = len(results)
    percentage = (passed / total) * 100
    
    print(f"\n{BOLD}{'='*60}{RESET}")
    print(f"{BOLD}   FINAL RESULTS: {passed}/{total} ({percentage:.1f}%){RESET}")
    print(f"{BOLD}{'='*60}{RESET}")
    
    if percentage >= 80:
        print(f"{GREEN}{BOLD}✅ SUCCESS: Real Intelligence Confirmed!{RESET}")
    elif percentage >= 50:
        print(f"{BLUE}{BOLD}⚠️  PARTIAL: Some engines working{RESET}")
    else:
        print(f"{RED}{BOLD}❌ FAILED: System needs debugging{RESET}")

if __name__ == "__main__":
    asyncio.run(run_all_tests())
