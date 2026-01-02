import sys
import os
import time
import json

# --- Path Setup ---
root_dir = os.path.dirname(os.path.abspath(__file__))
repo_copy_dir = os.path.join(root_dir, 'repo-copy')
if repo_copy_dir not in sys.path:
    sys.path.insert(0, repo_copy_dir)

from Core_Engines.Holographic_LLM import HolographicLLM

def main():
    print("🚀 Initializing Holographic LLM Test...")
    
    # Initialize Engine
    holo_llm = HolographicLLM(key_seed=999)
    
    # Define a complex query
    messages = [
        {"role": "system", "content": "You are a helpful AI assistant."},
        {"role": "user", "content": "What is the speed of light in vacuum?"}
    ]
    
    print("\n🧪 Test 1: First Call (API Fallback + Storage)")
    print("-" * 50)
    start_time = time.time()
    response1 = holo_llm.chat_llm(messages)
    duration1 = time.time() - start_time
    print(f"📝 Response: {response1[:100]}...")
    print(f"⏱️ Duration: {duration1:.4f}s")
    
    print("\n🧪 Test 2: Second Call (Holographic Retrieval)")
    print("-" * 50)
    start_time = time.time()
    response2 = holo_llm.chat_llm(messages)
    duration2 = time.time() - start_time
    print(f"📝 Response: {response2[:100]}...")
    print(f"⏱️ Duration: {duration2:.4f}s")
    
    # Calculate Speedup
    if duration2 > 0:
        speedup = duration1 / duration2
        print(f"\n🚀 Speedup Factor: {speedup:.2f}x")
    
    print("\n📊 Statistics:")
    print(json.dumps(holo_llm.get_statistics(), indent=2))

if __name__ == "__main__":
    main()
