import os
import sys
import asyncio
import time

# --- Setup Environment ---
os.environ["AGL_SELF_LEARNING_ENABLE"] = "1"
os.environ["AGL_LOG_LEVEL"] = "INFO"

# Ensure imports work
root_dir = os.path.dirname(os.path.abspath(__file__))
repo_dir = os.path.join(root_dir, 'repo-copy')
if repo_dir not in sys.path:
    sys.path.insert(0, repo_dir)

from dynamic_modules.mission_control_enhanced import EnhancedMissionController

async def run_real_mission():
    print("\n🚀 [AGI] Starting Real-World Mission: Code Analysis & Optimization")
    print("===============================================================")
    
    # 1. Define a Real-World Problem (Buggy, Thread-Unsafe Code)
    buggy_code = """
import threading
import time

global_cache = []

def process_data(data):
    # Simulate processing
    time.sleep(0.1)
    # BUG: Unbounded growth (Memory Leak)
    # BUG: Thread-unsafe modification of global list (Race Condition)
    global_cache.append(data)
    return len(global_cache)

def worker():
    for i in range(1000):
        process_data(f"data_{i}")

threads = []
for _ in range(10):
    t = threading.Thread(target=worker)
    threads.append(t)
    t.start()
"""

    mission_prompt = f"""
    You are a Senior Software Architect. 
    Analyze the following Python code. It contains critical issues regarding memory management and thread safety.
    
    Code to Analyze:
    ```python
    {buggy_code}
    ```
    
    Task:
    1. Identify the specific bugs (Memory Leaks, Race Conditions).
    2. Rewrite the code to be production-ready, thread-safe, and memory-efficient.
    3. Explain your solution scientifically.
    """

    # 2. Initialize Controller
    controller = EnhancedMissionController()
    
    print(f"📝 Task: Analyzing concurrent code for memory leaks and race conditions...")
    
    # 3. Execute Mission
    start_time = time.time()
    result = await controller.orchestrate_cluster(
        cluster_key="engineering_cluster",
        task_input=mission_prompt,
        metadata={
            "type": "engineering", 
            "complexity": "high",
            "force_creativity": True, # Ask for creative solutions
            "use_unified": True       # Use the full AGI brain
        }
    )
    duration = time.time() - start_time
    
    # 4. Output Results
    print("\n===============================================================")
    print(f"✅ Mission Complete in {duration:.2f}s")
    print("===============================================================")
    
    # Extract and print the solution
    response = result.get("focused_output", "") or result.get("llm_summary", "")
    
    print("\n🧠 [AGI Solution]:")
    print(response)
    
    print("\n📊 [Internal State]:")
    if "cluster_result" in result:
        cr = result["cluster_result"]
        if isinstance(cr, dict):
            print(f"   - Confidence: {cr.get('confidence', 'N/A')}")
            print(f"   - Engine Used: {cr.get('engine', 'N/A')}")

if __name__ == "__main__":
    asyncio.run(run_real_mission())
