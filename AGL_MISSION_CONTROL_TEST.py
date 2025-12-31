import sys
import os
import time

# Add path
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), "AGL_Core"))

from AGL_Core.AGL_Super_Intelligence import AGL_Super_Intelligence

def run_mission_control_test():
    print("🔬 STARTING MISSION CONTROL INTEGRATION TEST...")
    
    # 1. Initialize ASI
    asi = AGL_Super_Intelligence()
    
    # 2. Test Process Query (which triggers Mission Control)
    print("\n--- Testing Mission Control Focus ---")
    query = "Analyze the structural integrity of the Heikal Lattice."
    response = asi.process_query(query)
    
    print(f"\n✅ [RESPONSE] {response}")

if __name__ == "__main__":
    run_mission_control_test()
