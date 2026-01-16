import os
import sys
import time
from pathlib import Path

# Add src to path
ag_src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.append(ag_src_path)

from agl.engines.web_search import WebSearchEngine
from agl.engines.holographic_llm import HolographicLLM

def run_deep_research():
    print("🔬 [AGL] Starting Deep Research & Synthesis Protocol...")
    
    # 1. Initialize Engines
    search_engine = WebSearchEngine()
    # Holographic LLM with specific seed for this research
    holo_llm = HolographicLLM(key_seed=999) 
    
    topic = "Latest breakthroughs in Quantum-Classical Hybrid ASI architectures Jan 2026"
    
    # 2. Search Phase
    print(f"\n📡 [Phase 1] Searching for: '{topic}'")
    search_results = search_engine.search(topic, num_results=3)
    
    if not search_results:
        print("⚠️ No internet results found. Using internal synthesis.")
        snippets = "Internal Knowledge: Quantum-Classical Hybrid systems are merging superconducting qubits with tensor cores."
    else:
        snippets = "\n".join([f"- {r['title']}: {r['snippet']}" for r in search_results])
    
    # 3. Synthesis Phase (Attempt 1 - Real LLM Call)
    print("\n🧠 [Phase 2] Synthesizing findings through Holographic LLM...")
    prompt = f"Based on the following search results, provide a concise summary of the state of Quantum-Classical Hybrid ASI in early 2026:\n\n{snippets}"
    
    messages = [
        {"role": "system", "content": "You are the AGL Synthesis Engine. Analyze technical data and provide insights."},
        {"role": "user", "content": prompt}
    ]
    
    start_t = time.time()
    synthesis = holo_llm.chat_llm(messages)
    duration = time.time() - start_t
    
    print("\n--- SYNTHESIS REPORT ---")
    print(synthesis)
    print(f"------------------------")
    print(f"Time Taken (Real Call): {duration:.2f}s")
    
    # 4. Instant Retrieval Test (Attempt 2 - Holographic Hit)
    print("\n⚡ [Phase 3] Testing Holographic Instant Retrieval (Zero-Latency Test)...")
    start_t = time.time()
    cached_synthesis = holo_llm.chat_llm(messages)
    duration_cached = time.time() - start_t
    
    print(f"Time Taken (Holographic): {duration_cached:.6f}s")
    
    if duration_cached < 0.1:
        print("✅ SUCCESS: Holographic retrieval verified (Instant).")
    else:
        print("❌ FAILURE: Retrieval was not instant.")

    # 5. Final Statistics
    print("\n📊 Final AGL Intelligence Stats:")
    print(json.dumps(holo_llm.get_statistics(), indent=4))

if __name__ == "__main__":
    import json
    run_deep_research()
