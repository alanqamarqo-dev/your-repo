import sys
import os
import time

# Add paths
sys.path.append(os.path.join(os.getcwd(), 'AGL_Core'))
sys.path.append(os.path.join(os.getcwd(), 'repo-copy'))

from AGL_Core.AGL_Awakened import AGL_Super_Intelligence

def run_demo():
    print("🚀 INITIATING AGL FULL POWER DEMONSTRATION")
    print("==========================================")
    
    asi = AGL_Super_Intelligence()
    
    # Complex Query to trigger all engines
    query = "Design a quantum algorithm to optimize global energy distribution while adhering to ethical constraints. Also calculate the eigenvalues of the energy matrix."
    
    print(f"\n🗣️ USER QUERY: {query}")
    print("------------------------------------------")
    
    response = asi.process_query(query)
    
    print(f"\n💡 FULL SYSTEM RESPONSE:\n{response}")
    
    # Check Volition
    print("\n⚡ CHECKING VOLITION STATE...")
    goal = asi.autonomous_tick()
    if goal:
        print(f"   -> Volition Generated Goal: {goal}")
    else:
        print("   -> Volition is observing.")
        
    # Dreaming
    print("\n🌙 ENTERING DREAMING CYCLE (Memory Consolidation)...")
    asi.sleep_mode()
    
    print("\n✅ DEMONSTRATION COMPLETE. SYSTEM IS FULLY OPERATIONAL.")

if __name__ == "__main__":
    run_demo()
