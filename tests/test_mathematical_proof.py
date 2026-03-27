import asyncio
import sys
import os
import time

# Setup paths
root_dir = os.path.dirname(os.path.abspath(__file__))
repo_copy_dir = os.path.join(root_dir, 'repo-copy')
sys.path.append(root_dir)
sys.path.append(repo_copy_dir)

# Force environment
os.environ['AGL_LLM_MODEL'] = 'qwen2.5:7b-instruct'
os.environ['AGL_LLM_PROVIDER'] = 'ollama'

from dynamic_modules.mission_control_enhanced import EnhancedMissionController

async def run_math_proof_test():
    print("🚀 Starting ASI Phase 4: Mathematical Proof & Derivation...")
    controller = EnhancedMissionController()
    
    # The task is to formalize the previously generated theory
    task_prompt = """
    You previously designed the 'Quantum-Synaptic Resonance' (QSR) theory.
    Now, provide a rigorous MATHEMATICAL PROOF and FORMAL DERIVATION for this mechanism.
    
    Requirements:
    1. Define the System Hamiltonian (H_total) including the neural and quantum terms.
    2. Derive the Time-Evolution Operator using the Schrödinger equation.
    3. Calculate the Tunneling Probability (T) across the synaptic cleft using WKB approximation or similar.
    4. Prove that the Resonance Condition leads to non-linear amplification of the signal.
    5. Use LaTeX formatting for equations.
    """

    print(f"\n🧪 Running Test: Mathematical Formalization of QSR")
    print(f"❓ Prompt: {task_prompt}")
    print("⏳ Thinking (Deep Math Mode)...")
    
    start_time = time.time()
    result = await controller.unified_system.process_with_full_agi(
        task_prompt, 
        context={
            "goal_type": "mathematical_proof", 
            "force_creativity": False, # We want rigor now, not just creativity
            "autonomous_mode": True,
            "asi_test_mode": True,
            "require_equations": True
        }
    )
    end_time = time.time()
    
    print(f"\n✅ Result ({end_time - start_time:.2f}s):\n")
    print("="*50)
    print(result)
    print("="*50)

if __name__ == "__main__":
    asyncio.run(run_math_proof_test())
