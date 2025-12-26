import sys
import os
import time

# Setup paths
root_dir = os.path.dirname(os.path.abspath(__file__))
repo_copy_dir = os.path.join(root_dir, 'repo-copy')
sys.path.append(root_dir)
sys.path.append(repo_copy_dir)
sys.path.append(os.path.join(repo_copy_dir, 'dynamic_modules'))

# Force environment
os.environ['AGL_LLM_MODEL'] = 'qwen2.5:7b-instruct'
os.environ['AGL_LLM_PROVIDER'] = 'ollama'

print("🚀 Initializing Full AGL System (Trace Mode)...")

try:
    from mission_control_enhanced import EnhancedMissionController
except ImportError:
    print("❌ Failed to import Mission Control. Check paths.")
    sys.exit(1)

import asyncio

def run_trace_test():
    print("\n[1] 🧠 Loading Unified Brain...")
    controller = EnhancedMissionController()
    
    print("\n[2] 🧪 Sending Complex Request: 'Explain the relationship between Quantum Entanglement and Information Theory'...")
    print("    (This requires multiple engines: Quantum_Processor, NLP_Advanced, Reasoning_Layer)")
    
    start_time = time.time()
    
    # We use the async method via asyncio.run
    async def run_async():
        return await controller.process_with_scientific_validation(
            "Explain the relationship between Quantum Entanglement and Information Theory in one paragraph.",
            context={"use_unified": True}
        )
    
    result = asyncio.run(run_async())
    
    # Extract response text
    if isinstance(result, dict):
        response = result.get('response', '') or result.get('final_response', '') or str(result)
    else:
        response = str(result)
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"\n[3] ✅ Response Received in {duration:.2f}s:")
    print("-" * 50)
    print(response)
    print("-" * 50)
    
    print("\n[4] 🕵️ Verification Evidence:")
    print(f"    - Time taken: {duration:.2f}s (Real AI takes time, scripts are instant)")
    print(f"    - Response length: {len(response)} chars")
    print("    - Check your Task Manager: Did 'Ollama' or 'Python' spike in CPU?")

if __name__ == "__main__":
    run_trace_test()
