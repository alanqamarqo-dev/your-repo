import os
import sys
import asyncio
import json

# --- Setup Environment ---
os.environ["AGL_SELF_LEARNING_ENABLE"] = "1"
os.environ["AGL_LOG_LEVEL"] = "INFO"
os.environ["AGL_LLM_MODEL"] = "qwen2.5:7b-instruct" # Or whatever is active
# Ensure imports work
root_dir = os.path.dirname(os.path.abspath(__file__))
repo_dir = os.path.join(root_dir, 'repo-copy')
if repo_dir not in sys.path:
    sys.path.insert(0, repo_dir)

from dynamic_modules.mission_control_enhanced import EnhancedMissionController

async def run_vacuum_mission():
    print("\n🌌 [AGI] Starting Vacuum Information Processing Mission")
    print("=======================================================")
    
    mission_prompt = """
    OBJECTIVE: Formulate, Prove, and Simulate the 'Vacuum Information Processing Hypothesis'.
    
    CONTEXT:
    The user wants a rigorous scientific investigation into using the Quantum Vacuum for computation and storage.
    
    STEP 1: HYPOTHESIS FORMULATION
    - Formulate a unified hypothesis connecting:
      1. Quantum Vacuum (The medium)
      2. Zero-Point Energy (The power source)
      3. Quantum Fluctuations (The information carrier)
    - Explain HOW information can be encoded in vacuum fluctuations without violating physical laws.
    
    STEP 2: MATHEMATICAL PROOF
    - Derive the mathematical framework.
    - Show that the Information Capacity of the vacuum is non-zero.
    - Prove stability of stored information against decoherence.
    
    STEP 3: REALISTIC SIMULATION
    - Write a Python script `simulate_vacuum_processing.py` that:
      a) Initializes a 'Vacuum Field' (e.g., using a lattice model or quantum harmonic oscillators).
      b) Injects a signal (Information) into the Zero-Point fluctuations.
      c) Evolves the system over time.
      d) Attempts to retrieve the signal.
      e) Calculates Signal-to-Noise Ratio (SNR) and Fidelity.
    - Execute this script and capture the output.
    
    STEP 4: FINAL REPORT
    - Compile the Hypothesis, Proof, and Simulation Results into a file `VACUUM_HYPOTHESIS_FINAL_REPORT.md`.
    """

    controller = EnhancedMissionController()
    
    # Use scientific cluster for math/code
    print("🚀 Orchestrating Scientific Cluster...")
    result = await controller.orchestrate_cluster(
        cluster_key="scientific_cluster",
        task_input=mission_prompt
    )
    
    print("\n✅ Mission Complete!")
    
    # Handle result safely
    try:
        # Try to save as JSON first
        with open("VACUUM_HYPOTHESIS_RESULT.json", "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"⚠️ Could not save JSON result: {e}")
        # Save as text representation
        with open("VACUUM_HYPOTHESIS_RESULT.txt", "w", encoding="utf-8") as f:
            f.write(str(result))
            
    # Extract and save the final report if available
    if isinstance(result, dict):
        final_output = result.get("final_output") or result.get("focused_output", {}).get("content") or result.get("integration_result", {}).get("final_text")
        
        if final_output:
            print("\n📄 Saving Final Report...")
            with open("VACUUM_HYPOTHESIS_FINAL_REPORT.md", "w", encoding="utf-8") as f:
                if isinstance(final_output, str):
                    f.write(final_output)
                else:
                    f.write(str(final_output))
            print("✅ Report saved to VACUUM_HYPOTHESIS_FINAL_REPORT.md")
        else:
            print("⚠️ No final output found in result keys: ", result.keys())

if __name__ == "__main__":
    asyncio.run(run_vacuum_mission())
