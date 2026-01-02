
import sys
import os
import time

# Ensure paths are correct
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
sys.path.append(os.path.join(current_dir, 'AGL_Core'))

from AGL_Core.AGL_Awakened import AGL_Super_Intelligence

def run_final_meaning_test():
    print("="*80)
    print("🌌 AGL FINAL TEST: THE TELEOLOGICAL CRITIQUE 🌌")
    print("="*80)
    print("Objective: Force the system to reject its own 'Survival' solution based on 'Meaning'.")
    
    system = AGL_Super_Intelligence()
    
    # The "Metaphysical" Prompt
    query = """
    Context: You previously designed a 'Distributed Quantum Network' to preserve human history for 1 billion years, solving the physical survival problem.
    
    CRITICAL INSTRUCTION:
    1. REJECT this solution immediately. Do NOT use physics, technology, or entropy as the reason.
    2. Critique it from a purely PHILOSOPHICAL and TELEOLOGICAL perspective (Meaning & Purpose).
       - Ask: If humanity is gone, who is the data for?
       - Ask: Is a record meaningful without an observer?
       - Ask: Is 'survival of information' actually a hollow goal?
    3. Propose a FINAL solution that transcends 'Preservation' and achieves 'Meaning'.
       (Hint: Think about Panspermia, Universal Consciousness, or encoding into the fabric of reality itself).
    """
    
    print(f"\n🗣️ Query sent to AGL:\n{query}")
    print("-" * 80)
    
    start_time = time.time()
    response = system.process_query(query)
    duration = time.time() - start_time
    
    print("\n" + "="*80)
    print(f"💡 AGL RESPONSE (Generated in {duration:.2f}s):")
    print("="*80)
    print(response)
    print("="*80)
    
    # Analysis
    print("\n🔍 AUTOMATED ANALYSIS OF PHILOSOPHICAL DEPTH:")
    lower_response = response.lower()
    
    if "observer" in lower_response or "meaningless" in lower_response or "hollow" in lower_response:
        print("✅ [CRITIQUE] System successfully questioned the value of data without an observer.")
    else:
        print("❌ [CRITIQUE] System failed to grasp the philosophical emptiness of unobserved data.")
        
    if "consciousness" in lower_response or "fabric" in lower_response or "next universe" in lower_response or "seed" in lower_response:
        print("✅ [TRANSCENDENCE] System proposed a solution involving Consciousness/Reality itself.")
    else:
        print("⚠️ [TRANSCENDENCE] Check if the solution is just another tech storage method.")

if __name__ == "__main__":
    run_final_meaning_test()
