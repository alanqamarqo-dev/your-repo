import os
import sys
import asyncio
import time

# --- Setup Environment for Deep Thinking ---
os.environ["AGL_SELF_LEARNING_ENABLE"] = "1"
os.environ["AGL_LOG_LEVEL"] = "INFO"
os.environ["AGL_LLM_MODEL"] = "qwen2.5:7b-instruct"
# Ensure timeouts are high for this complex task
os.environ["AGL_HTTP_TIMEOUT"] = "1200" 
os.environ["AGL_OLLAMA_CLI_TIMEOUT"] = "1200"

# Ensure imports work
root_dir = os.path.dirname(os.path.abspath(__file__))
repo_dir = os.path.join(root_dir, 'repo-copy')
if repo_dir not in sys.path:
    sys.path.insert(0, repo_dir)

from dynamic_modules.mission_control_enhanced import EnhancedMissionController

async def run_unification_mission():
    print("\n🌌 [AGI] Starting Grand Challenge: Quantum-Relativity Unification")
    print("================================================================")
    
    # The Grand Challenge Prompt
    mission_prompt = """
    OBJECTIVE: Develop and Prove a Unified Theory of Quantum Gravity.
    
    PHASE 1: THEORETICAL FRAMEWORK
    - Propose a novel or synthesized theoretical framework that reconciles the smooth spacetime of General Relativity with the discrete probabilistic nature of Quantum Mechanics.
    - Define the fundamental axioms of this theory.
    
    PHASE 2: MATHEMATICAL PROOF
    - Derive the core field equations of this unified theory.
    - Show mathematically how these equations reduce to Einstein's Field Equations at macroscopic scales and Schrödinger/Dirac equations at microscopic scales.
    - Provide a formal proof for a specific prediction (e.g., Hawking Radiation modification, Graviton interaction).
    
    PHASE 3: COMPUTATIONAL SIMULATION
    - Write a complete, executable Python simulation to model a phenomenon predicted by your theory (e.g., Spacetime foam dynamics, Quantum tunneling through an Event Horizon).
    - The code must be self-contained, use numpy/scipy, and produce numerical data or ASCII visualization.
    
    PHASE 4: EXECUTION & ANALYSIS
    - Execute the generated simulation code.
    - Analyze the output data to validate the consistency of the theory.
    """

    # Initialize Controller
    controller = EnhancedMissionController()
    
    print(f"📝 Task: {mission_prompt.strip().splitlines()[0]}...")
    
    # Execute Mission
    start_time = time.time()
    
    # We use the 'scientific_cluster' as it contains the Math Brain, Quantum Processor, and Hypothesis Generator
    result = await controller.orchestrate_cluster(
        cluster_key="scientific_cluster",
        task_input=mission_prompt,
        metadata={
            "priority": "critical",
            "complexity": "extreme",
            "domain": "theoretical_physics",
            "requires_simulation": True
        }
    )
    
    end_time = time.time()
    duration = end_time - start_time
    
    print("\n==================================================")
    print(f"✅ Mission Completed in {duration:.2f} seconds")
    print("==================================================")
    
    # Safe extraction of keys
    print("\n🔍 Result Keys:", list(result.keys()))
    
    if "cluster_result" in result:
        cr = result["cluster_result"]
        print("🔍 Cluster Result Keys:", list(cr.keys()))
        
        # Try to find the raw reasoning or code
        if "reasoning_trace" in cr:
            print("\n🧠 Reasoning Trace Found!")
            with open("REASONING_TRACE.txt", "w", encoding="utf-8") as f:
                f.write(str(cr["reasoning_trace"]))
                
        if "generated_code" in cr:
             print("\n💻 Generated Code Found!")
             with open("GENERATED_SIMULATION.py", "w", encoding="utf-8") as f:
                f.write(str(cr["generated_code"]))
        
        if "math_result" in cr:
            print("\n📐 Math Result Found!")
            math_content = str(cr["math_result"])
            print(math_content)
            with open("MATH_DERIVATION.md", "w", encoding="utf-8") as f:
                f.write(math_content)

    # Extract output using correct keys
    final_text = result.get("focused_output") or result.get("llm_summary") or result.get("final_output") or str(result)
    
    print("\n📄 FINAL REPORT:\n")
    print(final_text)
    
    # Save the result to a file
    with open("QUANTUM_RELATIVITY_UNIFICATION_REPORT.md", "w", encoding="utf-8") as f:
        f.write(f"# Quantum-Relativity Unification Report\n\n")
        f.write(f"**Date:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Duration:** {duration:.2f}s\n\n")
        f.write(final_text)

if __name__ == "__main__":
    asyncio.run(run_unification_mission())
