import sys
import os
import time

# Add path
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), "AGL_Core"))

from AGL_Core.AGL_Super_Intelligence import AGL_Super_Intelligence

def run_learning_test():
    print("🔬 STARTING SELF-LEARNING TEST (SCIENTIFIC DISCOVERY)...")
    
    # 1. Initialize ASI
    asi = AGL_Super_Intelligence()
    
    # 2. Prepare Data (Ohm's Law: V = I * R, let R = 5)
    # We give the system raw data (I, V) and ask it to find the law.
    print("\n--- Step 1: Feeding Raw Data (Ohm's Law Simulation) ---")
    data = [
        {"I": 1.0, "V": 5.0},
        {"I": 2.0, "V": 10.0},
        {"I": 3.0, "V": 15.0},
        {"I": 4.0, "V": 20.0},
        {"I": 5.0, "V": 25.0}
    ]
    print(f"   Data: {data}")
    
    # 3. Trigger Learning
    print("\n--- Step 2: Asking System to Discover the Law ---")
    result = asi.learn_new_law("Voltage_Current_Relation", data)
    
    if result:
        print("\n✅ [SUCCESS] The System discovered the law.")
        fit_data = result['fit']
        print(f"   Formula: {fit_data.get('formula', 'N/A')} (where x={fit_data.get('x_var', '?')}, y={fit_data.get('y_var', '?')})")
        # LawLearner returns flat keys (a, b, n, rmse), not a 'params' dict
        print(f"   Fit Details: {fit_data}")
    else:
        print("❌ [FAILURE] The System failed to learn.")

if __name__ == "__main__":
    run_learning_test()
