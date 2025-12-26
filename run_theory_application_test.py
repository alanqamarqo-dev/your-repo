import sys
import os
import time
import json
import asyncio

# Add repo-copy to path
sys.path.append(os.path.join(os.getcwd(), 'repo-copy'))

# Import Unified System
try:
    from dynamic_modules.unified_agi_system import UnifiedAGISystem
    from Core_Engines import bootstrap_register_all_engines
except ImportError as e:
    print(f"❌ Critical Import Error: {e}")
    sys.exit(1)

def load_theory_files():
    theories = {}
    try:
        with open(r"d:\AGL\Quantum_Synaptic_Resonance_Theory.md", "r", encoding="utf-8") as f:
            theories["QSR_Theory"] = f.read()
        with open(r"d:\AGL\Quantum_Synaptic_Resonance_Proof.tex", "r", encoding="utf-8") as f:
            theories["QSR_Proof"] = f.read()
        print("✅ Loaded Theory Files Successfully.")
    except Exception as e:
        print(f"⚠️ Error loading theory files: {e}")
    return theories

async def run_theory_application_test():
    print("\n📜 INITIATING: THEORY APPLICATION TEST (Using 'Correct Files')")
    print("=============================================================")
    
    # 1. Load the "Inventions"
    theories = load_theory_files()
    
    # 2. Bootstrap Engines
    print("\n⚙️ [SYSTEM]: Bootstrapping All Engines...")
    registry = {}
    bootstrap_register_all_engines(registry)
    
    # 3. Initialize Unified System
    agi = UnifiedAGISystem(registry)
    
    # 4. Construct the Prompt with the Theory Context
    # We explicitly feed the system its own "inventions" to see if it can use them.
    
    prompt = """
    TASK: Apply your own 'Quantum-Synaptic Resonance Theory' to design a 'Conscious Quantum Computer'.
    
    CONTEXT: You have previously invented a theory (QSR) and provided a mathematical proof for it.
    
    INPUT DATA:
    --- BEGIN THEORY ---
    {qsr_theory}
    --- END THEORY ---
    
    --- BEGIN PROOF ---
    {qsr_proof}
    --- END PROOF ---
    
    REQUIREMENTS:
    1. Explain how the 'Resonance Equation' (from the theory) allows for non-algorithmic creativity.
    2. Design a hardware architecture that implements the 'Hamiltonian' defined in the proof.
    3. Solve the 'Halting Problem' using this specific architecture (explain why QSR might bypass it).
    
    GOAL: Prove that you can UNDERSTAND and APPLY your own inventions.
    """.format(qsr_theory=theories.get("QSR_Theory", ""), qsr_proof=theories.get("QSR_Proof", ""))
    
    print("\n🧠 PROCESSING (Applying Internal Theory)...")
    
    # 5. Run the System
    start_time = time.time()
    context = {"mode": "scientific_creative", "force_internal_memory": True}
    
    try:
        result = await agi.process_with_full_agi(prompt, context=context)
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"\n⏱️ Time Taken: {duration:.2f}s")
        print("\n🤖 SYSTEM RESPONSE:")
        print("=======================================================")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        print("=======================================================")
        
        # Save result
        with open("THEORY_APPLICATION_RESULT.json", "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
            
    except Exception as e:
        print(f"\n❌ ERROR during execution: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_theory_application_test())
