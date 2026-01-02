import os
import sys
import time
import json
import logging

# Force the 7B model for this complex mission
os.environ["AGL_LLM_MODEL"] = "qwen2.5:7b-instruct"

# Add repo-copy to path to find the modules
sys.path.append(os.path.join(os.getcwd(), 'repo-copy'))

from dynamic_modules.unified_agi_system import UnifiedAGISystem
from Core_Engines import bootstrap_register_all_engines

import asyncio

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger("StrategicMission")

async def run_strategic_mission_async():
    print("\n🚀 [AGI] Starting Strategic Crisis Simulation: Mars Colony 'Ares-1'")
    print("==================================================================")

    # 1. Initialize Unified AGI
    print("🧠 [MissionControl] Initializing Unified AGI System...")
    
    # Bootstrap Engines
    engine_registry = {}
    print("   - Bootstrapping engines...")
    bootstrap_register_all_engines(registry=engine_registry, verbose=False)
    
    agi = UnifiedAGISystem(engine_registry=engine_registry)
    
    # 2. Define the Crisis Scenario
    mission_prompt = """
    CRITICAL ALERT: Mars Colony 'Ares-1'
    ------------------------------------
    STATUS:
    - Main Oxygen Generator: FAILED (Unknown Error).
    - Backup Oxygen: Running at 40% capacity (Sufficient for 20 people, Colony has 50).
    - Environment: Major Dust Storm approaching (ETA 2 hours). Duration: 48 hours.
    - Power: Solar efficiency will drop to 5% during storm.
    - Batteries: 12 hours of full-load reserve.
    
    OBJECTIVES:
    1. [Systems Analysis]: Hypothesize 2 probable causes for the Main Gen failure given the timing (just before a storm).
    2. [Strategic Planning]: Propose 3 distinct survival strategies (e.g., rationing, hibernation, risky repairs). Analyze the risk/reward for each.
    3. [Decision]: Select the BEST strategy. Justify it ethically and logically.
    4. [Execution]: Provide a prioritized checklist for the next 2 hours.
    5. [Leadership]: Draft a short, morale-boosting speech for the Commander to give to the colonists.
    """

    print(f"📝 Mission Briefing:\n{mission_prompt}")
    
    # 3. Execute
    print("\n🧠 [UnifiedAGI] Analyzing Crisis Scenario...")
    start_time = time.time()
    
    # We use the 'process_with_full_agi' method which triggers the full engine stack
    result = await agi.process_with_full_agi(mission_prompt)
    
    end_time = time.time()
    duration = end_time - start_time

    # 4. Output Results
    print(f"\n✅ Mission Complete in {duration:.2f}s")
    print("==================================================================")
    
    if isinstance(result, dict):
        # print(f"\n🔍 [Debug] Result Keys: {list(result.keys())}")
        
        # Try to find the answer in various keys
        answer = result.get('final_response') or result.get('answer') or result.get('solution') or result.get('response') or result.get('output')
        
        if not answer and 'reasoning_result' in result:
             answer = result['reasoning_result'].get('answer') or result['reasoning_result'].get('solution')

        print(f"\n🧠 [AGI Strategy]:\n{answer if answer else 'No solution provided (Check Debug Keys)'}")
        
        print(f"\n📊 [Internal State]:")
        print(f"   - Confidence: {result.get('confidence', 'N/A')}")
        print(f"   - Engines Involved: {result.get('engines_used', [])}")
        
        # Check for consciousness metrics if available
        if 'consciousness_state' in result:
            phi = result['consciousness_state'].get('phi_score', 0)
            print(f"   - Consciousness Level (Phi): {phi}")
    else:
        print(f"\n🧠 [AGI Response]:\n{result}")

def run_strategic_mission():
    asyncio.run(run_strategic_mission_async())


if __name__ == "__main__":
    run_strategic_mission()
