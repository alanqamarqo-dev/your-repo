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

async def run_intelligence_test():
    print("🧠 Initializing Unified AGI for Intelligence Verification...")
    controller = EnhancedMissionController()
    
    if not controller.unified_system:
        print("❌ Unified AGI System failed to initialize.")
        return

    # Test Question: Requires reasoning + potential search/knowledge
    question = "Analyze the potential impact of Quantum Computing on current encryption standards (RSA) and propose a migration strategy to Post-Quantum Cryptography."
    
    print(f"\n❓ Question: {question}")
    print("⏳ Thinking (Unified AGI)...")
    
    start_time = time.time()
    
    # Use the unified system directly
    result = await controller.unified_system.process_with_full_agi(
        question, 
        context={
            "goal_type": "research", 
            "force_creativity": True,
            "autonomous_mode": True
        }
    )
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"\n✅ Result ({duration:.2f}s):\n")
    print("="*50)
    print(result)
    print("="*50)

if __name__ == "__main__":
    asyncio.run(run_intelligence_test())
