
import sys
import os
import asyncio
import time
import json

# Set Environment Variables for LLM
os.environ['AGL_LLM_PROVIDER'] = 'ollama'
os.environ['AGL_LLM_MODEL'] = 'qwen2.5:7b-instruct'
os.environ['AGL_LLM_BASEURL'] = 'http://localhost:11434'

# Add project path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'repo-copy'))

from dynamic_modules.unified_agi_system import UnifiedAGISystem
from Core_Engines import ENGINE_REGISTRY

async def test_scientific_proof():
    print("🧪 Initializing AGL System for Scientific Proof Test...")
    
    # Initialize System
    system = UnifiedAGISystem(engine_registry=ENGINE_REGISTRY)
    
    # Define the scientific proof task - using "Prove" to trigger the engine
    task = "Prove the formula for Kinetic Energy (KE = 1/2 mv^2) using Newton's Second Law."
    
    print(f"\n📝 Task: {task}")
    print("⏳ Processing... (Simulating UI Request)")
    
    start_time = time.time()
    
    # Process the task
    result = await system.process_with_full_agi(task)
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"\n✅ Result Received in {duration:.2f}s")
    print("-" * 50)
    
    response = result.get('response')
    if response:
        print(response)
    else:
        print("⚠️ No textual response generated (LLM might be offline).")
        
        # Check for scientific results directly
        sci_results = result.get('scientific_results', {})
        if sci_results:
            print("\n🔬 Scientific Results Found:")
            for key, val in sci_results.items():
                print(f"\n--- {key} ---")
                # Pretty print if it's a dict
                if isinstance(val, dict):
                    print(json.dumps(val, indent=2))
                else:
                    print(val)
        else:
            print("Debug Info:")
            print(f"Reasoning Result: {result.get('reasoning_result')}")
            print(f"Scientific Results: {result.get('scientific_results')}")
        
    print("-" * 50)
    
    # Check if scientific engines were involved
    if 'trace' in result:
        print("\n🔍 Engine Trace:")
        for step in result['trace']:
            print(f"   - {step.get('engine', 'Unknown')}: {step.get('status', 'Unknown')}")

if __name__ == "__main__":
    asyncio.run(test_scientific_proof())
