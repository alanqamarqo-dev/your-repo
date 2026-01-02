import os
import sys
import asyncio
import time

# --- Setup Environment ---
os.environ["AGL_SELF_LEARNING_ENABLE"] = "1"
os.environ["AGL_LOG_LEVEL"] = "INFO"
# Force the larger model
os.environ["AGL_LLM_MODEL"] = "qwen2.5:7b-instruct"

# Ensure imports work
root_dir = os.path.dirname(os.path.abspath(__file__))
repo_dir = os.path.join(root_dir, 'repo-copy')
if repo_dir not in sys.path:
    sys.path.insert(0, repo_dir)

from dynamic_modules.mission_control_enhanced import EnhancedMissionController

async def run_scientific_mission():
    print("\n🚀 [AGI] Starting Scientific & Linguistic Mission")
    print("==================================================")
    
    # Task combining Linguistics (Tone/Audience) and Science (Math/Physics)
    mission_prompt = """
    Task:
    1. Linguistically analyze the following statement for logical fallacies and tone: 
       "If the earth were spinning, the water would fly off like a wet tennis ball! It's obviously stationary."
    
    2. Scientifically refute this by calculating the centrifugal acceleration at the equator.
       - Earth Radius: 6378 km
       - Rotation Period: 24 hours
       - Formula: a = v^2 / r
    
    3. Compare the calculated acceleration with Gravity (9.8 m/s^2) to prove why water stays on.
    
    4. Output the final response in a sarcastic but educational tone.
    """

    # Initialize Controller
    controller = EnhancedMissionController()
    
    print(f"📝 Task: Logical Fallacy Analysis + Physics Calculation...")
    
    # Execute Mission
    start_time = time.time()
    result = await controller.orchestrate_cluster(
        cluster_key="scientific_cluster",
        task_input=mission_prompt,
        metadata={
            "type": "scientific", 
            "complexity": "high",
            "force_creativity": True, # For the "sarcastic" tone
            "use_unified": True
        }
    )
    duration = time.time() - start_time
    
    # Output Results
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
    asyncio.run(run_scientific_mission())
