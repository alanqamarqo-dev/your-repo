import sys
import os
import asyncio
import json

# Add repo root to path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root_dir)
sys.path.append(os.path.join(root_dir, 'repo-copy'))

# Ensure environment variables
os.environ['AGL_LLM_PROVIDER'] = 'ollama'
os.environ['AGL_LLM_MODEL'] = 'qwen2.5:7b-instruct'
os.environ['AGL_LLM_BASEURL'] = 'http://localhost:11434'

try:
    from dynamic_modules.mission_control_enhanced import EnhancedMissionController, SCIENTIFIC_ORCHESTRATOR
except ImportError:
    sys.path.append(os.path.join(root_dir, 'repo-copy', 'dynamic_modules'))
    from mission_control_enhanced import EnhancedMissionController, SCIENTIFIC_ORCHESTRATOR

async def run_grand_challenge():
    print("--- 🌍 AGL GRAND CHALLENGE: FULL SYSTEM ACTIVATION ---")
    print("Objective: Activate all major engine clusters in a single session.")
    
    controller = EnhancedMissionController()
    
    tasks = [
        {
            "name": "🎨 Creative Phase",
            "cluster": "creative_writing",
            "prompt": "Write a short, emotional poem about a robot discovering a flower on Mars."
        },
        {
            "name": "🧪 Scientific Phase",
            "cluster": "scientific_reasoning",
            "prompt": "Calculate the energy required to melt 1kg of ice on Europa (Temp -160C) into liquid water at 10C. Show formulas."
        },
        {
            "name": "♟️ Strategic Phase",
            "cluster": "strategic_planning",
            "prompt": "Outline a 3-step strategy to terraform Mars using current technology constraints."
        },
        {
            "name": "💻 Technical Phase",
            "cluster": "technical_analysis",
            "prompt": "Write a Python function to calculate the Fibonacci sequence using dynamic programming."
        }
    ]
    
    results = {}
    
    for task in tasks:
        print(f"\n\n>>> ACTIVATING: {task['name']} (Cluster: {task['cluster']})")
        print(f"    Prompt: {task['prompt']}")
        
        try:
            # Use orchestrate_cluster directly for specific control
            result = await controller.orchestrate_cluster(
                cluster_key=task['cluster'],
                task_input=task['prompt'],
                metadata={"type": "grand_challenge"}
            )
            
            # Extract summary
            summary = ""
            if isinstance(result.get('llm_summary'), dict):
                summary = result['llm_summary'].get('summary', '')
            else:
                summary = str(result.get('llm_summary', ''))
                
            results[task['name']] = "✅ Success" if summary else "⚠️ No Output Captured (Check Stream)"
            
            print(f"    Result Captured: {len(summary)} chars")
            
        except Exception as e:
            print(f"    ❌ FAILED: {e}")
            results[task['name']] = f"❌ Error: {e}"

    print("\n\n--- 🏆 GRAND CHALLENGE REPORT ---")
    for phase, status in results.items():
        print(f"{phase}: {status}")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(run_grand_challenge())
