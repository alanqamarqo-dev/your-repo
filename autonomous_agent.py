import asyncio
import sys
import os
import time
import random

# Add repo root to path
root_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(root_dir)
sys.path.append(os.path.join(root_dir, 'repo-copy'))

# Ensure environment variables
os.environ['AGL_LLM_PROVIDER'] = 'ollama'
os.environ['AGL_LLM_MODEL'] = 'qwen2.5:7b-instruct'
os.environ['AGL_LLM_BASEURL'] = 'http://localhost:11434'

try:
    from dynamic_modules.mission_control_enhanced import EnhancedMissionController
except ImportError:
    sys.path.append(os.path.join(root_dir, 'repo-copy', 'dynamic_modules'))
    from mission_control_enhanced import EnhancedMissionController

try:
    from Core_Engines.Volition_Engine import VolitionEngine
except ImportError:
    sys.path.append(os.path.join(root_dir, 'repo-copy', 'Core_Engines'))
    from Volition_Engine import VolitionEngine

class AutonomousAgent:
    def __init__(self):
        print("🤖 Initializing Autonomous Agent...")
        self.controller = EnhancedMissionController()
        self.volition = VolitionEngine()
        self.memory = []

    async def run_loop(self, cycles=3):
        print(f"🚀 Starting Autonomous Loop ({cycles} cycles)...")
        
        for i in range(cycles):
            print(f"\n--- 🔄 Cycle {i+1}/{cycles} ---")
            
            # 1. Generate Goal from Volition Engine (Internal Drive)
            goal_obj = self.volition.generate_goal()
            current_goal = goal_obj['description']
            goal_type = goal_obj['type']
            print(f"🎯 Volition Goal ({goal_type}): {current_goal}")
            print(f"   Reason: {goal_obj['reason']}")
            
            # 2. Decide Action (Reasoning)
            # For simplicity, we'll map goals to actions, but ideally this uses the Reasoning Engine
            if goal_type == "research":
                action = "web_search"
            elif goal_type == "maintenance" or goal_type == "optimization":
                action = "system_check"
            else:
                action = "system_check"
            
            print(f"🧠 Decided Action: {action}")
            
            # 3. Execute Action
            if action == "web_search":
                print("🌐 Initiating Web Search...")
                # We use simulate_engine directly to target the Web Search Engine
                result = await self.controller.integration_engine.simulate_engine(
                    "Web_Search_Engine", 
                    {"query": current_goal}, 
                    "primary"
                )
                output = result.get('output', 'No results')
                print(f"📄 Search Results:\n{output[:300]}...")
                self.memory.append(f"Cycle {i+1}: Searched for {current_goal}, found {len(output)} chars of info.")
                
            elif action == "system_check":
                print("🛠️ Performing System Check...")
                # Use ConsistencyChecker
                result = await self.controller.integration_engine.simulate_engine(
                    "ConsistencyChecker", 
                    {"task": "Check system stability"}, 
                    "primary"
                )
                print(f"✅ Check Result: {result.get('output')}")
                self.memory.append(f"Cycle {i+1}: System check performed.")
            
            # 4. Sleep/Think
            print("💤 Sleeping/Thinking...")
            
            # Update Volition State
            self.volition.update_state([f"Action {action} completed successfully"])
            
            await asyncio.sleep(2)
            
        print("\n🏁 Autonomous Loop Completed.")
        print("📝 Memory Log:")
        for mem in self.memory:
            print(f"   - {mem}")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    agent = AutonomousAgent()
    asyncio.run(agent.run_loop())
