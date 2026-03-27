import sys
import os
import asyncio
import json

# Add repo root to path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
repo_copy_dir = os.path.join(root_dir, 'repo-copy')
if repo_copy_dir not in sys.path:
    sys.path.insert(0, repo_copy_dir)

import agl_paths
agl_paths.setup_sys_path()
agl_paths.load_env_defaults()

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
            
            # --- SHOW INTERNAL ENGINE WORK (THE "STRENGTH") ---
            print("\n    🔍 [INTERNAL ENGINE DATA - EVIDENCE OF REAL WORK]:")
            cluster_res = result.get('cluster_result', {})
            if isinstance(cluster_res, dict):
                # Show the specific engine that did the work
                active_engine = cluster_res.get('engine', 'Unknown')
                confidence = cluster_res.get('confidence', 0.0)
                print(f"       ⚙️ Active Engine: {active_engine}")
                print(f"       🧠 Confidence Score: {confidence}")
                
                # Show specific keys based on engine type to prove it's not just text
                if 'calculations' in cluster_res:
                    print(f"       🧮 Calculations: {str(cluster_res['calculations'])[:200]}...")
                if 'simulation' in cluster_res:
                    print(f"       🧪 Simulation Data: {str(cluster_res['simulation'])[:200]}...")
                if 'reasoning_trace' in cluster_res:
                    print(f"       🔗 Reasoning Steps: {len(cluster_res['reasoning_trace'])} steps executed.")
                
                # If it's a raw output, show a snippet
                if 'output' in cluster_res:
                    out_preview = str(cluster_res['output'])[:150].replace('\n', ' ')
                    print(f"       📄 Raw Engine Output Preview: {out_preview}...")
            else:
                print(f"       ⚠️ Raw Result: {str(cluster_res)[:200]}...")
            print("    ---------------------------------------------------\n")

            print(f"    📝 [FULL LLM OUTPUT]:\n    {summary}\n")

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
