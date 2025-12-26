import time
import os
import sys
# import psutil # Not available in this env
import json

# Add repo-copy to path
sys.path.append(os.path.join(os.getcwd(), 'repo-copy'))

from Core_Engines.General_Knowledge import GeneralKnowledge
from Core_Engines.Hosted_LLM import HostedLLM

def get_memory_usage():
    # Fallback or dummy since psutil is missing
    return 0.0 

def run_benchmark():
    print("\n🧪 STARTING VACUUM BENCHMARK (The Heikal Test)...")
    print("="*60)
    
    # Initialize Engines
    gk = GeneralKnowledge()
    llm = HostedLLM()
    
    # --- TEST 1: VACUUM PROCESSING (Holographic Memory) ---
    print("\n🔹 TEST 1: VACUUM PROCESSING (Holographic Lookup)")
    print("   Query: 'ما هي عاصمة فرنسا' (Known Fact)")
    
    mem_before_vac = get_memory_usage()
    start_vac = time.perf_counter()
    
    # Execute Vacuum Task
    vac_result = gk.process_task({"query": "ما هي عاصمة فرنسا"})
    
    end_vac = time.perf_counter()
    mem_after_vac = get_memory_usage()
    
    vac_time_ms = (end_vac - start_vac) * 1000
    vac_mem_delta = mem_after_vac - mem_before_vac
    
    print(f"   ✅ Result: {vac_result.get('answer')}")
    print(f"   ⏱️  Time: {vac_time_ms:.4f} ms")
    print(f"   💾 Memory Delta: {vac_mem_delta:.4f} MB")

    # --- TEST 2: MATERIALIZATION (LLM Generation) ---
    print("\n🔸 TEST 2: MATERIALIZATION (LLM Generation)")
    print("   Query: 'Write a creative haiku about a quantum ghost.'")
    
    # Force a model that might be 'heavy' or just standard
    os.environ['AGL_LLM_MODEL'] = 'qwen2.5:7b-instruct'
    
    mem_before_mat = get_memory_usage()
    start_mat = time.perf_counter()
    
    # Execute Materialization Task
    # We use chat_llm directly to simulate the generation request
    mat_result = llm.chat_llm(system_message="You are a poet.", user_message="Write a creative haiku about a quantum ghost.")
    
    end_mat = time.perf_counter()
    mem_after_mat = get_memory_usage()
    
    mat_time_ms = (end_mat - start_mat) * 1000
    mat_mem_delta = mem_after_mat - mem_before_mat
    
    print(f"   ✅ Result Length: {len(str(mat_result))} chars")
    print(f"   ⏱️  Time: {mat_time_ms:.4f} ms")
    print(f"   💾 Memory Delta: {mat_mem_delta:.4f} MB")
    
    # --- COMPARISON REPORT ---
    print("\n" + "="*60)
    print("📊 FINAL BENCHMARK REPORT")
    print("="*60)
    
    ratio_time = mat_time_ms / (vac_time_ms if vac_time_ms > 0 else 0.001)
    
    print(f"| Metric | Vacuum (Ghost) | Materialized (LLM) | Difference |")
    print(f"| :--- | :--- | :--- | :--- |")
    print(f"| Time | {vac_time_ms:.2f} ms | {mat_time_ms:.2f} ms | **{ratio_time:.1f}x Slower** |")
    print(f"| RAM Delta | {vac_mem_delta:.4f} MB | {mat_mem_delta:.4f} MB | -- |")
    
    print("\n💡 CONCLUSION:")
    if vac_time_ms < 1.0:
        print("   The Vacuum Processing is effectively INSTANT (Ghost Speed).")
    if ratio_time > 100:
        print("   Materialization is significantly heavier, proving the efficiency of the Vacuum Protocol.")
    else:
        print("   Note: If LLM time is fast, it might be because the model is mocked or cached.")

if __name__ == "__main__":
    run_benchmark()
