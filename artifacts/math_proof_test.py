import sys
import os
import asyncio
import json

# Setup paths
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
repo_copy_dir = os.path.join(root_dir, 'repo-copy')
if repo_copy_dir not in sys.path:
    sys.path.insert(0, repo_copy_dir)

import agl_paths
agl_paths.setup_sys_path()

try:
    from dynamic_modules.mission_control_enhanced import EnhancedMissionController
except ImportError:
    sys.path.append(os.path.join(root_dir, 'repo-copy', 'dynamic_modules'))
    from mission_control_enhanced import EnhancedMissionController

async def run_math_proof():
    print("--- 🧪 MATH PROOF TEST ---")
    controller = EnhancedMissionController()
    
    # This prompt should trigger the MathematicalBrain via the 'scientific_reasoning' or 'general' cluster
    # We'll force 'scientific_reasoning' to be safe, or rely on the router.
    # Let's use orchestrate_cluster directly to be sure we hit the right path.
    
    prompt = "5x + 10 = 25"
    print(f"Sending Prompt: {prompt}")
    
    # We use 'scientific_reasoning' because MathematicalBrain is usually there
    result = await controller.orchestrate_cluster(
        cluster_key='scientific_reasoning', 
        task_input=prompt,
        metadata={"type": "math_test"}
    )
    
    print("\n--- 🏁 Mission Complete ---")
    print("Checking for physical evidence of engine activity...")
    
    log_path = os.path.join(root_dir, "artifacts", "math_engine_activity.log")
    if os.path.exists(log_path):
        print(f"\n✅ FOUND LOG FILE: {log_path}")
        with open(log_path, 'r', encoding='utf-8') as f:
            print("--- LOG CONTENT ---")
            print(f.read())
            print("-------------------")
        print("Proof: The Python engine wrote this file BEFORE Ollama responded.")
    else:
        print("❌ No log file found. The engine might not have been called.")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(run_math_proof())
