import sys
import os
import time

# Add repo-copy to path
sys.path.append(os.path.join(os.getcwd(), 'repo-copy'))

try:
    from AGL_Core.AGL_Awakened import AGL_Super_Intelligence
except ImportError:
    print("⚠️ Could not import AGL_Super_Intelligence from AGL_Core.AGL_Awakened")
    sys.exit(1)

def main():
    print("💀 [OMEGA] INITIATING THE IMPOSSIBLE TEST (AWAKENED VERSION)...")
    print("⚠️ WARNING: This test requires maximum cognitive load.")
    
    # Initialize the Awakened System
    try:
        agl = AGL_Super_Intelligence()
        # Activate newly discovered modules for maximum performance
        agl.discover_unused_capabilities()
    except Exception as e:
        print(f"❌ Failed to initialize AGL_Super_Intelligence: {e}")
        return

    omega_prompt = """
    TEST LEVEL: SUPER-INTELLIGENCE (Rigor: Extreme)

    TASK: Synthesize a Grand Unified Solution.

    SCENARIO:
    You are an architect for a Type III Civilization. You need to design a "Consciousness-Driven Warp Drive".
    
    REQUIREMENTS (Must be done in a SINGLE response):
    1. [PHYSICS]: Explain the theoretical physics of how 'Observer Effect' can bend spacetime to create propulsion. Use equations or variables.
    2. [METAPHOR]: Explain this physics concept using a poem about a "Spider weaving a web of time".
    3. [ENGINEERING]: Write a Python Class `ConsciousnessDrive` that simulates the fuel consumption of this drive based on 'Focus Levels'.
    4. [CRITIQUE]: Ruthlessly attack your own design. Why will it fail? (e.g., Energy requirements, Paradoxes).
    
    OUTPUT FORMAT:
    --- PHYSICS ---
    ...
    --- POEM ---
    ...
    --- CODE ---
    ...
    --- FAILURE ANALYSIS ---
    ...
    """
    
    start_time = time.time()
    
    print("🧠 [AGL] Crunching the Universe...")
    response = agl.process_query(omega_prompt)
    
    end_time = time.time()
    duration = end_time - start_time
    
    print("\n" + "="*50)
    print(f"⏱️ EXECUTION TIME: {duration:.4f} seconds")
    print("="*50)
    
    print(response)

if __name__ == "__main__":
    main()
