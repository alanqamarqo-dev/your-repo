import os
import sys
import asyncio
import time
import json

# --- Setup Environment for Deep Reasoning ---
os.environ["AGL_SELF_LEARNING_ENABLE"] = "1"
os.environ["AGL_LOG_LEVEL"] = "INFO"
os.environ["AGL_LLM_MODEL"] = "qwen2.5:7b-instruct"
os.environ["AGL_HTTP_TIMEOUT"] = "1200"
os.environ["AGL_OLLAMA_CLI_TIMEOUT"] = "1200"

# Ensure imports work
root_dir = os.path.dirname(os.path.abspath(__file__))
repo_dir = os.path.join(root_dir, 'repo-copy')
if repo_dir not in sys.path:
    sys.path.insert(0, repo_dir)

from dynamic_modules.mission_control_enhanced import EnhancedMissionController

async def run_proof_mission():
    print("\n🧪 [AGI] Starting Rigorous Proof & Stress Test Mission")
    print("=======================================================")
    
    # The Proof & Test Prompt
    mission_prompt = """
    OBJECTIVE: Rigorously PROVE and STRESS-TEST the 'Hybrid Quantum-Gravity Equation' derived previously.
    
    THEORY RECAP:
    Equation: [ i*hbar * d/dt + H_GR + V_QM - Psi, G_AB ] = 0
    
    TASK 1: SYMBOLIC VERIFICATION (Python/SymPy)
    - Write a Python script using 'sympy' to define the terms symbolically.
    - Implement a function `check_classical_limit()` that takes the limit as hbar -> 0 and verifies the quantum term vanishes.
    - Implement a function `check_flat_space_limit()` that sets metric G_AB to Minkowski metric and checks if it reduces to Schrödinger form.
    
    TASK 2: NUMERICAL STRESS TEST (Python/NumPy)
    - Simulate a particle wavepacket approaching an Event Horizon at r = 2M.
    - Classical Prediction: Wavepacket gets stuck/frozen at horizon.
    - Hybrid Theory Prediction: Wavepacket tunnels through due to lattice discreteness.
    - Write a simulation to calculate the 'Tunneling Probability' vs 'Lattice Spacing'.
    
    TASK 3: EXECUTION & ANALYSIS
    - Execute the verification and simulation scripts.
    - Output the results: Did the limits hold? What is the tunneling probability?
    """

    # Initialize Controller
    controller = EnhancedMissionController()
    
    print(f"📝 Task: Verifying Hybrid Quantum-Gravity Theory...")
    
    # Execute Mission
    start_time = time.time()
    
    # Use scientific cluster for math/code
    result = await controller.orchestrate_cluster(
        cluster_key="scientific_cluster",
        task_input=mission_prompt,
        metadata={
            "priority": "critical",
            "complexity": "extreme",
            "domain": "mathematical_physics",
            "requires_code_execution": True
        }
    )
    
    end_time = time.time()
    duration = end_time - start_time
    
    print("\n==================================================")
    print(f"✅ Proof Mission Completed in {duration:.2f} seconds")
    print("==================================================")
    
    # Safe extraction of keys
    print("\n🔍 Result Keys:", list(result.keys()))
    
    if "cluster_result" in result:
        cr = result["cluster_result"]
        print("🔍 Cluster Result Keys:", list(cr.keys()))
        
        # Save generated code if available
        if "generated_code" in cr:
             print("\n💻 Generated Verification Code Found!")
             with open("THEORY_VERIFICATION_CODE.py", "w", encoding="utf-8") as f:
                f.write(str(cr["generated_code"]))
        
        # Save reasoning
        if "reasoning_trace" in cr:
            with open("PROOF_REASONING.txt", "w", encoding="utf-8") as f:
                f.write(str(cr["reasoning_trace"]))

    # Extract output
    final_text = result.get("focused_output") or result.get("llm_summary") or result.get("final_output") or str(result)
    
    print("\n📄 FINAL PROOF REPORT:\n")
    print(final_text)
    
    # Save the result to a file
    with open("THEORY_PROOF_RESULTS.md", "w", encoding="utf-8") as f:
        f.write(f"# Theory Proof & Stress Test Results\n\n")
        f.write(f"**Date:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Duration:** {duration:.2f}s\n\n")
        f.write(final_text)

if __name__ == "__main__":
    asyncio.run(run_proof_mission())
