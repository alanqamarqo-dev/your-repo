"""Test LLM-powered engines in mission_control_enhanced"""
import asyncio
import sys
sys.path.insert(0, 'D:\\AGL\\repo-copy')

from dynamic_modules.mission_control_enhanced import quick_start_enhanced

async def test_math_routing():
    print("Testing math routing...")
    result = await quick_start_enhanced("science", "Solve: 3x - 7 = 8")
    print(f"\nResult Engine: {result.get('meta', {}).get('engine')}")
    print(f"Confidence: {result.get('meta', {}).get('confidence')}")
    print(f"Real Processing: {result.get('meta', {}).get('real_processing')}")
    print(f"Reply: {result.get('reply', '')[:200]}")

if __name__ == "__main__":
    asyncio.run(test_math_routing())
