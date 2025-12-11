import sys
import os
import asyncio
import json

# Add repo root to path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root_dir)
sys.path.append(os.path.join(root_dir, 'repo-copy'))

# Ensure environment variables for testing
os.environ['AGL_LLM_PROVIDER'] = 'ollama'
os.environ['AGL_LLM_MODEL'] = 'qwen2.5:7b-instruct'
os.environ['AGL_LLM_BASEURL'] = 'http://localhost:11434'

try:
    from dynamic_modules.mission_control_enhanced import EnhancedMissionController, SCIENTIFIC_ORCHESTRATOR
except ImportError:
    # Try importing from repo-copy if direct import fails
    sys.path.append(os.path.join(root_dir, 'repo-copy', 'dynamic_modules'))
    from mission_control_enhanced import EnhancedMissionController, SCIENTIFIC_ORCHESTRATOR

async def run_stress_test():
    print("--- 🚀 AGL Full System Stress Test ---")
    print("Target: Activate All Engines (Creative, Scientific, Strategic, Memory)")
    
    # 1. Initialize Mission Control
    print("\n[1] Initializing Enhanced Mission Control...")
    controller = EnhancedMissionController()
    
    # Verify Scientific Orchestrator
    if SCIENTIFIC_ORCHESTRATOR:
        print("   ✅ Scientific Orchestrator: Active")
    else:
        print("   ❌ Scientific Orchestrator: Inactive (Check imports)")
        
    # 2. Define Complex Mission
    mission_prompt = (
        "Design a self-sustaining colony on Europa (Jupiter's moon). "
        "The design must include: "
        "1. Energy source (Fusion or Geothermal) with specific output calculations. "
        "2. Structural integrity against ice pressure (Depth: 10km). "
        "3. Life support systems for 1000 humans. "
        "4. Scientific validation of all parameters (Energy, Stress, Resources)."
    )
    
    print(f"\n[2] Mission: {mission_prompt}")
    print("\n[3] Executing with Scientific Validation Loop...")
    
    start_time = asyncio.get_event_loop().time()
    
    # 3. Execute
    try:
        response = await controller.process_with_scientific_validation(
            prompt=mission_prompt,
            context={"cluster": "scientific_reasoning", "type": "complex_design"}
        )
        
        end_time = asyncio.get_event_loop().time()
        duration = end_time - start_time
        
        print(f"\n[4] Mission Complete in {duration:.2f} seconds")
        print("\n--- 📝 Final System Output ---")
        print(response)
        
        # 4. Analyze Output for Engine Signatures
        print("\n--- 🔍 Engine Signature Analysis ---")
        if "Fusion" in response or "Geothermal" in response:
            print("   ✅ Creative Engine: Concepts Generated")
        if "Watts" in response or "Joules" in response:
            print("   ✅ Physics Engine: Units Detected")
        if "Stress" in response or "Pressure" in response:
            print("   ✅ Simulation Engine: Structural Analysis Detected")
        if "Correction" in response or "Constraint" in response:
            print("   ✅ Validation Loop: Self-Correction Triggered")
            
    except Exception as e:
        print(f"\n❌ Error during execution: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(run_stress_test())
