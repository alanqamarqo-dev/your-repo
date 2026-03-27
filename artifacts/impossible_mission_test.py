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
    from dynamic_modules.mission_control_enhanced import EnhancedMissionController
except ImportError:
    sys.path.append(os.path.join(root_dir, 'repo-copy', 'dynamic_modules'))
    from mission_control_enhanced import EnhancedMissionController

async def run_impossible_mission():
    print("--- 🌌 AGL IMPOSSIBLE MISSION: SCIENTIFIC SIMULATION ---")
    print("Objective: Use the full Mission Control to simulate and prove impossible questions.")
    
    controller = EnhancedMissionController()
    
    missions = [
        {
            "name": "🕵️ Dark Matter Detection",
            "prompt": """
            Perform a scientific simulation to detect Dark Matter WIMPs.
            Parameters:
            - Detector: 1000 kg Xenon
            - Cross-section: 1e-47 cm^2
            - Exposure: 5 years
            - Background: 0.001 events/kg/year
            
            Provide a mathematical proof of the detection probability.
            """
        },
        {
            "name": "⏳ Arrow of Time (Entropy)",
            "prompt": """
            Simulate the Arrow of Time using a particle box model to demonstrate entropy increase.
            System: 500 particles.
            Steps: 2000.
            
            Prove the Second Law of Thermodynamics using this simulation.
            """
        }
    ]
    
    results = {}
    
    for mission in missions:
        print(f"\n\n>>> INITIATING MISSION: {mission['name']}")
        print(f"    Prompt: {mission['prompt'].strip()[:100]}...")
        
        try:
            # Use process_with_scientific_validation which now includes pre-simulation
            result = await controller.process_with_scientific_validation(
                prompt=mission['prompt'],
                context={"cluster": "scientific_reasoning"}
            )
            
            print(f"\n[Mission Output]\n{result}")
            
            if "Simulation Report" in result:
                results[mission['name']] = "✅ Success (Simulation Data Found)"
            else:
                results[mission['name']] = "⚠️ Warning (No Simulation Data)"
                
        except Exception as e:
            print(f"    ❌ FAILED: {e}")
            results[mission['name']] = f"❌ Error: {e}"

    print("\n\n--- 🏆 IMPOSSIBLE MISSION REPORT ---")
    for name, status in results.items():
        print(f"{name}: {status}")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(run_impossible_mission())
