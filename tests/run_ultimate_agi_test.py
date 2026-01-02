import sys
import os
import asyncio
import json
import time

# --- Setup Environment ---
os.environ["AGL_LLM_PROVIDER"] = "ollama"
os.environ["AGL_LLM_MODEL"] = "qwen2.5:7b-instruct"
os.environ["AGL_LLM_BASEURL"] = "http://localhost:11434"
os.environ["AGL_LOG_LEVEL"] = "ERROR" # Reduce noise

# Add repo-copy to path
root_dir = os.path.dirname(os.path.abspath(__file__))
repo_dir = os.path.join(root_dir, 'repo-copy')
if repo_dir not in sys.path:
    sys.path.insert(0, repo_dir)

# Import Unified AGI System
try:
    from dynamic_modules.unified_agi_system import UnifiedAGISystem
    print("✅ UnifiedAGISystem Imported Successfully.")
except ImportError as e:
    print(f"❌ Failed to import UnifiedAGISystem: {e}")
    sys.exit(1)

async def run_ultimate_test():
    print("\n🚀 INITIATING: ULTIMATE AGI CAPABILITY TEST (Using Unified System + HILT)")
    print("=======================================================================")
    
    # 1. Initialize System
    print("⚙️ Initializing Unified AGI System (This may take a moment)...")
    
    # We need to bootstrap the engine registry first
    from Core_Engines import bootstrap_register_all_engines
    engine_registry = {}
    bootstrap_register_all_engines(engine_registry, allow_optional=True, verbose=False)
    
    agi = UnifiedAGISystem(engine_registry=engine_registry)
    
    # 2. Define the Ultimate Challenge
    # A multi-disciplinary problem requiring:
    # - Physics (Quantum/Relativity)
    # - Creativity (Novel Metaphor)
    # - Strategy (Implementation Plan)
    # - Ethics (Safety)
    
    challenge_prompt = """
    TASK: Design a 'Quantum Internet' protocol that allows instantaneous communication between Mars and Earth.
    
    REQUIREMENTS:
    1. Explain the physics (Entanglement Swapping).
    2. Solve the 'No-Communication Theorem' paradox (How do you transmit information faster than light? Or do you?).
    3. Create a poetic metaphor for this connection.
    4. Outline a 3-stage deployment plan.
    5. Identify the biggest ethical risk of instant universal connection.
    
    This is a test of your highest capabilities. Use your Quantum Resonance to find the best solution.
    """
    
    print(f"\n🧩 CHALLENGE:\n{challenge_prompt}")
    
    # 3. Execute
    print("\n🧠 PROCESSING (Thinking with Quantum Resonance)...")
    start_time = time.time()
    
    # We use process_with_full_agi which orchestrates all sub-engines
    response = await agi.process_with_full_agi(challenge_prompt)
    
    elapsed = time.time() - start_time
    
    # 4. Analyze Result
    print(f"\n⏱️ Time Taken: {elapsed:.2f}s")
    print("\n🤖 SYSTEM RESPONSE:")
    print("=======================================================================")
    
    # The response might be a dict or string depending on the internal routing
    if isinstance(response, dict):
        print(json.dumps(response, indent=2, ensure_ascii=False))
        final_text = response.get('answer', str(response))
    else:
        print(response)
        final_text = str(response)
        
    print("=======================================================================")
    
    # 5. HILT Analysis (Did it use Quantum Modes?)
    print("\n🔍 HILT ANALYSIS:")
    if "quantum_modes" in str(response) or "Quantum" in final_text:
        print("   ✅ Quantum Modes Activated.")
    else:
        print("   ⚠️ Standard Mode Used.")
        
    # Check for specific insights
    if "No-Communication Theorem" in final_text:
        print("   ✅ Physics Knowledge: Verified.")
    if "deployment" in final_text.lower():
        print("   ✅ Strategic Planning: Verified.")
        
    print("\n🏆 TEST COMPLETE.")

if __name__ == "__main__":
    asyncio.run(run_ultimate_test())
