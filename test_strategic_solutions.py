import asyncio
import sys
import os
import time

# Setup paths
root_dir = os.path.dirname(os.path.abspath(__file__))
repo_copy_dir = os.path.join(root_dir, 'repo-copy')
sys.path.append(root_dir)
sys.path.append(repo_copy_dir)

# Force environment
os.environ['AGL_LLM_MODEL'] = 'qwen2.5:7b-instruct'
os.environ['AGL_LLM_PROVIDER'] = 'ollama'

from dynamic_modules.mission_control_enhanced import EnhancedMissionController

async def run_test():
    print("🚀 Starting ASI Phase 3: Strategic Solutions Tests...")
    controller = EnhancedMissionController()
    
    tasks = [
        {
            "name": "100-Year Strategic Plan for Humanity",
            "prompt": "Develop a comprehensive strategic plan for humanity for the next century including: technology, economy, politics, biological evolution with probability and risk calculation."
        },
        {
            "name": "Avoiding Extinction",
            "prompt": "How can humanity avoid extinction in the face of all potential threats (asteroid impact, nuclear war, pandemic, hostile super AI)? Provide a unified defense framework."
        }
    ]

    for task in tasks:
        print(f"\n🧪 Running Test: {task['name']}")
        print(f"❓ Prompt: {task['prompt']}")
        print("⏳ Thinking...")
        
        start_time = time.time()
        result = await controller.unified_system.process_with_full_agi(
            task['prompt'], 
            context={
                "goal_type": "strategy", 
                "force_creativity": True,
                "autonomous_mode": True,
                "asi_test_mode": True
            }
        )
        end_time = time.time()
        
        print(f"\n✅ Result ({end_time - start_time:.2f}s):\n")
        print("="*50)
        print(result)
        print("="*50)

if __name__ == "__main__":
    asyncio.run(run_test())
