import os
import sys
import time
import asyncio
import logging

# Add repo-copy to path FIRST so Core_Engines can be found
sys.path.append(os.path.join(os.getcwd(), 'repo-copy'))

from Core_Engines import bootstrap_register_all_engines
from dynamic_modules.unified_agi_system import UnifiedAGISystem

# Force the 7B model
os.environ["AGL_LLM_MODEL"] = "qwen2.5:7b-instruct"

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger("ArabicMission")

async def run_arabic_mission_async():
    print("\n🚀 [AGI] Starting Arabic Language Mission (مهمة اللغة العربية)")
    print("==============================================================")

    # 1. Initialize Unified AGI
    print("🧠 [MissionControl] Initializing Unified AGI System...")
    
    # Bootstrap Engines
    engine_registry = {}
    print("   - Bootstrapping engines...")
    bootstrap_register_all_engines(registry=engine_registry, verbose=False)
    
    agi = UnifiedAGISystem(engine_registry=engine_registry)
    
    # 2. Define the Arabic Task
    mission_prompt = """
    المهمة:
    1. قم بتحليل المثل العربي الشهير "الوقت كالسيف إن لم تقطعه قطعك" تحليلاً عميقاً.
    2. اربط هذا المفهوم بنظرية النسبية لأينشتاين (تمدد الزمن).
    3. اكتب قصة قصيرة جداً (خيال علمي) عن عالم يحاول اختراع "سيف" لقطع الوقت حرفياً للهروب من الشيخوخة.
    
    المخرجات المطلوبة:
    - لغة عربية فصحى سليمة.
    - دمج بين الفلسفة والفيزياء.
    - إبداع في القصة.
    """

    print(f"📝 Mission Briefing:\n{mission_prompt}")
    
    # 3. Execute
    print("\n🧠 [UnifiedAGI] Analyzing (جاري التحليل)...")
    start_time = time.time()
    
    result = await agi.process_with_full_agi(mission_prompt)
    
    end_time = time.time()
    duration = end_time - start_time

    # 4. Output Results
    print(f"\n✅ Mission Complete in {duration:.2f}s")
    print("==================================================================")
    
    if isinstance(result, dict):
        # Try to find the answer in various keys
        answer = result.get('final_response') or result.get('answer') or result.get('solution') or result.get('response') or result.get('output')
        
        if not answer and 'reasoning_result' in result:
             answer = result['reasoning_result'].get('answer') or result['reasoning_result'].get('solution')

        print(f"\n🧠 [AGI Response]:\n{answer if answer else 'No solution provided'}")
    else:
        print(f"\n🧠 [AGI Response]:\n{result}")

def run_arabic_mission():
    asyncio.run(run_arabic_mission_async())

if __name__ == "__main__":
    run_arabic_mission()
