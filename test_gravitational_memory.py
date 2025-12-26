import sys
import os
import time
import json

# Add repo-copy to path
sys.path.append(os.path.join(os.getcwd(), 'repo-copy'))

from Learning_System.ExperienceMemory import ExperienceMemory

def test_gravitational_memory():
    print("=== Testing Heikal Gravitational Memory ===")
    
    # Setup temporary memory file
    test_db_path = "test_memory_heikal.jsonl"
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
        
    memory = ExperienceMemory(test_db_path)
    
    current_time = time.time()
    
    # Create synthetic memories
    # 1. Recent but trivial (Low Mass, Small Distance)
    mem_recent_trivial = {
        "id": "recent_trivial",
        "content": "I just ate a sandwich.",
        "importance": 1.0,
        "intensity": 1.0,
        "timestamp": current_time - 10 # 10 seconds ago
    }
    
    # 2. Old but CRITICAL (High Mass, Large Distance)
    mem_old_critical = {
        "id": "old_critical",
        "content": "I discovered the Heikal InfoQuantum Lattice Theory.",
        "importance": 100.0, # Massive importance
        "intensity": 50.0,
        "timestamp": current_time - 10000 # 10,000 seconds ago (~3 hours)
    }
    
    # 3. Medium age, medium importance
    mem_medium = {
        "id": "medium",
        "content": "I ran a diagnostic scan.",
        "importance": 5.0,
        "intensity": 2.0,
        "timestamp": current_time - 500
    }
    
    print("Injecting memories...")
    memory.append(mem_recent_trivial)
    memory.append(mem_old_critical)
    memory.append(mem_medium)
    
    print("\nRetrieving top 2 memories using Gravitational Pull...")
    results = memory.retrieve_gravitational(top_k=2)
    
    print("\n--- Results ---")
    for i, mem in enumerate(results):
        print(f"{i+1}. ID: {mem['id']} | Content: {mem['content']}")
        
    # Verification
    top_id = results[0]['id']
    if top_id == "old_critical":
        print("\nSUCCESS: The 'Old Critical' memory was retrieved first!")
        print("Gravity (Importance) overcame Distance (Time).")
        print("The Heikal Gravitational Memory theory is working.")
    else:
        print(f"\nFAILURE: Expected 'old_critical', got '{top_id}'.")
        print("Time decay might be too strong compared to importance mass.")

    # Cleanup
    if os.path.exists(test_db_path):
        os.remove(test_db_path)

if __name__ == "__main__":
    test_gravitational_memory()
