
import sys
import os
import time

# Setup paths
root_dir = os.path.dirname(os.path.abspath(__file__))
repo_copy_dir = os.path.join(root_dir, 'repo-copy')
sys.path.append(root_dir)
sys.path.append(repo_copy_dir)

# Mock environment for LLM
os.environ['AGL_LLM_PROVIDER'] = 'ollama'
os.environ['AGL_LLM_MODEL'] = 'qwen2.5:7b-instruct'
os.environ['AGL_OLLAMA_KB_MOCK'] = '1' # Use mock to avoid actual LLM calls for speed

from Core_Engines.Creative_Innovation import CreativeInnovation
from Safety_Systems.Dissonance_Watchdog import DissonanceWatchdog

def test_creative_entanglement():
    print("\n🧪 Testing Quantum Entanglement in Creative Innovation...")
    engine = CreativeInnovation()
    
    # Test case: Entangle "Biology" and "Computer Science"
    task = {
        "query": "Create a new field of study.",
        "concepts": ["Biology", "Computer Science"]
    }
    
    result = engine.process_task(task)
    
    print(f"   Output: {result.get('output')}")
    print(f"   Quantum Metadata: {result.get('quantum_metadata')}")
    
    if 'quantum_metadata' in result and result['quantum_metadata'].get('state'):
        print("   ✅ Entanglement Successful!")
    else:
        print("   ❌ Entanglement Failed.")

def test_dissonance_watchdog():
    print("\n🧪 Testing Cognitive Dissonance Watchdog...")
    watchdog = DissonanceWatchdog()
    
    # Case 1: High Coherence (Agreement)
    state_stable = {
        "logic_confidence": 0.9,
        "intuition_confidence": 0.85,
        "ethics_confidence": 0.9
    }
    res_stable = watchdog.monitor(state_stable)
    print(f"   Stable State Dissonance: {res_stable['dissonance']:.2f} (Status: {res_stable['status']})")
    
    # Case 2: High Dissonance (Conflict)
    state_conflict = {
        "logic_confidence": 0.9,   # High confidence
        "intuition_confidence": 0.1, # Low confidence (Conflict!)
        "ethics_confidence": 0.5
    }
    res_conflict = watchdog.monitor(state_conflict)
    print(f"   Conflict State Dissonance: {res_conflict['dissonance']:.2f} (Status: {res_conflict['status']})")
    
    if res_stable['status'] == 'stable' and res_conflict['status'] == 'alert':
        print("   ✅ Watchdog Logic Verified!")
    else:
        print("   ❌ Watchdog Logic Failed.")

if __name__ == "__main__":
    print("🚀 Starting Quantum Tools Verification...")
    test_creative_entanglement()
    test_dissonance_watchdog()
