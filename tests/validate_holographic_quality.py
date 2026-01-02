import asyncio
import time
import sys
import os
import json
from difflib import SequenceMatcher

# Add repo-copy to path
sys.path.append(os.path.join(os.getcwd(), "repo-copy"))

from Core_Engines.Holographic_LLM import HolographicLLM
import Core_Engines.Hosted_LLM as HostedLLM

async def validate_quality():
    print("🔍 HOLOGRAPHIC QUALITY VALIDATION HARNESS")
    print("=========================================")
    
    # Initialize Engines
    holographic = HolographicLLM()
    # live_llm = HostedLLM() # HostedLLM is a module now
    
    test_prompts = [
        {
            "category": "Code",
            "prompt": "Write a Python function to calculate the Fibonacci sequence recursively."
        },
        {
            "category": "Reasoning",
            "prompt": "Explain the concept of Quantum Entanglement to a 5-year-old."
        },
        {
            "category": "Creative",
            "prompt": "Write a haiku about artificial intelligence."
        }
    ]
    
    results = []
    
    for item in test_prompts:
        category = item["category"]
        prompt = item["prompt"]
        messages = [{"role": "user", "content": prompt}]
        
        print(f"\n🧪 Testing Category: {category}")
        print(f"   Prompt: '{prompt}'")
        
        # 1. Live Generation (Baseline)
        print("   ⏳ Generating Live Response (Baseline)...")
        start_live = time.time()
        # HostedLLM.chat_llm is a static method that takes (system, user) or a module level function chat_llm(messages)
        # The file has both a class HostedLLM and a module level function chat_llm.
        # Let's use the module level function which accepts messages list.
        
        live_result = HostedLLM.chat_llm(messages)
        live_response = live_result.get("text", "") if isinstance(live_result, dict) else str(live_result)
        
        live_time = time.time() - start_live
        print(f"      Time: {live_time:.2f}s | Length: {len(live_response)} chars")
        
        # 2. Holographic Retrieval (Test)
        # Ensure it's in the cache first (simulate previous run)
        # For this test, we might need to manually inject or run it once to cache it.
        # But HolographicLLM usually caches on write.
        # Let's assume we want to test the *retrieval* quality vs the *live* quality.
        # If it's a cache hit, they should be identical.
        # If it's a cache miss, HolographicLLM calls Live LLM.
        
        print("   🌌 Retrieving Holographic Response...")
        start_holo = time.time()
        holo_response = holographic.chat_llm(messages) # This might trigger live if not cached
        holo_time = time.time() - start_holo
        
        is_cache_hit = holo_time < 1.0 # Simple heuristic
        source = "CACHE" if is_cache_hit else "LIVE_FILL"
        print(f"      Source: {source} | Time: {holo_time:.2f}s | Length: {len(holo_response)} chars")
        
        # 3. Comparison
        # Ensure both are strings
        live_response = str(live_response)
        holo_response = str(holo_response)
        
        similarity = SequenceMatcher(None, live_response, holo_response).ratio()
        print(f"   📊 Similarity: {similarity:.4f}")
        
        results.append({
            "category": category,
            "live_time": live_time,
            "holo_time": holo_time,
            "similarity": similarity,
            "source": source
        })
        
    print("\n📈 SUMMARY REPORT")
    print("=================")
    for res in results:
        print(f"Category: {res['category']:<10} | Speedup: {res['live_time']/res['holo_time']:.1f}x | Similarity: {res['similarity']:.2f}")

if __name__ == "__main__":
    asyncio.run(validate_quality())
