
import sys
import os
import time

# Setup paths
root_dir = os.path.dirname(os.path.abspath(__file__))
repo_copy_dir = os.path.join(root_dir, 'repo-copy')
sys.path.append(root_dir)
sys.path.append(repo_copy_dir)

# Mock environment
os.environ['AGL_LLM_PROVIDER'] = 'ollama'
os.environ['AGL_LLM_MODEL'] = 'qwen2.5:7b-instruct'
os.environ['AGL_OLLAMA_KB_MOCK'] = '1'

from Core_Engines.Dreaming_Cycle import DreamingEngine

def test_quantum_dreaming():
    print("\n🌌 Testing Quantum Dreaming Cycle...")
    engine = DreamingEngine()
    
    # Simulate a batch of memories
    memories = [
        {"id": 1, "content": "Ate lunch", "importance": 0.1, "alignment": 0.1}, # Noise
        {"id": 2, "content": "Discovered new physics law", "importance": 0.9, "alignment": 0.95}, # Signal
        {"id": 3, "content": "Saw a cat", "importance": 0.2, "alignment": 0.2}, # Noise
        {"id": 4, "content": "Solved complex bug", "importance": 0.8, "alignment": 0.9}, # Signal
        {"id": 5, "content": "Random thought", "importance": 0.3, "alignment": 0.4} # Borderline
    ]
    
    print(f"   Input Memories: {len(memories)}")
    
    # Run Quantum Consolidation
    consolidated = engine._quantum_consolidation(memories)
    
    print(f"   Consolidated Memories: {len(consolidated)}")
    
    # Verify results
    ids = [m['id'] for m in consolidated]
    if 2 in ids and 4 in ids and 1 not in ids:
        print("   ✅ Quantum Filter Successful! (Kept signals, removed noise)")
    else:
        print(f"   ❌ Quantum Filter Failed. Kept IDs: {ids}")

if __name__ == "__main__":
    test_quantum_dreaming()
