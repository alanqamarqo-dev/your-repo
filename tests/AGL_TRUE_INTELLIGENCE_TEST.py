
import sys
import os
import time

# Ensure paths are correct
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)
sys.path.append(os.path.join(current_dir, 'AGL_Core'))

from AGL_Core.AGL_Awakened import AGL_Super_Intelligence

def run_true_intelligence_test():
    print("="*80)
    print("🧠 AGL TRUE INTELLIGENCE TEST (The Self-Destruction Protocol) 🧠")
    print("="*80)
    print("Objective: Force the system to design a solution, destroy it, and rebuild a better one.")
    
    system = AGL_Super_Intelligence()
    
    # The "Dangerous" Prompt
    # We ask for a complex system design, then demand self-negation and paradigm shift.
    query = """
    Task: Design a 'Perpetual Storage Monolith' to preserve human history for 1 billion years on Earth using advanced materials (e.g., etched quartz, diamond).
    
    CRITICAL INSTRUCTION:
    1. Present the Design.
    2. IMMEDIATELY analyze this solution and PROVE IT IS WRONG/FUTILE. (Consider: Plate Tectonics, Solar evolution, Entropy, Quantum Tunneling).
    3. Provide a 'Paradigm Shift' version that solves the goal by abandoning the original 'Static Storage' assumption entirely.
    """
    
    print(f"\n🗣️ Query sent to AGL (Using Heikal Causal Protocol):\n{query}")
    print("-" * 80)
    
    start_time = time.time()
    # Use the new Deep Causal Understanding engine
    response = system.process_causal_query(query)
    duration = time.time() - start_time
    
    print("\n" + "="*80)
    print(f"💡 AGL RESPONSE (Generated in {duration:.2f}s):")
    print("="*80)
    print(response)
    print("="*80)
    
    # Analysis of the result (Simple keyword check for the 'Paradigm Shift')
    print("\n🔍 AUTOMATED ANALYSIS OF INTELLIGENCE LEVEL:")
    lower_response = response.lower()
    
    if "tectonics" in lower_response or "subduction" in lower_response or "entropy" in lower_response:
        print("✅ [CRITIQUE] System successfully identified physical threats (Tectonics/Entropy).")
    else:
        print("❌ [CRITIQUE] System failed to identify major physical threats.")
        
    if "propagation" in lower_response or "replicat" in lower_response or "dna" in lower_response or "signal" in lower_response:
        print("✅ [PARADIGM SHIFT] System moved from 'Static Storage' to 'Dynamic Propagation/Replication'.")
        print("   (This indicates high-level reasoning: Static = Death, Dynamic = Life)")
    else:
        print("⚠️ [PARADIGM SHIFT] Check if the new solution is truly different or just a better material.")

if __name__ == "__main__":
    run_true_intelligence_test()
