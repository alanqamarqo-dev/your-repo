import numpy as np
import time
import sys
import os
import multiprocessing

# Add repo-copy to path
sys.path.append(os.path.join(os.getcwd(), "repo-copy"))

from Core_Engines.Heikal_Quantum_Core import HeikalQuantumCore

def main():
    print("🚀 Starting Parallel Performance Test (Phase 2B)...")
    
    # Initialize Core
    core = HeikalQuantumCore()
    
    # Generate HUGE Data for Parallel Test
    # We need enough data to justify process overhead
    BATCH_SIZE = 10_000_000 # 10 Million operations
    print(f"📊 Generating {BATCH_SIZE} random inputs (Huge Batch)...")
    inputs_a = np.random.randint(0, 2, BATCH_SIZE)
    inputs_b = np.random.randint(0, 2, BATCH_SIZE)
    
    # --- Test 1: Vectorized (Single Core) ---
    # We force single core by calling wave_processor directly or using a smaller batch
    # But here we want to compare on the SAME large batch.
    # We can temporarily disable parallel executor to test single core speed on this batch
    print("\n⚡ Test 1: Single Core Vectorized (Main Process)...")
    
    start_single = time.time()
    # Direct call to wave processor to bypass parallel routing logic for test
    if core.wave_processor:
        res_single = core.wave_processor.wave_xor_vectorized(inputs_a, inputs_b)
    else:
        print("Error: Wave processor missing")
        return
        
    end_single = time.time()
    single_time = end_single - start_single
    print(f"   ⏱️ Single Core Time: {single_time:.4f}s")
    
    # --- Test 2: Multi-Core Parallel ---
    print(f"\n🚀 Test 2: Multi-Core Parallel ({multiprocessing.cpu_count()} Cores)...")
    start_multi = time.time()
    
    # This will trigger the routing logic in batch_ghost_decision because size > 500k
    res_multi = core.batch_ghost_decision(inputs_a, inputs_b, ethical_index=1.0, operation="XOR")
    
    end_multi = time.time()
    multi_time = end_multi - start_multi
    print(f"   ⏱️ Multi-Core Time: {multi_time:.4f}s")
    
    # --- Results ---
    speedup = single_time / multi_time
    print(f"\n🚀 Parallel Speedup Factor: {speedup:.2f}x")
    
    # Verification
    if np.array_equal(res_single, res_multi):
        print("✅ Verification: Results Match Exactly.")
    else:
        print("❌ Verification: Results Do Not Match!")

if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
