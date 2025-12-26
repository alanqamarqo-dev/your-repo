import sys
import os
import json

# Add repo-copy to path
sys.path.append(os.path.join(os.getcwd(), 'repo-copy'))

from Core_Engines.Heikal_Holographic_Memory import HeikalHolographicMemory

def extract_answers():
    print("🔦 Decoding Holographic Memory...")
    memory = HeikalHolographicMemory(key_seed=2025)
    vacuum_db = memory.load_memory()
    
    if not vacuum_db:
        print("❌ No holographic memory found.")
        return

    output_file = "FULL_ANSWERS.md"
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("# 🧠 Heikal Unified Theory: Full Decoded Answers\n")
        f.write("**Source:** `core_state.hologram.npy` (Interference Patterns)\n\n")
        
        for task, answer in vacuum_db.items():
            f.write(f"## ❓ Task: {task}\n")
            f.write(f"**Answer:**\n\n{answer}\n\n")
            f.write("---\n")
            
    print(f"✅ Answers extracted to {output_file}")

if __name__ == "__main__":
    extract_answers()
