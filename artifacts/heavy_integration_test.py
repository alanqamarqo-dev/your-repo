import sys
import os
import asyncio
import json
import time

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

async def run_heavy_test():
    print("\n🚀 --- HEAVY INTEGRATION TEST: ALL ENGINES --- 🚀\n")
    controller = EnhancedMissionController()
    
    tasks = [
        {
            "name": "Scientific Reasoning (Math + Quantum)",
            "cluster": "scientific_reasoning",
            "prompt": "Calculate the eigenvalues of a 4x4 matrix representing a quantum gate, then simulate the circuit.",
            "metadata": {"type": "quantum_simulation"}
        },
        {
            "name": "Strategic Planning (Hypothesis + Strategy)",
            "cluster": "strategic_planning",
            "prompt": "Develop a hypothesis for the impact of AGI on global economics and outline a 5-year adaptation strategy.",
            "metadata": {"type": "strategic_analysis"}
        },
        {
            "name": "Technical Analysis (Code + Simulation)",
            "cluster": "technical_analysis",
            "prompt": "Generate a Python script to optimize a neural network using genetic algorithms.",
            "metadata": {"type": "code_generation"}
        }
    ]
    
    results = {}
    
    for task in tasks:
        print(f"\n>>> ACTIVATING CLUSTER: {task['cluster'].upper()}...")
        print(f"   Task: {task['prompt']}")
        
        start_time = time.time()
        result = await controller.orchestrate_cluster(
            cluster_key=task['cluster'],
            task_input=task['prompt'],
            metadata=task['metadata']
        )
        duration = time.time() - start_time
        
        print(f"   ✅ Completed in {duration:.2f}s")
        
        # Extract active engines from the result
        active_engines = []
        if 'cluster_result' in result:
            for res in result['cluster_result']:
                if isinstance(res, dict) and 'engine' in res:
                    active_engines.append(res['engine'])
        
        print(f"   ⚙️ Active Engines: {', '.join(active_engines)}")
        results[task['name']] = active_engines

    print("\n" + "="*50 + "\n")
    print("🔍 --- PHYSICAL EVIDENCE CHECK ---")
    
    log_files = {
        "MathematicalBrain": "math_engine_activity.log",
        "QuantumProcessor": "quantum_engine_activity.log",
        "HypothesisGenerator": "hypothesis_engine_activity.log"
    }
    
    for engine, log_file in log_files.items():
        path = os.path.join(root_dir, "artifacts", log_file)
        if os.path.exists(path):
            print(f"   ✅ {engine}: Log Found ({log_file})")
            # Read last line
            with open(path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                if lines:
                    print(f"      Last Entry: {lines[-1].strip()}")
        else:
            print(f"   ❌ {engine}: No Log Found")

    print("\n✅ HEAVY TEST COMPLETE.")

if __name__ == "__main__":
    asyncio.run(run_heavy_test())
