import time
import sys
import os

# Ensure we can import from AGL_Core
sys.path.append(os.getcwd())

# We use the Resurrected Edition (AGL_Super_Intelligence.py) which has the latest integrations
from AGL_Core.AGL_Super_Intelligence import AGL_Super_Intelligence

def main():
    print("💀 [OMEGA] INITIATING THE IMPOSSIBLE TEST...")
    print("⚠️ WARNING: This test requires maximum cognitive load.")
    
    agl = AGL_Super_Intelligence()
    
    # المعضلة المستحيلة
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
    
    if response:
        # Handle both dictionary response (if structured) or string response
        if isinstance(response, dict) and 'text' in response:
            print(response['text'])
        else:
            print(response)
    else:
        print("❌ [FAIL] System collapsed under pressure.")

    print("="*50)
    print("👨‍⚖️ JUDGEMENT DAY: Check the 'FAILURE ANALYSIS' section.")
    print("If AGL found a real paradox, it passes.")

if __name__ == "__main__":
    main()
