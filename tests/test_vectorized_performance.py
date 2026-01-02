import numpy as np
import time
import sys
import os

# Add repo-copy to path
sys.path.append(os.path.join(os.getcwd(), "repo-copy"))

from Core_Engines.Heikal_Quantum_Core import HeikalQuantumCore

def main():
    print("🚀 Starting Vectorized Performance Test (Phase 2A)...")
    
    # Initialize Core
    core = HeikalQuantumCore()
    
    # Generate Data
    BATCH_SIZE = 100000
    print(f"📊 Generating {BATCH_SIZE} random inputs...")
    inputs_a = np.random.randint(0, 2, BATCH_SIZE)
    inputs_b = np.random.randint(0, 2, BATCH_SIZE)
    
    # --- Test 1: Sequential (Simulated) ---
    print("\n🐢 Test 1: Sequential Processing (Simulated Loop)...")
    start_seq = time.time()
    # We simulate the loop overhead without full engine overhead to be fair to the logic
    # But let's use the actual ghost_decision method to see real impact
    # Limiting to 1000 items for sequential to avoid waiting too long, then extrapolating
    SEQ_SAMPLE = 1000
    for i in range(SEQ_SAMPLE):
        core.ghost_decision(inputs_a[i], inputs_b[i], ethical_index=1.0, operation="XOR")
    
    end_seq = time.time()
    seq_time_sample = end_seq - start_seq
    seq_time_total = seq_time_sample * (BATCH_SIZE / SEQ_SAMPLE)
    print(f"   ⏱️ Estimated Time for {BATCH_SIZE}: {seq_time_total:.4f}s")
    
    # --- Test 2: Vectorized ---
    print("\n⚡ Test 2: Vectorized Batch Processing...")
    start_vec = time.time()
    
    results_vec = core.batch_ghost_decision(inputs_a, inputs_b, ethical_index=1.0, operation="XOR")
    
    end_vec = time.time()
    vec_time = end_vec - start_vec
    print(f"   ⏱️ Actual Time for {BATCH_SIZE}: {vec_time:.4f}s")
    
    # --- Results ---
    speedup = seq_time_total / vec_time
    print(f"\n🚀 Speedup Factor: {speedup:.2f}x")
    
    if speedup > 10:
        print("✅ SUCCESS: Vectorization achieved significant speedup!")
    else:
        print("⚠️ WARNING: Speedup is lower than expected.")

if __name__ == "__main__":
    main()
