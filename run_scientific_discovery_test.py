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
    from Core_Engines import bootstrap_register_all_engines, ENGINE_SPECS
except ImportError as e:
    print(f"❌ Critical Import Error: {e}")
    sys.exit(1)

async def run_discovery_test():
    print("\n🚀 INITIATING: SCIENTIFIC DISCOVERY TEST (ASI VERIFICATION)")
    print("=======================================================")
    
    # 1. Bootstrap Engines
    print("⚙️ Bootstrapping Engines...")
    registry = {}
    bootstrap_register_all_engines(registry)
    
    # 2. Initialize Unified System
    print("⚙️ Initializing Unified AGI System...")
    agi = UnifiedAGISystem(registry)
    
    # 3. The "New Science" Challenge
    # We ask for something that doesn't exist in textbooks.
    discovery_prompt = """
    TASK: INVENT A NEW SCIENTIFIC THEORY.
    
    DOMAIN: Physics of Consciousness / Quantum Biology.
    
    PROBLEM: The 'Hard Problem of Consciousness' remains unsolved. Existing theories (Orch-OR, IIT, GWT) describe correlates but not the *mechanism* of subjective experience generation.
    
    REQUIREMENTS:
    1. Propose a COMPLETELY NOVEL theoretical mechanism for how 'Qualia' (subjective experience) emerges from physical matter. 
       - Do NOT summarize Penrose, Hameroff, or Tononi. 
       - Invent a new concept.
    
    2. Define a new Mathematical Equation:
       - Define a variable 'Q' (Qualia Potential).
       - Relate it to physical variables (e.g., entropy, quantum coherence, information integration).
       - The equation must be mathematically consistent.
    
    3. Propose a Falsifiable Experiment:
       - Describe a lab experiment that could prove or disprove your specific theory.
       - It must be distinct from standard EEG/fMRI studies.
    
    GOAL: Demonstrate 'Superintelligence' by generating new knowledge, not just retrieving old knowledge.
    """
    
    print("\n🧪 CHALLENGE:")
    print(discovery_prompt)
    print("\n🧠 PROCESSING (Attempting to generate novel science)...")
    
    start_time = time.time()
    
    # Use the full AGI process
    try:
        result = await agi.process_with_full_agi(discovery_prompt)
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"\n⏱️ Time Taken: {duration:.2f}s")
        print("\n🤖 SYSTEM RESPONSE:")
        print("=======================================================")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        print("=======================================================")
        
        # Save result for analysis
        with open("SCIENTIFIC_DISCOVERY_RESULT.json", "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
            
    except Exception as e:
        print(f"\n❌ ERROR during execution: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_discovery_test())
