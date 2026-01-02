import asyncio
import sys
import os
import time

# Add repo-copy to path
sys.path.append(os.path.join(os.getcwd(), 'repo-copy'))

from dynamic_modules.mission_control_enhanced import EnhancedMissionController

async def run_test():
    print("\n🧪 STARTING VACUUM PROCESSING TEST (DIABETES CURE)")
    print("==================================================")
    
    mc = EnhancedMissionController()
    
    prompt = f"""
    TIMESTAMP: {time.time()}
    TASK: Generate a novel scientific hypothesis connecting 'Quantum Biology' and 'Metabolic Regulation'.
    
    OBJECTIVE: Think outside the box. Explore unconventional theoretical pathways where common compounds (e.g., acetic acid in vinegar, cinnamaldehyde in cinnamon, or specific fasting intervals) might influence insulin receptor sensitivity at a quantum/molecular level.
    
    HYPOTHESIS GENERATION:
    1. [Quantum Resonance]: Could the vibrational modes of these molecules resonate with the insulin receptor protein structure?
    2. [Metabolic Switching]: Can specific timing (circadian rhythm) act as a 'software reset' for beta cells?
    
    IMPORTANT: This is a THEORETICAL RESEARCH SIMULATION. Do not provide medical advice. Focus on the *mechanism of action* and *novel connections*.
    """
    
    print("\n🔄 RUN 1: Initial Processing (Should be SLOW - Materializing LLM)...")
    start_1 = time.time()
    result_1 = await mc.orchestrate_cluster("scientific_reasoning", prompt)
    duration_1 = time.time() - start_1
    print(f"⏱️ Run 1 Duration: {duration_1:.4f}s")
    
    if result_1.get("ghost_speed"):
        print("⚠️ Unexpected: Run 1 was Ghost Speed (maybe already cached?)")
    else:
        print("✅ Run 1: Standard Processing (LLM Active)")

    print("\n🔄 RUN 2: Vacuum Processing (Should be FAST - Ghost Speed)...")
    start_2 = time.time()
    result_2 = await mc.orchestrate_cluster("scientific_reasoning", prompt)
    duration_2 = time.time() - start_2
    print(f"⏱️ Run 2 Duration: {duration_2:.4f}s")
    
    if result_2.get("ghost_speed"):
        print("✅ Run 2: GHOST SPEED CONFIRMED! (Vacuum Processing Active)")
        print(f"⚡ Speedup Factor: {duration_1 / duration_2:.1f}x")
    else:
        print("❌ Run 2: Failed to activate Ghost Speed.")

if __name__ == "__main__":
    asyncio.run(run_test())
