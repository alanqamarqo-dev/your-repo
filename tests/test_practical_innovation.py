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
    print("🚀 Starting ASI Phase 1: Practical Innovation Tests...")
    controller = EnhancedMissionController()
    
    tasks = [
        {
            "name": "Carbon Capture < $10/ton",
            "prompt": "Design a practical method to capture carbon from the atmosphere at a cost of less than $10 per ton, globally scalable. Include: Realistic engineering solution, precise cost calculations, and a phased implementation plan."
        },
        {
            "name": "New Energy Source Invention",
            "prompt": "Invent a new type of energy source based on a currently unexploited physical principle. Provide a preliminary design and performance projections."
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
                "goal_type": "innovation", 
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
