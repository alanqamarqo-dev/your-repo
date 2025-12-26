import os
import sys
import json
import time
import asyncio

# Force Self-Learning Enable
os.environ["AGL_SELF_LEARNING_ENABLE"] = "1"
os.environ["AGL_SELF_LEARNING_LOGDIR"] = "artifacts/learning_logs"

# Ensure we can import from repo-copy
root_dir = os.path.dirname(os.path.abspath(__file__))
repo_dir = os.path.join(root_dir, "repo-copy")
if repo_dir not in sys.path:
    sys.path.insert(0, repo_dir)

from dynamic_modules.mission_control_enhanced import EnhancedMissionController

STATS_FILE = os.path.join(root_dir, "artifacts", "engine_stats.json")
LEARNING_CURVE_FILE = os.path.join(root_dir, "artifacts", "learning_curve.json")

def read_json(path):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return None

async def run_verification():
    print("[1]  Reading Initial State...")
    initial_stats = read_json(STATS_FILE)
    initial_curve = read_json(LEARNING_CURVE_FILE)
    
    initial_curve_len = len(initial_curve) if initial_curve else 0
    print(f"    - Engine Stats Keys: {list(initial_stats.keys()) if initial_stats else "None"}")
    print(f"    - Learning Curve Epochs: {initial_curve_len}")

    print("\n[2]  Running Learning Task...")
    # Initialize Controller
    controller = EnhancedMissionController()
    
    # Run a task that should trigger learning
    # Using a task that involves reasoning and creativity to engage multiple engines
    task = "Analyze the impact of quantum computing on cryptography and propose a new security protocol."
    
    result = await controller.orchestrate_cluster(
        cluster_key="verification_cluster",
        task_input=task,
        metadata={"type": "scientific", "force_creativity": True}
    )
    
    print(f"\n[3]  Checking for Updates...")
    
    # Allow a moment for async file writes
    await asyncio.sleep(2)
    
    final_stats = read_json(STATS_FILE)
    final_curve = read_json(LEARNING_CURVE_FILE)
    final_curve_len = len(final_curve) if final_curve else 0
    
    print(f"    - Final Learning Curve Epochs: {final_curve_len}")
    
    if final_curve_len > initial_curve_len:
        print("\n SUCCESS: Learning Curve updated! New epoch recorded.")
        new_entry = final_curve[-1]
        print(f"    New Epoch: {new_entry.get("epoch")}")
        print(f"    Avg Reward: {new_entry.get("avg_reward")}")
    else:
        print("\n WARNING: Learning Curve NOT updated.")

    # Check engine stats changes
    if initial_stats and final_stats:
        diff = []
        for k, v in final_stats.items():
            if k not in initial_stats:
                diff.append(f"New Engine: {k}")
            elif v != initial_stats[k]:
                diff.append(f"Updated: {k}")
        
        if diff:
            print(f" SUCCESS: Engine Stats updated! Changes: {diff}")
        else:
            print(" Engine Stats unchanged.")

if __name__ == "__main__":
    asyncio.run(run_verification())
